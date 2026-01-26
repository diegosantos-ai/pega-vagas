"""
Scraper para APIs públicas de Agregadores de Vagas via Busca.

Foco principal: Gupy Portal (portal.api.gupy.io)
Esta versão remove a dependência de uma lista fixa de empresas.
"""

import asyncio
import json
import urllib.parse
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger()


class BaseSearchScraper(ABC):
    """Classe base para scrapers de busca (keyword-based)."""

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
                "Accept": "application/json",
            },
        )

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Nome da plataforma (ex: gupy)."""
        pass

    @abstractmethod
    async def search_jobs(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Busca vagas por palavra-chave."""
        pass

    async def _save_job(self, job: Dict[str, Any], query: str) -> Path:
        """Salva uma vaga no formato Bronze."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        job_id = str(job.get("id", job.get("jobId", timestamp)))
        
        # Sanitiza nome do arquivo
        safe_company = "".join(x for x in job.get("companyName", "unknown") if x.isalnum())
        filename = f"{safe_company}_{job_id}_{timestamp}.json"
        filepath = self.output_dir / filename

        # Adiciona metadados
        job["_metadata"] = {
            "platform": self.platform_name,
            "query": query,
            "scraped_at": datetime.now().isoformat(),
            "scraper_version": "2.0.0",  # Search-based
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(job, f, ensure_ascii=False, indent=2)

        return filepath


class GupySearchScraper(BaseSearchScraper):
    """
    Scraper para o Portal de Vagas da Gupy.
    API: https://portal.api.gupy.io/api/v1/jobs
    """

    platform_name = "gupy"
    API_URL = "https://portal.api.gupy.io/api/v1/jobs"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
    async def search_jobs(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Busca vagas no portal da Gupy usando termo de busca.
        """
        logger.info(f"Buscando vagas na Gupy: '{query}'")
        
        all_jobs = []
        offset = 0
        page_size = 100 # Máximo permitido pela API costuma ser 100
        
        # Busca até atingir o limite ou acabar os resultados
        while len(all_jobs) < limit:
            remaining = limit - len(all_jobs)
            current_limit = min(page_size, remaining)
            
        while len(all_jobs) < limit:
            remaining = limit - len(all_jobs)
            current_limit = min(page_size, remaining)
            
            # Tentativa 1: jobName (algumas versoes da API usam isso para busca textual)
            params = {
                "jobName": query, 
                "limit": current_limit,
                "offset": offset,
            }

            try:
                response = await self.client.get(self.API_URL, params=params)
                
                # Se der erro 400, tenta com searchTerm (pode ser alternativo)
                if response.status_code == 400:
                    logger.warning("Gupy API 400 com 'jobName', tentando 'searchTerm'...")
                    params["searchTerm"] = query
                    del params["jobName"]
                    response = await self.client.get(self.API_URL, params=params)

                if response.status_code != 200:
                    logger.error(f"Erro Gupy API: {response.status_code} - {response.text[:100]}")
                    break
                    
                data = response.json()
                jobs = data.get("data", [])
                
                if not jobs:
                    break
                    
                for job in jobs:
                    # Normaliza URL
                    career_page = job.get("careerPageUrl", "")
                    job_id = job.get("id")
                    if career_page and job_id:
                        # careerPageUrl geralmente vem como "https://nome.gupy.io/"
                        job["url"] = f"{career_page.rstrip('/')}/job/{job_id}"
                    else:
                        job["url"] = f"https://portal.gupy.io/job/{job_id}" # Fallback
                        
                    # Adiciona metadados úteis para o pipeline
                    job["title"] = job.get("name")
                    job["company"] = job.get("companyName")
                    job["description"] = job.get("description", "") # Gupy Portal as vezes não traz full description na lista
                    
                all_jobs.extend(jobs)
                offset += len(jobs)
                
                logger.info(f"Gupy: Coletadas {len(jobs)} vagas (Total: {len(all_jobs)})")
                
                await asyncio.sleep(0.5) # Rate limit suave
                
            except Exception as e:
                logger.error(f"Erro na busca Gupy: {e}")
                break

        return all_jobs[:limit]


# =============================================================================
# FACTORY E EXECUTOR
# =============================================================================

async def run_search_scrapers(
    queries: List[str],
    max_jobs: int = 50,
) -> List[str]:
    """
    Executa scrapers de busca para uma lista de termos.
    
    Args:
        queries: Lista de termos de busca (ex: ["Data Engineer", "Python"])
        max_jobs: Máximo de vagas por termo
        
    Returns:
        Lista de arquivos salvos
    """
    saved_files = []
    
    # Por enquanto, apenas Gupy suporta busca global confiável via API
    scraper = GupySearchScraper()
    
    for query in queries:
        try:
            logger.info(f"Iniciando busca para: {query}")
            jobs = await scraper.search_jobs(query, limit=max_jobs)
            
            for job in jobs:
                try:
                    filepath = await scraper._save_job(job, query)
                    saved_files.append(str(filepath))
                except Exception as e:
                    logger.error(f"Erro ao salvar vaga: {e}")
                    
        except Exception as e:
            logger.error(f"Erro no scraper para query '{query}': {e}")
            
    await scraper.client.aclose()
    return saved_files
