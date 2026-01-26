"""
Scraper para Workday usando interceptação de requests.

Workday usa um protocolo proprietário (WDX) que requer:
1. Navegação inicial para obter token de sessão
2. Interceptação de chamadas à API interna
3. Parsing de resposta em formato específico

Empresas suportadas: Bradesco, Santander, Natura, Avanade
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path

import structlog
from playwright.async_api import Response

from src.config.companies import ATSType, Company, get_companies_by_ats
from src.ingestion.browser import BrowserManager

logger = structlog.get_logger()


# =============================================================================
# MAPEAMENTO DE URLS WORKDAY POR EMPRESA
# =============================================================================
WORKDAY_URLS = {
    "bradesco": "https://bradesco.wd5.myworkdayjobs.com/External",
    "santander": "https://santander.wd3.myworkdayjobs.com/SantanderBrasil",
    "naturaco": "https://natura.wd5.myworkdayjobs.com/Natura",
    "avanade": "https://avanade.wd1.myworkdayjobs.com/Careers",
}


class WorkdayScraper:
    """
    Scraper para sites Workday.

    Estratégia:
    1. Navega até página de carreiras da empresa
    2. Intercepta responses da API WDX
    3. Extrai vagas do payload JSON
    4. Salva no formato Bronze
    """

    platform_name = "workday"
    ats_type = ATSType.WORKDAY

    def __init__(
        self,
        output_dir: str = "data/bronze",
        headless: bool = True,
    ):
        self.output_dir = Path(output_dir) / self.platform_name
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.headless = headless
        self._jobs_collected: list[dict] = []
        self._current_company: Company | None = None

    async def _handle_response(self, response: Response):
        """Intercepta e processa respostas da API Workday."""
        url = response.url

        # Filtra apenas chamadas à API de vagas
        if "jobs" not in url.lower() and "jobPosting" not in url:
            return

        # Ignora recursos estáticos
        if any(ext in url for ext in [".js", ".css", ".png", ".svg", ".woff"]):
            return

        try:
            content_type = response.headers.get("content-type", "")
            if "application/json" not in content_type:
                return

            body = await response.text()
            if not body:
                return

            data = json.loads(body)

            # Extrai vagas do payload WDX
            jobs = self._extract_jobs_from_wdx(data)
            if jobs:
                logger.debug(f"Interceptadas {len(jobs)} vagas", url=url[:80])
                self._jobs_collected.extend(jobs)

        except Exception as e:
            logger.debug("Erro ao processar response", url=url[:50], error=str(e))

    def _extract_jobs_from_wdx(self, data: dict) -> list[dict]:
        """Extrai vagas do formato WDX complexo."""
        jobs = []

        # Tenta diferentes estruturas conhecidas do WDX
        # Formato 1: jobPostings array
        if "jobPostings" in data:
            for posting in data["jobPostings"]:
                job = self._parse_wdx_posting(posting)
                if job:
                    jobs.append(job)

        # Formato 2: data > body > children (paginado)
        elif "body" in data:
            body = data.get("body", {})
            children = body.get("children", [])
            for child in children:
                if child.get("widget") == "jobPosting" or "job" in str(child).lower():
                    job = self._parse_wdx_widget(child)
                    if job:
                        jobs.append(job)

        # Formato 3: listItems (mais comum)
        elif "listItems" in data:
            for item in data["listItems"]:
                job = self._parse_wdx_list_item(item)
                if job:
                    jobs.append(job)

        # Formato 4: facetContainer > paginatedSearchResult
        if "facetContainer" in data:
            facet = data["facetContainer"]
            if "paginatedSearchResult" in facet:
                result = facet["paginatedSearchResult"]
                list_items = result.get("listItems", [])
                for item in list_items:
                    job = self._parse_wdx_list_item(item)
                    if job:
                        jobs.append(job)

        # Formato 5: Busca recursiva por job patterns
        if not jobs:
            jobs = self._recursive_job_search(data)

        return jobs

    def _parse_wdx_posting(self, posting: dict) -> dict | None:
        """Parseia formato jobPosting."""
        return {
            "id": posting.get("bulletFields", [{}])[0].get("id")
            if posting.get("bulletFields")
            else None,
            "title": posting.get("title", ""),
            "location": posting.get("locationsText", posting.get("location", "")),
            "posted_on": posting.get("postedOn", ""),
            "job_req_id": posting.get("jobReqId", ""),
            "time_type": posting.get("timeType", ""),
            "external_url": posting.get("externalPath", ""),
        }

    def _parse_wdx_widget(self, widget: dict) -> dict | None:
        """Parseia formato widget."""
        title = widget.get("title", {}).get("text", "")
        if not title:
            return None

        return {
            "id": widget.get("id", ""),
            "title": title,
            "location": widget.get("subtitle", {}).get("text", ""),
            "external_url": widget.get("commandLink", {}).get("uri", ""),
        }

    def _parse_wdx_list_item(self, item: dict) -> dict | None:
        """Parseia formato listItem (mais comum)."""
        title_data = item.get("title", {})
        title = (
            title_data.get("instances", [{}])[0].get("text", "")
            if title_data.get("instances")
            else ""
        )

        if not title:
            # Tenta estrutura alternativa
            title = item.get("title", "") if isinstance(item.get("title"), str) else ""

        if not title:
            return None

        # Extrai localização
        subtitles = item.get("subtitles", [])
        location = ""
        for sub in subtitles:
            instances = sub.get("instances", [])
            for inst in instances:
                if "location" in str(inst).lower() or "brasil" in inst.get("text", "").lower():
                    location = inst.get("text", "")
                    break

        return {
            "id": item.get("id", ""),
            "title": title,
            "location": location or item.get("locationsText", ""),
            "subtitles": subtitles,
            "external_url": item.get("title", {}).get("commandLink", {}).get("destination", ""),
        }

    def _recursive_job_search(self, data: dict, depth: int = 0) -> list[dict]:
        """Busca recursiva por estruturas de vaga."""
        if depth > 5:
            return []

        jobs = []

        if isinstance(data, dict):
            # Procura por campos típicos de vaga
            if "title" in data and ("location" in data or "locationsText" in data):
                title = data.get("title")
                if isinstance(title, str) and len(title) > 3:
                    jobs.append(
                        {
                            "id": data.get("id", ""),
                            "title": title,
                            "location": data.get("location", data.get("locationsText", "")),
                            "external_url": data.get("externalPath", data.get("url", "")),
                        }
                    )

            # Continua buscando em filhos
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    jobs.extend(self._recursive_job_search(value, depth + 1))

        elif isinstance(data, list):
            for item in data:
                jobs.extend(self._recursive_job_search(item, depth + 1))

        return jobs

    async def fetch_jobs(self, company: Company, query: str | None = None) -> list[dict]:
        """
        Busca vagas de uma empresa no Workday.

        Args:
            company: Empresa configurada
            query: Filtro opcional por termo

        Returns:
            Lista de vagas extraídas
        """
        self._jobs_collected = []
        self._current_company = company

        base_url = WORKDAY_URLS.get(company.identifier)
        if not base_url:
            logger.warning("URL Workday não configurada", company=company.name)
            return []

        async with BrowserManager(headless=self.headless) as browser:
            page = await browser.new_page()

            # Configura interceptação de responses
            page.on("response", self._handle_response)

            try:
                # Navega para página de carreiras
                logger.info("Navegando para Workday", company=company.name, url=base_url)
                await page.goto(base_url, wait_until="networkidle", timeout=60000)

                # Aguarda carregamento inicial
                await asyncio.sleep(3)

                # Scroll para carregar mais vagas (paginação lazy)
                for i in range(3):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(2)

                # Tenta clicar em "Mostrar mais" se existir
                try:
                    show_more = page.locator(
                        'button:has-text("more"), button:has-text("mais"), '
                        '[data-automation-id="loadMoreButton"]'
                    )
                    for _ in range(5):
                        if await show_more.first.is_visible():
                            await show_more.first.click()
                            await asyncio.sleep(2)
                        else:
                            break
                except Exception:
                    pass

                # Aguarda mais responses
                await asyncio.sleep(3)

            except Exception as e:
                logger.error("Erro ao navegar Workday", company=company.name, error=str(e))

            finally:
                await page.close()

        # Deduplica vagas
        seen_ids = set()
        unique_jobs = []
        for job in self._jobs_collected:
            job_id = job.get("id") or job.get("title")
            if job_id and job_id not in seen_ids:
                seen_ids.add(job_id)
                unique_jobs.append(job)

        logger.info("Vagas coletadas do Workday", company=company.name, count=len(unique_jobs))
        return unique_jobs

    async def run(
        self,
        companies: list[Company] | None = None,
        query: str | None = None,
        max_jobs_per_company: int = 100,
    ) -> list[str]:
        """
        Executa scraping para todas as empresas Workday configuradas.

        Args:
            companies: Lista de empresas (usa config se None)
            query: Filtro opcional
            max_jobs_per_company: Limite de vagas por empresa

        Returns:
            Lista de arquivos salvos
        """
        if companies is None:
            companies = get_companies_by_ats(ATSType.WORKDAY)

        saved_files = []
        total_jobs = 0

        for company in companies:
            try:
                jobs = await self.fetch_jobs(company, query)

                if not jobs:
                    logger.warning("Nenhuma vaga encontrada", company=company.name)
                    continue

                # Limita quantidade
                jobs = jobs[:max_jobs_per_company]

                # Filtra por query se especificado
                if query:
                    query_lower = query.lower()
                    jobs = [
                        j
                        for j in jobs
                        if query_lower in j.get("title", "").lower()
                        or query_lower in j.get("location", "").lower()
                    ]

                # Salva cada vaga
                for job in jobs:
                    file_path = self._save_job(company, job)
                    saved_files.append(str(file_path))
                    total_jobs += 1

                logger.info("Vagas salvas", company=company.name, count=len(jobs))

                # Rate limiting entre empresas
                await asyncio.sleep(5)

            except Exception as e:
                logger.error("Erro no scraping Workday", company=company.name, error=str(e))

        logger.info("Scraping Workday finalizado", total_jobs=total_jobs)
        return saved_files

    def _save_job(self, company: Company, job: dict) -> Path:
        """Salva uma vaga no formato Bronze."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        job_id = job.get("id") or job.get("job_req_id") or timestamp
        # Limpa caracteres inválidos do ID
        job_id = re.sub(r"[^\w\-]", "_", str(job_id))[:50]
        filename = f"{company.identifier}_{job_id}_{timestamp}.json"
        filepath = self.output_dir / filename

        # Adiciona metadados
        job["_metadata"] = {
            "platform": self.platform_name,
            "company": company.name,
            "company_id": company.identifier,
            "scraped_at": datetime.now().isoformat(),
            "category": company.category,
            "source_url": WORKDAY_URLS.get(company.identifier, ""),
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(job, f, ensure_ascii=False, indent=2)

        return filepath


# =============================================================================
# EXECUÇÃO STANDALONE
# =============================================================================
async def main():
    """Executa scraper Workday standalone."""
    scraper = WorkdayScraper(headless=False)  # headless=False para debug

    # Testa com uma empresa
    from src.config.companies import WORKDAY_COMPANIES

    if WORKDAY_COMPANIES:
        company = WORKDAY_COMPANIES[0]
        print(f"Testando com {company.name}...")
        jobs = await scraper.fetch_jobs(company)
        print(f"Encontradas {len(jobs)} vagas")
        for job in jobs[:5]:
            print(f"  - {job.get('title', 'N/A')[:50]} | {job.get('location', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(main())
