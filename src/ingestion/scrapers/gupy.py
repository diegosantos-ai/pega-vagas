"""
Scraper específico para a plataforma Gupy (portal.gupy.io).

A Gupy é uma das maiores plataformas de vagas do Brasil, usada por empresas
como Ambev, Natura, Nubank, iFood, entre outras.

Estrutura:
- Busca: https://portal.gupy.io/job-search/term={query}
- Detalhes: https://{empresa}.gupy.io/job/{job_id}?jobBoardSource=gupy_portal
"""

import asyncio
import re
from datetime import datetime
from urllib.parse import quote

import structlog

from src.ingestion.browser import humanize_delay, humanize_scroll
from src.ingestion.scrapers.base import BaseScraper

logger = structlog.get_logger()


class GupyScraper(BaseScraper):
    """
    Scraper para vagas da plataforma Gupy.

    Exemplo de uso:
        async with BrowserManager() as browser:
            scraper = GupyScraper(browser)
            files = await scraper.run(query="Data Engineer", max_jobs=50)
    """

    platform_name = "gupy"
    search_url = "https://portal.gupy.io/job-search/term={query}"

    # Seletores CSS (usando aria-labels para maior estabilidade)
    SELECTORS = {
        # Página de listagem
        "job_cards": 'a[href*="/job/"]',
        "job_title": "h3",
        "company_name": 'p[aria-label*="empresa"], [aria-label*="company"]',
        "location": '[aria-label*="Local de trabalho"], [aria-label*="location"]',
        "work_model": '[aria-label*="Modelo de trabalho"], [aria-label*="work model"]',
        "contract_type": '[aria-label*="Tipo de contratação"], [aria-label*="contract"]',
        "published_date": 'p:has-text("Publicada em")',
        # Página de detalhes
        "detail_title": "h1",
        "detail_sections": "h2",
        "detail_description": "main",
        # Paginação / Load more
        "load_more": 'button:has-text("Carregar mais"), button:has-text("Ver mais")',
        "no_results": ':has-text("Nenhuma vaga encontrada")',
    }

    async def scrape_listings(
        self,
        query: str,
        location: str | None = None,
        max_pages: int = 5,
    ) -> list[dict]:
        """
        Extrai listagem de vagas a partir de uma busca na Gupy.

        Args:
            query: Termo de busca (ex: "Data Engineer")
            location: Não implementado ainda (Gupy usa filtro diferente)
            max_pages: Número de vezes para clicar em "Carregar mais"

        Returns:
            Lista de dicts com dados básicos de cada vaga
        """
        listings = []
        search_url = self.search_url.format(query=quote(query))

        logger.info("Iniciando busca na Gupy", query=query, url=search_url)

        async with self.browser.get_page() as page:
            # Navega para a página de busca
            await self._navigate_with_retry(page, search_url)
            await humanize_delay(1.5, 2.5)

            # Verifica se há resultados
            no_results = await page.query_selector(self.SELECTORS["no_results"])
            if no_results:
                logger.warning("Nenhuma vaga encontrada para a busca", query=query)
                return []

            # Carrega mais resultados (scroll infinito ou botão)
            for page_num in range(max_pages):
                logger.debug(f"Carregando página {page_num + 1}/{max_pages}")

                # Scroll para carregar conteúdo lazy-loaded
                await humanize_scroll(page, scroll_count=3)
                await humanize_delay(1.0, 2.0)

                # Tenta clicar em "Carregar mais" se existir
                load_more = await page.query_selector(self.SELECTORS["load_more"])
                if load_more:
                    try:
                        await load_more.click()
                        await humanize_delay(1.5, 2.5)
                    except Exception:
                        break  # Botão desapareceu ou não clicável
                else:
                    # Sem mais resultados para carregar
                    break

            # Extrai todos os cards de vagas
            job_cards = await page.query_selector_all(self.SELECTORS["job_cards"])
            logger.info(f"Encontrados {len(job_cards)} cards de vagas")

            for card in job_cards:
                try:
                    listing = await self._extract_listing_card(card)
                    if listing and listing.get("url"):
                        listings.append(listing)
                except Exception as e:
                    logger.debug(f"Erro ao extrair card: {e}")
                    continue

        logger.info(f"Extraídas {len(listings)} vagas da listagem")
        return listings

    async def _extract_listing_card(self, card) -> dict | None:
        """Extrai dados de um card de vaga na listagem."""
        try:
            # URL da vaga
            href = await card.get_attribute("href")
            if not href:
                return None

            # Título
            title_el = await card.query_selector(self.SELECTORS["job_title"])
            title = await title_el.inner_text() if title_el else ""

            # Empresa (do aria-label ou texto)
            company = ""
            company_el = await card.query_selector(self.SELECTORS["company_name"])
            if company_el:
                company = await company_el.inner_text()
            else:
                # Fallback: tentar extrair do aria-label do card
                aria = await card.get_attribute("aria-label") or ""
                if " - " in aria:
                    company = aria.split(" - ")[0]

            # Localização
            location = ""
            loc_el = await card.query_selector(self.SELECTORS["location"])
            if loc_el:
                aria = await loc_el.get_attribute("aria-label") or ""
                # "Local de trabalho: São Paulo - SP"
                if ":" in aria:
                    location = aria.split(": ", 1)[-1]
                else:
                    location = await loc_el.inner_text()

            # Modelo de trabalho (Remoto, Híbrido, Presencial)
            work_model = ""
            model_el = await card.query_selector(self.SELECTORS["work_model"])
            if model_el:
                aria = await model_el.get_attribute("aria-label") or ""
                if ":" in aria:
                    work_model = aria.split(": ", 1)[-1]
                else:
                    work_model = await model_el.inner_text()

            # Data de publicação
            published = ""
            date_el = await card.query_selector(self.SELECTORS["published_date"])
            if date_el:
                text = await date_el.inner_text()
                # "Publicada em: 10/01/2025"
                match = re.search(r"(\d{2}/\d{2}/\d{4})", text)
                if match:
                    published = match.group(1)

            return {
                "url": href if href.startswith("http") else f"https://portal.gupy.io{href}",
                "title": title.strip(),
                "company": company.strip(),
                "location": location.strip(),
                "work_model": work_model.strip(),
                "published_date": published,
            }

        except Exception as e:
            logger.debug(f"Erro ao extrair card: {e}")
            return None

    async def scrape_job_detail(self, url: str) -> dict:
        """
        Extrai detalhes completos de uma vaga específica.

        Args:
            url: URL da página de detalhes da vaga

        Returns:
            Dict com HTML bruto e metadados
        """
        logger.debug("Extraindo detalhes da vaga", url=url[:80])

        async with self.browser.get_page() as page:
            # Navega para a página de detalhes
            await self._navigate_with_retry(page, url)
            await humanize_delay(1.0, 2.0)

            # Scroll para carregar todo o conteúdo
            await humanize_scroll(page, scroll_count=3)

            # Extrai HTML completo
            html = await page.content()

            # Extrai metadados básicos
            title = ""
            title_el = await page.query_selector(self.SELECTORS["detail_title"])
            if title_el:
                title = await title_el.inner_text()

            # URL final (pode ter redirecionado)
            final_url = page.url

            # Extrai empresa do subdomínio
            company = ""
            match = re.search(r"https://([^.]+)\.gupy\.io", final_url)
            if match:
                company = match.group(1).replace("-", " ").title()

            return {
                "url": url,
                "final_url": final_url,
                "title": title.strip(),
                "company": company,
                "html": html,
                "extracted_at": datetime.now().isoformat(),
            }


async def main():
    """Função de teste para executar o scraper diretamente."""
    import argparse

    from src.ingestion import BrowserManager

    parser = argparse.ArgumentParser(description="Scraper Gupy")
    parser.add_argument("--query", default="Data Engineer", help="Termo de busca")
    parser.add_argument("--max-jobs", type=int, default=10, help="Máximo de vagas")
    parser.add_argument("--headless", action="store_true", help="Executar sem interface")
    parser.add_argument("--debug", action="store_true", help="Modo debug (mostra navegador)")

    args = parser.parse_args()

    headless = args.headless or not args.debug

    async with BrowserManager(headless=headless) as browser:
        scraper = GupyScraper(browser)
        files = await scraper.run(query=args.query, max_jobs=args.max_jobs)
        print(f"\n✅ Salvos {len(files)} arquivos em data/bronze/gupy/")


if __name__ == "__main__":
    asyncio.run(main())
