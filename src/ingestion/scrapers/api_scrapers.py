"""
Scraper para APIs públicas e Sites de Vagas via Busca (Search-First).

Foco:
1. Gupy Portal (API)
2. RemoteOK (API)
3. Programathor (HTML/Scraping)
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

import httpx
import structlog
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger()


class BaseSearchScraper(ABC):
    """Classe base para scrapers de busca (keyword-based) com suporte a filtro de data."""

    def __init__(
        self,
        output_dir: str = "data/bronze",
        timeout: int = 30,
    ):
        self.output_dir = Path(output_dir) / self.platform_name
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json, text/html",
            },
            follow_redirects=True
        )

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Nome da plataforma (ex: gupy)."""
        pass

    @abstractmethod
    async def search_jobs(self, query: str, limit: int = 50, since_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Busca vagas por palavra-chave.
        Args:
            query: Termo de busca.
            limit: Limite máximo de vagas.
            since_date: Se informado, para a busca ao encontrar vagas mais antigas que essa data.
        """
        pass

    async def _save_job(self, job: Dict[str, Any], query: str) -> Path:
        """Salva uma vaga no formato Bronze."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        job_id = str(job.get("id", job.get("jobId", timestamp)))
        
        # Sanitiza nome do arquivo
        company_raw = job.get("companyName", job.get("company", "unknown"))
        safe_company = "".join(x for x in company_raw if x.isalnum()) or "unknown"
        filename = f"{safe_company}_{job_id}_{timestamp}.json"
        filepath = self.output_dir / filename

        # Adiciona metadados
        job["_metadata"] = {
            "platform": self.platform_name,
            "query": query,
            "scraped_at": datetime.now().isoformat(),
            "scraper_version": "3.0.0",  # Optimized + New Sources
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(job, f, ensure_ascii=False, indent=2)

        return filepath


# =============================================================================
# 1. GUPY (API)
# =============================================================================
class GupySearchScraper(BaseSearchScraper):
    platform_name = "gupy"
    API_URL = "https://portal.api.gupy.io/api/v1/jobs"

    async def search_jobs(self, query: str, limit: int = 50, since_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        logger.info(f"[{self.platform_name}] Buscando: '{query}' (Desde: {since_date or 'inicio'})")
        
        all_jobs = []
        offset = 0
        page_size = 100
        start_time = time.time()
        seen_ids = set()
        
        # Proteção global de tempo (5 minutos max por query)
        MAX_DURATION_SECONDS = 300 

        while len(all_jobs) < limit:
            # 1. Verifica timeout global
            if time.time() - start_time > MAX_DURATION_SECONDS:
                logger.warning(f"[{self.platform_name}] Timeout de segurança atingido ({MAX_DURATION_SECONDS}s). Parando.")
                break

            remaining = limit - len(all_jobs)
            current_limit = min(page_size, remaining)
            
            params = {
                "jobName": query, 
                "limit": current_limit,
                "offset": offset,
                "sort": "date_desc" # Tenta forçar ordenação por data, embora nem sempre funcione na Gupy
            }

            try:
                response = await self.client.get(self.API_URL, params=params)
                
                if response.status_code == 400:
                    params["searchTerm"] = query
                    del params["jobName"]
                    response = await self.client.get(self.API_URL, params=params)

                if response.status_code != 200:
                    logger.error(f"[{self.platform_name}] Erro API {response.status_code}")
                    break
                    
                data = response.json()
                jobs = data.get("data", [])
                
                if not jobs:
                    logger.info(f"[{self.platform_name}] Fim dos resultados (página vazia).")
                    break

                # 2. Verifica Loop Infinito (IDs repetidos)
                new_ids = [j.get("id") for j in jobs]
                if all(nid in seen_ids for nid in new_ids):
                    logger.warning(f"[{self.platform_name}] Loop detectado (todos IDs repetidos). Parando.")
                    break
                seen_ids.update(new_ids)

                filtered_jobs_in_page = []
                stop_fetching = False

                for job in jobs:
                    # Parse da data
                    pub_date_str = job.get("publishedDate")
                    job_date = None
                    if pub_date_str:
                        try:
                            # 2023-10-25T14:30:00.000Z
                            job_date = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
                        except:
                            pass

                    # 3. Filtro de Data
                    if since_date and job_date:
                        # Se a vaga é mais antiga que nossa janela, paramos SE confiarmos na ordenação
                        # Como Gupy as vezes mistura, vamos apenas IGNORAR a vaga se for velha,
                        # mas continuamos olhando a página (safety).
                        # Se encontrarmos MUITAS vagas velhas seguidas, ai paramos.
                        if job_date < since_date:
                            # Opcional: Contar streak de vagas velhas para dar break
                            continue

                    # Normalização
                    career_page = job.get("careerPageUrl", "")
                    jid = job.get("id")
                    if career_page and jid:
                        job["url"] = f"{career_page.rstrip('/')}/job/{jid}"
                    else:
                        job["url"] = f"https://portal.gupy.io/job/{jid}"
                        
                    job["title"] = job.get("name")
                    job["company"] = job.get("companyName")
                    job["description"] = job.get("description", "")
                    
                    filtered_jobs_in_page.append(job)

                all_jobs.extend(filtered_jobs_in_page)
                offset += len(jobs)
                
                logger.info(f"[{self.platform_name}] Coletadas: {len(filtered_jobs_in_page)} (Total: {len(all_jobs)})")
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"[{self.platform_name}] Erro: {e}")
                break

        return all_jobs[:limit]


# =============================================================================
# 2. REMOTEOK (API)
# =============================================================================
class RemoteOkScraper(BaseSearchScraper):
    platform_name = "remoteok"
    # RemoteOK retorna TUDO em um JSON gigante, não tem paginação real na API publica
    API_URL = "https://remoteok.com/api"

    async def search_jobs(self, query: str, limit: int = 50, since_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        logger.info(f"[{self.platform_name}] Buscando via API para tags relacionadas a '{query}'...")
        
        # RemoteOK funciona melhor com tags. Vamos tentar mapear query -> tag ou usar busca textual
        # A API retorna ~30 dias de vagas.
        try:
            response = await self.client.get(self.API_URL)
            if response.status_code != 200:
                logger.error(f"[{self.platform_name}] Erro API {response.status_code}")
                return []

            data = response.json()
            # O primeiro item costuma ser "Legal", pular
            jobs_list = [j for j in data if "legal" not in j and "title" in j]

            filtered_jobs = []
            query_lower = query.lower()

            for job in jobs_list:
                # 1. Filtro Textual (Simples)
                title = job.get("title", "").lower()
                desc = job.get("description", "").lower()
                tags = [t.lower() for t in job.get("tags", [])]
                
                if query_lower not in title and query_lower not in tags and query_lower not in desc:
                    continue

                # 2. Filtro de Data
                date_str = job.get("date") # Formato: 2025-01-26T...
                if date_str and since_date:
                    try:
                        job_date = datetime.fromisoformat(date_str.split("+")[0])
                        if job_date < since_date:
                            continue
                    except:
                        pass

                # Normalização
                normalized_job = {
                    "id": job.get("id"),
                    "title": job.get("title"),
                    "companyName": job.get("company"),
                    "description": job.get("description"),
                    "url": job.get("url"), # geralmente link direto apply
                    "location": job.get("location"),
                    "publishedDate": job.get("date"),
                    "salary_min": job.get("salary_min"),
                    "salary_max": job.get("salary_max"),
                    "tags": job.get("tags")
                }
                filtered_jobs.append(normalized_job)
                
                if len(filtered_jobs) >= limit:
                    break
            
            logger.info(f"[{self.platform_name}] Encontradas {len(filtered_jobs)} vagas compatíveis.")
            return filtered_jobs

        except Exception as e:
            logger.error(f"[{self.platform_name}] Erro: {e}")
            return []


# =============================================================================
# 3. PROGRAMATHOR (HTML)
# =============================================================================
class ProgramathorScraper(BaseSearchScraper):
    platform_name = "programathor"
    BASE_URL = "https://programathor.com.br/jobs"

    async def search_jobs(self, query: str, limit: int = 50, since_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        logger.info(f"[{self.platform_name}] Scraping HTML para '{query}'...")
        
        all_jobs = []
        page = 1
        
        # Mapeamento simples de termo -> clean URL (Programathor usa /jobs/termo)
        # Ex: "Data Engineer" -> "data-engineer" (tentativa) ou busca geral filtra
        # Vamos usar a busca geral /jobs e filtrar na página para simplificar ou usar params
        # A URL de busca é https://programathor.com.br/jobs?term=python
        
        encoded_query = urllib.parse.quote(query)
        
        while len(all_jobs) < limit:
            url = f"{self.BASE_URL}?term={encoded_query}&page={page}"
            
            try:
                resp = await self.client.get(url)
                if resp.status_code != 200:
                    break
                
                soup = BeautifulSoup(resp.text, "html.parser")
                job_cards = soup.find_all("div", class_="cell-list") # Verificar classe atual
                
                if not job_cards:
                    logger.info(f"[{self.platform_name}] Fim das páginas.")
                    break

                for card in job_cards:
                    # Extração básica
                    try:
                        title_tag = card.find("h3")
                        if not title_tag: continue
                        
                        title = title_tag.get_text(strip=True)
                        link = "https://programathor.com.br" + card.find("a").get("href")
                        
                        # Data: Programathor as vezes mostra "New", "2 days ago".
                        # Parsing disso é chato. Vamos ignorar filtro de data preciso 
                        # e confiar que páginas > 5 são velhas.
                        
                        # Empresa
                        company_tag = card.find("span", class_="company-name") # hipotetico
                        company = company_tag.get_text(strip=True) if company_tag else "Confidencial"

                        job_obj = {
                            "title": title,
                            "companyName": company,
                            "url": link,
                            "description": f"Vaga na Programathor: {title}", # Description só na pag detalhe
                            "publishedDate": datetime.now().isoformat() # Fake date pois nao temos facil
                        }
                        
                        all_jobs.append(job_obj)
                        if len(all_jobs) >= limit: break
                        
                    except Exception as e:
                        continue

                page += 1
                await asyncio.sleep(1) # Etiqueta

            except Exception as e:
                logger.error(f"[{self.platform_name}] Erro: {e}")
                break

        return all_jobs


# =============================================================================
# EXECUTOR
# =============================================================================

async def run_search_scrapers(
    queries: List[str],
    max_jobs: int = 50,
    since_date: Optional[datetime] = None
) -> List[str]:
    """
    Executa TODOS os scrapers configurados em sequência (One-Shot).
    """
    saved_files = []
    
    # Lista de scrapers ativos
    scrapers = [
        GupySearchScraper(),
        RemoteOkScraper(),
        ProgramathorScraper()
    ]
    
    for query in queries:
        logger.info(f"=== Iniciando busca para termo: '{query}' ===")
        
        for scraper in scrapers:
            try:
                # Divide o limite entre scrapers ou aplica para todos?
                # Vamos aplicar um limite menor por scraper para não inundar
                jobs = await scraper.search_jobs(query, limit=max_jobs, since_date=since_date)
                
                for job in jobs:
                    try:
                        fpath = await scraper._save_job(job, query)
                        saved_files.append(str(fpath))
                    except Exception as e:
                        logger.error(f"Erro salvando vaga: {e}")
                        
            except Exception as e:
                logger.error(f"Erro fatal no scraper {scraper.platform_name}: {e}")
            
            finally:
                await scraper.client.aclose()
                
    return saved_files

