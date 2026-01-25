"""
Scraper específico para a plataforma Vagas.com.br.

Vagas.com.br é um dos sites mais tradicionais de vagas do Brasil,
com HTML mais simples e menos proteções anti-bot que a Gupy.

Estrutura:
- Busca: https://www.vagas.com.br/vagas-de-{termo-com-hifens}
- Detalhes: https://www.vagas.com.br/vagas/v{job_id}/{titulo}
"""

import asyncio
from datetime import datetime

import structlog
from playwright.async_api import Page

from src.ingestion.browser import humanize_delay, humanize_scroll
from src.ingestion.scrapers.base import BaseScraper

logger = structlog.get_logger()


class VagasScraper(BaseScraper):
    """
    Scraper para vagas da plataforma Vagas.com.br.

    Exemplo de uso:
        async with BrowserManager() as browser:
            scraper = VagasScraper(browser)
            files = await scraper.run(query="Data Engineer", max_jobs=50)
    """

    platform_name = "vagas"
    search_url = "https://www.vagas.com.br/vagas-de-{query}"

    # Seletores CSS
    SELECTORS = {
        # Página de listagem
        "job_cards": ".vaga",
        "job_title": ".link-detalhes-vaga",
        "company_name": ".emprVaga",
        "location": ".vaga-local",
        "level": ".nivelVaga",
        "published_date": ".data-publicacao",
        # Cookie banner
        "cookie_accept": "[data-action='accept-all'], .lgpd-accept, #lgpd-accept",
        # Página de detalhes
        "detail_title": "h1",
        "detail_company": ".job-shortdescription__company, .vaga-empresa, .exibe-nome-empresa",
        "detail_description": ".job-description__text, .vaga-descricao, .infoVaga",
        "detail_salary": ".job-shortdescription__salary, .vaga-salario",
        "detail_location": ".job-shortdescription__location",
        # Paginação
        "next_page": ".pagination .next a, a.proxima-pagina",
        "no_results": ".nao-encontrado, .no-results",
    }

    async def scrape_listings(
        self,
        query: str,
        location: str | None = None,
        max_pages: int = 3,
    ) -> list[dict]:
        """
        Extrai listagem de vagas a partir de uma busca no Vagas.com.br.

        Args:
            query: Termo de busca (ex: "Data Engineer")
            location: Não implementado ainda
            max_pages: Número máximo de páginas a processar

        Returns:
            Lista de dicts com dados básicos de cada vaga
        """
        listings = []

        # Formata a query para URL (espaços viram hífens)
        query_formatted = query.lower().replace(" ", "-")
        search_url = self.search_url.format(query=query_formatted)

        logger.info("Iniciando busca no Vagas.com.br", query=query, url=search_url)

        async with self.browser.get_page() as page:
            # Navega para a página de busca
            await self._navigate_with_retry(page, search_url)
            await humanize_delay(1.5, 2.5)

            # Fecha banner de cookies se existir
            await self._close_cookie_banner(page)

            # Verifica se há resultados
            no_results = await page.query_selector(self.SELECTORS["no_results"])
            if no_results:
                logger.warning("Nenhuma vaga encontrada para a busca", query=query)
                return []

            # Processa múltiplas páginas
            for page_num in range(max_pages):
                logger.debug(f"Processando página {page_num + 1}/{max_pages}")

                # Scroll para carregar conteúdo
                await humanize_scroll(page, scroll_count=2)

                # Extrai todos os cards de vagas
                job_cards = await page.query_selector_all(self.SELECTORS["job_cards"])
                logger.debug(f"Encontrados {len(job_cards)} cards na página {page_num + 1}")

                for card in job_cards:
                    try:
                        listing = await self._extract_listing_card(card)
                        if listing and listing.get("url"):
                            # Evita duplicatas
                            if not any(l["url"] == listing["url"] for l in listings):
                                listings.append(listing)
                    except Exception as e:
                        logger.debug(f"Erro ao extrair card: {e}")
                        continue

                # Tenta ir para próxima página
                next_button = await page.query_selector(self.SELECTORS["next_page"])
                if next_button and page_num < max_pages - 1:
                    try:
                        await next_button.click()
                        await humanize_delay(2.0, 3.0)
                    except Exception:
                        break
                else:
                    break

        logger.info(f"Extraídas {len(listings)} vagas da listagem")
        return listings

    async def _close_cookie_banner(self, page: Page) -> None:
        """Fecha banner de cookies se existir."""
        try:
            cookie_btn = await page.query_selector(self.SELECTORS["cookie_accept"])
            if cookie_btn:
                await cookie_btn.click()
                await humanize_delay(0.5, 1.0)
        except Exception:
            pass  # Ignora se não conseguir fechar

    async def _extract_listing_card(self, card) -> dict | None:
        """Extrai dados de um card de vaga na listagem."""
        try:
            # URL e título
            link_el = await card.query_selector(self.SELECTORS["job_title"])
            if not link_el:
                return None

            href = await link_el.get_attribute("href")
            title = await link_el.inner_text()

            if not href:
                return None

            # Empresa
            company = ""
            company_el = await card.query_selector(self.SELECTORS["company_name"])
            if company_el:
                company = await company_el.inner_text()

            # Localização
            location = ""
            loc_el = await card.query_selector(self.SELECTORS["location"])
            if loc_el:
                location = await loc_el.inner_text()

            # Nível/Senioridade
            level = ""
            level_el = await card.query_selector(self.SELECTORS["level"])
            if level_el:
                level = await level_el.inner_text()

            # Data de publicação
            published = ""
            date_el = await card.query_selector(self.SELECTORS["published_date"])
            if date_el:
                published = await date_el.inner_text()

            # Monta URL completa
            if href.startswith("/"):
                href = f"https://www.vagas.com.br{href}"

            return {
                "url": href,
                "title": title.strip(),
                "company": company.strip(),
                "location": location.strip(),
                "level": level.strip(),
                "published_date": published.strip(),
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

            # Fecha cookies
            await self._close_cookie_banner(page)

            # Scroll para carregar todo o conteúdo
            await humanize_scroll(page, scroll_count=2)

            # Extrai HTML completo
            html = await page.content()

            # Extrai metadados básicos
            title = ""
            title_el = await page.query_selector(self.SELECTORS["detail_title"])
            if title_el:
                title = await title_el.inner_text()

            # Empresa
            company = ""
            company_el = await page.query_selector(self.SELECTORS["detail_company"])
            if company_el:
                company = await company_el.inner_text()

            # Salário
            salary = ""
            salary_el = await page.query_selector(self.SELECTORS["detail_salary"])
            if salary_el:
                salary = await salary_el.inner_text()

            # Descrição
            description = ""
            desc_el = await page.query_selector(self.SELECTORS["detail_description"])
            if desc_el:
                description = await desc_el.inner_text()

            return {
                "url": url,
                "final_url": page.url,
                "title": title.strip(),
                "company": company.strip(),
                "salary": salary.strip(),
                "description_preview": description[:500] if description else "",
                "html": html,
                "extracted_at": datetime.now().isoformat(),
            }


async def main():
    """Função de teste para executar o scraper diretamente."""
    import argparse

    from src.ingestion import BrowserManager

    parser = argparse.ArgumentParser(description="Scraper Vagas.com.br")
    parser.add_argument("--query", default="Data Engineer", help="Termo de busca")
    parser.add_argument("--max-jobs", type=int, default=10, help="Máximo de vagas")
    parser.add_argument("--headless", action="store_true", help="Executar sem interface")
    parser.add_argument("--debug", action="store_true", help="Modo debug (mostra navegador)")

    args = parser.parse_args()

    headless = args.headless or not args.debug

    async with BrowserManager(headless=headless) as browser:
        scraper = VagasScraper(browser)
        files = await scraper.run(query=args.query, max_jobs=args.max_jobs)
        print(f"\n✅ Salvos {len(files)} arquivos em data/bronze/vagas/")


if __name__ == "__main__":
    asyncio.run(main())
