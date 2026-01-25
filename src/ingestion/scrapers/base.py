"""
Classe base para scrapers de vagas de emprego.

Define interface comum e funcionalidades compartilhadas:
- Persistência na camada Bronze
- Rate limiting e delays humanizados
- Retry com backoff exponencial
"""

import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

import structlog
from playwright.async_api import Page
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.ingestion.browser import BrowserManager, humanize_delay, humanize_scroll

logger = structlog.get_logger()


class ScrapingError(Exception):
    """Erro durante scraping."""

    pass


class RateLimitError(ScrapingError):
    """Rate limit atingido."""

    pass


class BlockedError(ScrapingError):
    """IP bloqueado ou CAPTCHA."""

    pass


class BaseScraper(ABC):
    """
    Classe base abstrata para scrapers de plataformas de emprego.

    Subclasses devem implementar:
    - platform_name: Nome da plataforma
    - search_url: URL de busca
    - scrape_listings: Extrai listagem de vagas
    - scrape_job_detail: Extrai detalhes de uma vaga
    """

    platform_name: str = "base"
    search_url: str = ""

    def __init__(
        self,
        browser_manager: BrowserManager,
        data_dir: Path = Path("data/bronze"),
        delay_min: float = 2.0,
        delay_max: float = 5.0,
        max_retries: int = 3,
    ):
        """
        Args:
            browser_manager: Instância do gerenciador de navegador
            data_dir: Diretório para salvar dados brutos (Bronze)
            delay_min: Delay mínimo entre requisições (segundos)
            delay_max: Delay máximo entre requisições (segundos)
            max_retries: Número máximo de tentativas em caso de erro
        """
        self.browser = browser_manager
        self.data_dir = Path(data_dir) / self.platform_name
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.max_retries = max_retries

        self._jobs_scraped = 0
        self._session_start = datetime.now()

        logger.info(
            "Scraper inicializado",
            platform=self.platform_name,
            data_dir=str(self.data_dir),
        )

    @abstractmethod
    async def scrape_listings(
        self,
        query: str,
        location: str | None = None,
        max_pages: int = 5,
    ) -> list[dict]:
        """
        Extrai listagem de vagas a partir de uma busca.

        Args:
            query: Termo de busca (ex: "Data Engineer")
            location: Filtro de localização (ex: "São Paulo")
            max_pages: Número máximo de páginas a processar

        Returns:
            Lista de dicts com {url, title, company, ...} para cada vaga
        """
        pass

    @abstractmethod
    async def scrape_job_detail(self, url: str) -> dict:
        """
        Extrai detalhes completos de uma vaga específica.

        Args:
            url: URL da página de detalhes da vaga

        Returns:
            Dict com HTML bruto e metadados
        """
        pass

    async def run(
        self,
        query: str,
        location: str | None = None,
        max_jobs: int = 100,
    ) -> list[str]:
        """
        Executa o pipeline completo de scraping.

        1. Busca listagens
        2. Para cada vaga, extrai detalhes
        3. Salva na camada Bronze

        Args:
            query: Termo de busca
            location: Filtro de localização
            max_jobs: Número máximo de vagas a coletar

        Returns:
            Lista de caminhos dos arquivos salvos
        """
        logger.info(
            "Iniciando scraping",
            platform=self.platform_name,
            query=query,
            location=location,
            max_jobs=max_jobs,
        )

        saved_files = []

        try:
            # 1. Extrai listagens
            listings = await self.scrape_listings(query, location)
            listings = listings[:max_jobs]

            logger.info(f"Encontradas {len(listings)} vagas na listagem")

            # 2. Para cada vaga, extrai detalhes e salva
            for i, listing in enumerate(listings, 1):
                try:
                    logger.info(
                        f"Processando vaga {i}/{len(listings)}",
                        url=listing.get("url", "")[:50],
                    )

                    # Delay humanizado entre requisições
                    await humanize_delay(self.delay_min, self.delay_max)

                    # Extrai detalhes
                    job_detail = await self.scrape_job_detail(listing["url"])

                    # Enriquece com metadados da listagem
                    job_detail["listing_data"] = listing

                    # Salva na Bronze
                    file_path = self._save_to_bronze(job_detail)
                    saved_files.append(file_path)

                    self._jobs_scraped += 1

                except ScrapingError as e:
                    logger.warning(f"Erro ao processar vaga: {e}", url=listing.get("url"))
                    continue

        except Exception as e:
            logger.error(f"Erro durante scraping: {e}")
            raise

        logger.info(
            "Scraping finalizado",
            total_saved=len(saved_files),
            duration=str(datetime.now() - self._session_start),
        )

        return saved_files

    def _save_to_bronze(self, data: dict) -> str:
        """
        Salva dados brutos na camada Bronze como JSON Lines.

        Args:
            data: Dict com HTML e metadados

        Returns:
            Caminho do arquivo salvo
        """
        # Gera nome único baseado em timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{timestamp}.json"
        file_path = self.data_dir / filename

        # Adiciona metadados de coleta
        data["_metadata"] = {
            "platform": self.platform_name,
            "collected_at": datetime.now().isoformat(),
            "scraper_version": "0.1.0",
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.debug(f"Salvo: {file_path}")
        return str(file_path)

    async def _navigate_with_retry(self, page: Page, url: str) -> None:
        """
        Navega para URL com retry e detecção de bloqueio.
        """

        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=4, max=60),
            retry=retry_if_exception_type(ScrapingError),
        )
        async def _navigate():
            response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            if response is None:
                raise ScrapingError(f"Sem resposta para {url}")

            status = response.status

            if status == 429:
                raise RateLimitError("Rate limit atingido")
            elif status == 403:
                raise BlockedError("Acesso bloqueado (403)")
            elif status >= 400:
                raise ScrapingError(f"Erro HTTP {status}")

            # Verifica se caiu em página de CAPTCHA
            page_content = await page.content()
            if self._detect_captcha(page_content):
                raise BlockedError("CAPTCHA detectado")

        await _navigate()

    def _detect_captcha(self, html: str) -> bool:
        """Detecta se a página contém CAPTCHA."""
        captcha_indicators = [
            "captcha",
            "recaptcha",
            "hcaptcha",
            "cf-challenge",  # Cloudflare
            "px-captcha",  # PerimeterX
            "Please verify you are a human",
        ]
        html_lower = html.lower()
        return any(indicator in html_lower for indicator in captcha_indicators)

    async def _extract_html(self, page: Page) -> str:
        """Extrai HTML limpo da página."""
        # Aguarda carregamento dinâmico
        await page.wait_for_load_state("networkidle", timeout=10000)

        # Scroll para carregar conteúdo lazy-loaded
        await humanize_scroll(page, scroll_count=2)

        return await page.content()
