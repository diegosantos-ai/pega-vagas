"""
Scraper para LinkedIn Jobs (Visualização Pública).

A busca pública do LinkedIn permite visualizar vagas sem login,
mas é agressiva com rate limiting e detecção de bots.
Usa Camoufox para mitigar.
"""

from datetime import datetime
from pathlib import Path

import structlog

from src.ingestion.browser import humanize_delay, humanize_scroll
from src.ingestion.scrapers.base import BaseScraper

logger = structlog.get_logger()


class LinkedInScraper(BaseScraper):
    """
    Scraper para LinkedIn (Public Jobs).
    
    Filtros de URL úteis:
    - f_WT=2: Remoto
    - f_WT=1: Presencial
    - f_WT=3: Híbrido
    - geoId=106057199: Brasil
    """

    platform_name = "linkedin"
    
    # URL base de busca (filtros: Brasil + Remoto)
    search_url = (
        "https://www.linkedin.com/jobs/search?"
        "keywords={query}"
        "&location=Brazil"
        "&geoId=106057199"
        "&f_WT=2"  # Filtro REMOTO
        "&trk=public_jobs_jobs-search-bar_search-submit"
        "&position=1"
        "&pageNum=0"
    )

    # Seletores da interface pública (podem mudar com frequência)
    SELECTORS = {
        # Lista de cards
        "job_card": "li:has(.base-card)", 
        "card_link": "a.base-card__full-link",
        "card_title": ".base-search-card__title",
        "card_company": ".base-search-card__subtitle",
        "card_location": ".job-search-card__location",
        "card_date": "time",
        
        # Botão "Ver mais vagas" (scroll infinito ou botão)
        "load_more": "button.infinite-scroller__show-more-button",
        
        # Detalhes (na página da vaga)
        "detail_title": "h1.top-card-layout__title",
        "detail_company": "a.top-card-layout__company-url",
        "detail_description": ".description__text, .show-more-less-html__markup",
        "detail_criteria": ".description__job-criteria-list",
    }

    async def scrape_listings(
        self,
        query: str,
        location: str | None = None,
        max_pages: int = 3,
    ) -> list[dict]:
        listings = []
        # Monta URL (adiciona aspas na query para exatidão, se desejar)
        search_url = self.search_url.format(query=query)
        
        logger.info("Iniciando busca LinkedIn", query=query, url=search_url)

        async with self.browser.get_page() as page:
            await self._navigate_with_retry(page, search_url)
            await humanize_delay(2.0, 4.0)
            
            # Tenta carregar mais vagas (scroll + click)
            # O LinkedIn publico carrega ~25 vagas inicialmente
            for _ in range(max_pages):
                await humanize_scroll(page, scroll_count=5)
                await humanize_delay(1.5, 3.0)
                
                # Tenta clicar em "Ver mais" se existir
                try:
                    load_more = await page.query_selector(self.SELECTORS["load_more"])
                    if load_more and await load_more.is_visible():
                        await load_more.click()
                        await humanize_delay(2.0, 3.0)
                except Exception:
                    pass

            # Extração dos cards
            cards = await page.query_selector_all(self.SELECTORS["job_card"])
            logger.info(f"Encontrados {len(cards)} cards (LinkedIn)")

            for card in cards:
                try:
                    # Título
                    title_el = await card.query_selector(self.SELECTORS["card_title"])
                    title = await title_el.inner_text() if title_el else "N/A"
                    
                    # Link
                    link_el = await card.query_selector(self.SELECTORS["card_link"])
                    url = await link_el.get_attribute("href") if link_el else None
                    
                    if not url:
                        continue
                        
                    # Remove tracking params do URL
                    if "?" in url:
                        url = url.split("?")[0]

                    # Empresa
                    company_el = await card.query_selector(self.SELECTORS["card_company"])
                    company = await company_el.inner_text() if company_el else "N/A"
                    
                    listings.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "url": url,
                        "work_model": "Remoto" # Forçado pelo filtro f_WT=2
                    })

                except Exception as e:
                    logger.debug(f"Erro ao extrair card LinkedIn: {e}")
                    continue

        return listings

    async def scrape_job_detail(self, url: str) -> dict:
        logger.debug("Extraindo detalhes LinkedIn", url=url)
        
        async with self.browser.get_page() as page:
            try:
                await self._navigate_with_retry(page, url)
            except Exception as e:
                # Debug: salva HTML se falhar
                html = await page.content()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                debug_file = Path(f"data/bronze/linkedin/debug_error_{timestamp}.html")
                debug_file.parent.mkdir(parents=True, exist_ok=True)
                debug_file.write_text(html, encoding="utf-8")
                logger.error(f"Erro ao navegar detalhes (HTML salvo em {debug_file}): {e}")
                raise e

            # LinkedIn detalhe público as vezes pede login/modal, vamos tentar fechar ou ignorar
            await humanize_delay(2.0, 3.0)
            
            # Tenta expandir descrição se tiver botão "Ver mais"
            try:
                expand_btn = await page.query_selector("button.show-more-less-html__button")
                if expand_btn:
                    await expand_btn.click()
                    await humanize_delay(0.5, 1.0)
            except:
                pass

            html = await page.content()
            
            # Tenta extrair título para confirmar sucesso
            title_el = await page.query_selector(self.SELECTORS["detail_title"])
            title = await title_el.inner_text() if title_el else "N/A"

            return {
                "url": url,
                "title": title.strip(),
                "html": html,
                "platform": "linkedin",
                # Empresa e outros dados virão do LLM processando o HTML
            }

    def _detect_captcha(self, html: str) -> bool:
        """Override: LinkedIn tem 'recaptcha' no source mesmo sem bloqueio."""
        # Só considera captcha se tiver título explícito de verificação
        if "security verification" in html.lower():
            return True
        if "challenge" in html.lower() and "linkedin" not in html.lower():
            return True
        return False
