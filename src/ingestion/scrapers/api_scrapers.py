"""
Scraper para APIs públicas/semi-públicas de ATS.

Implementa scrapers leves (sem navegador) para:
- Gupy API (portal.api.gupy.io)
- Greenhouse API (boards-api.greenhouse.io)
- Lever API (api.lever.co)
- SmartRecruiters API (api.smartrecruiters.com)

Estes scrapers são mais rápidos e confiáveis que navegador.
"""

import asyncio
import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config.companies import ATSType, Company, get_companies_by_ats

logger = structlog.get_logger()


class BaseAPIScraper(ABC):
    """Classe base para scrapers de API."""

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
        """Nome da plataforma (gupy, greenhouse, etc)."""
        pass

    @abstractmethod
    async def fetch_jobs(self, company: Company, query: str | None = None) -> list[dict]:
        """Busca vagas de uma empresa específica."""
        pass

    async def run(
        self,
        companies: list[Company] | None = None,
        query: str | None = None,
        max_jobs_per_company: int = 100,
    ) -> list[str]:
        """
        Executa o scraping para todas as empresas configuradas.

        Args:
            companies: Lista de empresas (usa config se None)
            query: Filtro opcional por termo
            max_jobs_per_company: Limite de vagas por empresa

        Returns:
            Lista de arquivos salvos
        """
        if companies is None:
            companies = get_companies_by_ats(self.ats_type)

        saved_files = []
        total_jobs = 0

        for company in companies:
            try:
                logger.info("Buscando vagas", company=company.name, platform=self.platform_name)
                jobs = await self.fetch_jobs(company, query)

                if not jobs:
                    logger.debug("Nenhuma vaga encontrada", company=company.name)
                    continue

                # Limita quantidade
                jobs = jobs[:max_jobs_per_company]

                # Filtra por query se especificado
                if query:
                    query_lower = query.lower()
                    jobs = [
                        j for j in jobs
                        if query_lower in j.get("name", "").lower()
                        or query_lower in j.get("title", "").lower()
                        or query_lower in j.get("description", "").lower()
                    ]

                # Salva cada vaga
                for job in jobs:
                    file_path = await self._save_job(company, job)
                    saved_files.append(str(file_path))
                    total_jobs += 1

                logger.info("Vagas coletadas", company=company.name, count=len(jobs))

                # Rate limiting
                await asyncio.sleep(1)

            except Exception as e:
                logger.error("Erro ao buscar vagas", company=company.name, error=str(e))

        await self.client.aclose()
        logger.info("Scraping finalizado", platform=self.platform_name, total_jobs=total_jobs)
        return saved_files

    async def _save_job(self, company: Company, job: dict) -> Path:
        """Salva uma vaga no formato Bronze."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        job_id = job.get("id", job.get("job_id", timestamp))
        filename = f"{company.identifier}_{job_id}_{timestamp}.json"
        filepath = self.output_dir / filename

        # Adiciona metadados
        job["_metadata"] = {
            "platform": self.platform_name,
            "company": company.name,
            "company_id": company.identifier,
            "scraped_at": datetime.now().isoformat(),
            "category": company.category,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(job, f, ensure_ascii=False, indent=2)

        return filepath


# =============================================================================
# GUPY API SCRAPER
# =============================================================================
class GupyAPIScraper(BaseAPIScraper):
    """
    Scraper para Gupy usando a API oculta.

    API Base: https://portal.api.gupy.io/api/v1/jobs
    Parâmetros:
        - jobName: Nome/slug da empresa (ex: "nubank", "itau")
        - limit: Quantidade de vagas (max 200)
        - offset: Paginação
    """

    platform_name = "gupy"
    ats_type = ATSType.GUPY

    # API v1 funciona para busca geral
    API_URL = "https://portal.api.gupy.io/api/v1/jobs"
    COMPANY_API_URL = "https://{company}.gupy.io/api/jobs"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
    async def fetch_jobs(
        self,
        company: Company,
        query: str | None = None,
        remote_only: bool = True,
    ) -> list[dict]:
        """Busca vagas de uma empresa na Gupy.
        
        Args:
            company: Empresa alvo
            query: Filtro de busca
            remote_only: Se True, filtra apenas vagas remotas
        """
        jobs = []

        # Tenta API do portal de carreira da empresa
        try:
            url = f"https://{company.identifier}.gupy.io/api/jobs"
            params = {}
            # Filtro de trabalho remoto (quando suportado)
            if remote_only:
                params["workplaceType"] = "remote"
            
            response = await self.client.get(url, params=params if params else None)

            if response.status_code == 200:
                data = response.json()
                # A resposta pode ter diferentes estruturas
                if isinstance(data, list):
                    jobs = data
                elif isinstance(data, dict):
                    jobs = data.get("data", data.get("jobs", []))

                # Adiciona URL de origem
                for job in jobs:
                    job["url"] = f"https://{company.identifier}.gupy.io/job/{job.get('id', '')}"

                # Filtro adicional por remoto (fallback se API não filtrou)
                if remote_only:
                    jobs = [
                        j for j in jobs
                        if self._is_remote_job(j)
                    ]

                return jobs

        except Exception as e:
            logger.debug("API da empresa falhou, tentando portal", error=str(e))

        # Fallback: API do portal de busca
        try:
            params = {
                "name": company.name,
                "limit": 100,
            }
            if query:
                params["searchTerm"] = query

            response = await self.client.get(self.API_URL, params=params)

            if response.status_code == 200:
                data = response.json()
                jobs = data.get("data", [])

                # Filtra apenas vagas da empresa específica
                jobs = [
                    j for j in jobs
                    if company.identifier.lower() in j.get("careerPageName", "").lower()
                    or company.name.lower() in j.get("companyName", "").lower()
                ]

        except Exception as e:
            logger.error("Erro na API Gupy", error=str(e))

        return jobs

    def _is_remote_job(self, job: dict) -> bool:
        """Verifica se vaga é remota baseado nos campos da Gupy."""
        # Campo workplaceType da Gupy
        workplace = job.get("workplaceType", "").lower()
        if workplace == "remote":
            return True
        if workplace in ["on-site", "hybrid"]:
            return False
        
        # Fallback: busca no título e descrição
        text = f"{job.get('name', '')} {job.get('description', '')}".lower()
        remote_keywords = ["remoto", "remote", "home office", "anywhere"]
        hybrid_keywords = ["híbrido", "hibrido", "hybrid", "presencial"]
        
        # Se tem palavra de híbrido/presencial, não é remoto
        if any(kw in text for kw in hybrid_keywords):
            return False
        
        # Se tem palavra de remoto, é remoto
        if any(kw in text for kw in remote_keywords):
            return True
        
        return False


# =============================================================================
# GREENHOUSE API SCRAPER
# =============================================================================
class GreenhouseAPIScraper(BaseAPIScraper):
    """
    Scraper para Greenhouse usando a API pública.

    API: https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true

    Esta é a "mina de ouro" mencionada no documento - API totalmente pública
    e bem documentada.
    """

    platform_name = "greenhouse"
    ats_type = ATSType.GREENHOUSE
    API_URL = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
    async def fetch_jobs(
        self,
        company: Company,
        query: str | None = None,
        remote_only: bool = True,
        brazil_only: bool = True,
    ) -> list[dict]:
        """Busca vagas de uma empresa no Greenhouse.
        
        Args:
            company: Empresa alvo
            query: Filtro de busca
            remote_only: Se True, filtra apenas vagas remotas
            brazil_only: Se True, filtra apenas vagas para Brasil
        """
        url = self.API_URL.format(token=company.identifier)
        params = {"content": "true"}  # Retorna HTML completo da descrição

        try:
            response = await self.client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                jobs = data.get("jobs", [])

                # Adiciona URL e metadados
                for job in jobs:
                    job["url"] = job.get("absolute_url", "")
                    job["html"] = job.get("content", "")  # Descrição em HTML
                    job["title"] = job.get("title", "")
                    job["company"] = company.name

                    # Extrai localização
                    if job.get("location"):
                        job["location_name"] = job["location"].get("name", "")

                # Filtro de remoto e Brasil (Greenhouse não tem filtro nativo)
                if remote_only or brazil_only:
                    jobs = [
                        j for j in jobs
                        if self._is_valid_job(j, remote_only, brazil_only)
                    ]

                return jobs

            elif response.status_code == 404:
                logger.warning("Board não encontrado", company=company.name)
                return []

        except Exception as e:
            logger.error("Erro na API Greenhouse", company=company.name, error=str(e))

        return []

    def _is_valid_job(self, job: dict, remote_only: bool, brazil_only: bool) -> bool:
        """Verifica se vaga atende critérios de remoto e Brasil."""
        location = job.get("location_name", "").lower()
        title = job.get("title", "").lower()
        content = job.get("html", "").lower()
        
        full_text = f"{title} {location} {content}"
        
        # Verifica remoto
        if remote_only:
            remote_keywords = ["remote", "remoto", "home office", "anywhere", "work from home"]
            hybrid_keywords = ["hybrid", "híbrido", "hibrido", "on-site", "presencial", "office"]
            
            # Se tem híbrido/presencial explícito, descarta
            if any(kw in location for kw in hybrid_keywords):
                return False
            
            # Se não menciona remoto em lugar nenhum, descarta
            if not any(kw in full_text for kw in remote_keywords):
                return False
        
        # Verifica Brasil
        if brazil_only:
            brazil_keywords = ["brazil", "brasil", "são paulo", "sao paulo", "rio de janeiro", 
                              "belo horizonte", "curitiba", "porto alegre", "florianópolis",
                              "brasília", "brasilia", "recife", "salvador", "fortaleza"]
            invalid_countries = ["spain", "espanha", "portugal", "usa", "united states", 
                                "uk", "germany", "france", "india", "canada", "mexico",
                                "argentina", "chile", "colombia"]
            
            # Se menciona país inválido na localização, descarta
            if any(country in location for country in invalid_countries):
                return False
            
            # Se é empresa brasileira (da nossa lista), assume Brasil
            # A menos que localização indique outro país
            # Empresas da lista já são validadas, então aceita
        
        return True


# =============================================================================
# LEVER API SCRAPER
# =============================================================================
class LeverAPIScraper(BaseAPIScraper):
    """
    Scraper para Lever usando a API pública.

    API: https://api.lever.co/v0/postings/{company}?mode=json
    """

    platform_name = "lever"
    ats_type = ATSType.LEVER
    API_URL = "https://api.lever.co/v0/postings/{company}"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
    async def fetch_jobs(self, company: Company, query: str | None = None) -> list[dict]:
        """Busca vagas de uma empresa no Lever."""
        url = self.API_URL.format(company=company.identifier)
        params = {"mode": "json"}

        try:
            response = await self.client.get(url, params=params)

            if response.status_code == 200:
                jobs = response.json()

                # Lever retorna lista diretamente
                if isinstance(jobs, list):
                    for job in jobs:
                        job["url"] = job.get("hostedUrl", "")
                        job["title"] = job.get("text", "")
                        job["company"] = company.name
                        job["html"] = job.get("descriptionPlain", "")

                        # Localização
                        if job.get("categories"):
                            job["location_name"] = job["categories"].get("location", "")
                            job["team"] = job["categories"].get("team", "")

                    return jobs

        except Exception as e:
            logger.error("Erro na API Lever", company=company.name, error=str(e))

        return []


# =============================================================================
# SMARTRECRUITERS API SCRAPER
# =============================================================================
class SmartRecruitersAPIScraper(BaseAPIScraper):
    """
    Scraper para SmartRecruiters usando a API pública.

    API: https://api.smartrecruiters.com/v1/companies/{id}/postings
    Permite filtrar por país: ?country=br
    """

    platform_name = "smartrecruiters"
    ats_type = ATSType.SMARTRECRUITERS
    API_URL = "https://api.smartrecruiters.com/v1/companies/{company}/postings"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
    async def fetch_jobs(self, company: Company, query: str | None = None) -> list[dict]:
        """Busca vagas de uma empresa no SmartRecruiters."""
        url = self.API_URL.format(company=company.identifier)
        params = {"country": "br"}  # Filtra apenas Brasil

        try:
            response = await self.client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                jobs = data.get("content", [])

                for job in jobs:
                    job["url"] = job.get("ref", {}).get("url", "") if isinstance(job.get("ref"), dict) else ""
                    job["title"] = job.get("name", "")
                    job["company"] = company.name

                    # Localização
                    if job.get("location"):
                        loc = job["location"]
                        job["location_name"] = f"{loc.get('city', '')}, {loc.get('region', '')}"

                return jobs

        except Exception as e:
            logger.error("Erro na API SmartRecruiters", company=company.name, error=str(e))

        return []


# =============================================================================
# FACTORY E AGREGADOR
# =============================================================================
def get_scraper(ats_type: ATSType) -> BaseAPIScraper | None:
    """Retorna o scraper apropriado para o tipo de ATS."""
    scrapers = {
        ATSType.GUPY: GupyAPIScraper,
        ATSType.GREENHOUSE: GreenhouseAPIScraper,
        ATSType.LEVER: LeverAPIScraper,
        ATSType.SMARTRECRUITERS: SmartRecruitersAPIScraper,
    }
    scraper_class = scrapers.get(ats_type)
    return scraper_class() if scraper_class else None


async def run_all_api_scrapers(
    query: str | None = None,
    max_jobs_per_company: int = 50,
    priority_only: bool = True,
) -> list[str]:
    """
    Executa todos os scrapers de API em paralelo.

    Args:
        query: Filtro opcional por termo
        max_jobs_per_company: Limite de vagas por empresa
        priority_only: Se True, busca apenas empresas prioridade 1

    Returns:
        Lista de todos os arquivos salvos
    """
    all_files = []
    
    # Scrapers disponíveis (exceto Workday que precisa de navegador)
    ats_types = [
        ATSType.GREENHOUSE,  # API mais confiável
        ATSType.LEVER,
        ATSType.SMARTRECRUITERS,
        ATSType.GUPY,  # Por último pois pode ter rate limiting
    ]

    for ats_type in ats_types:
        scraper = get_scraper(ats_type)
        if scraper:
            companies = get_companies_by_ats(ats_type)

            if priority_only:
                companies = [c for c in companies if c.priority == 1]

            if companies:
                try:
                    files = await scraper.run(
                        companies=companies,
                        query=query,
                        max_jobs_per_company=max_jobs_per_company,
                    )
                    all_files.extend(files)
                except Exception as e:
                    logger.error(f"Erro no scraper {ats_type.value}", error=str(e))

    return all_files


# Teste direto
if __name__ == "__main__":
    async def test():
        # Testa Greenhouse (mais confiável)
        scraper = GreenhouseAPIScraper()
        from src.config.companies import ATSType, Company

        nubank = Company("Nubank", ATSType.GREENHOUSE, "nubank", "fintech", 1, True)
        jobs = await scraper.fetch_jobs(nubank)
        print(f"Nubank: {len(jobs)} vagas encontradas")

        if jobs:
            print(f"Exemplo: {jobs[0].get('title')}")

    asyncio.run(test())
