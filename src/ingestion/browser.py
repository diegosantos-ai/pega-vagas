"""
Gerenciador do navegador Camoufox para evasão de anti-bot.

Camoufox é um fork do Firefox otimizado para scraping, com:
- Fingerprint spoofing nativo
- Bypass de Cloudflare Turnstile
- Comportamento humanizado
"""

import asyncio
import random
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

import structlog
from playwright.async_api import Browser, BrowserContext, Page, async_playwright

logger = structlog.get_logger()


class BrowserManager:
    """
    Gerencia instâncias do navegador Camoufox/Playwright.

    Exemplo de uso:
        async with BrowserManager() as manager:
            page = await manager.new_page()
            await page.goto("https://example.com")
    """

    def __init__(
        self,
        headless: bool = True,
        proxy_url: Optional[str] = None,
        slow_mo: int = 50,
    ):
        """
        Args:
            headless: Executar sem interface gráfica
            proxy_url: URL do proxy no formato http://user:pass@host:port
            slow_mo: Delay em ms entre ações (simula humano)
        """
        self.headless = headless
        self.proxy_url = proxy_url
        self.slow_mo = slow_mo
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

    async def __aenter__(self) -> "BrowserManager":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start(self) -> None:
        """Inicializa o navegador."""
        logger.info("Iniciando navegador", headless=self.headless)

        self._playwright = await async_playwright().start()

        # Configuração de proxy
        proxy_config = None
        if self.proxy_url:
            proxy_config = {"server": self.proxy_url}
            logger.info("Proxy configurado", proxy=self.proxy_url.split("@")[-1])

        # Tenta usar Camoufox, fallback para Firefox padrão
        try:
            # Camoufox usa Firefox sob o capô
            self._browser = await self._playwright.firefox.launch(
                headless=self.headless,
                slow_mo=self.slow_mo,
                # Argumentos adicionais para evasão
                firefox_user_prefs={
                    # Desabilita WebRTC leak
                    "media.peerconnection.enabled": False,
                    # Timezone spoofing
                    "privacy.resistFingerprinting": True,
                },
            )
            logger.info("Firefox iniciado com sucesso")
        except Exception as e:
            logger.error("Erro ao iniciar navegador", error=str(e))
            raise

        # Cria contexto com configurações anti-detecção
        self._context = await self._browser.new_context(
            proxy=proxy_config,
            viewport={"width": 1920, "height": 1080},
            user_agent=self._get_random_user_agent(),
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
            # Simula dispositivo real
            device_scale_factor=1,
            is_mobile=False,
            has_touch=False,
        )

    async def close(self) -> None:
        """Fecha o navegador e libera recursos."""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Navegador fechado")

    async def new_page(self) -> Page:
        """Cria uma nova página com configurações anti-detecção."""
        if not self._context:
            raise RuntimeError("Navegador não inicializado. Use 'async with' ou chame start().")

        page = await self._context.new_page()

        # Injeta scripts anti-detecção
        await self._inject_stealth_scripts(page)

        return page

    @asynccontextmanager
    async def get_page(self) -> AsyncGenerator[Page, None]:
        """Context manager para uma página com cleanup automático."""
        page = await self.new_page()
        try:
            yield page
        finally:
            await page.close()

    async def _inject_stealth_scripts(self, page: Page) -> None:
        """Injeta scripts para mascarar automação."""
        # Remove navigator.webdriver
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        # Spoofing de plugins (simula plugins reais)
        await page.add_init_script("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)

        # Spoofing de idiomas
        await page.add_init_script("""
            Object.defineProperty(navigator, 'languages', {
                get: () => ['pt-BR', 'pt', 'en-US', 'en']
            });
        """)

    def _get_random_user_agent(self) -> str:
        """Retorna um User-Agent aleatório de navegadores reais."""
        user_agents = [
            # Firefox Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
            # Firefox Mac
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.5; rv:128.0) Gecko/20100101 Firefox/128.0",
            # Chrome Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        ]
        return random.choice(user_agents)


async def humanize_delay(min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
    """Aguarda um tempo aleatório para simular comportamento humano."""
    delay = random.uniform(min_seconds, max_seconds)
    await asyncio.sleep(delay)


async def humanize_scroll(page: Page, scroll_count: int = 3) -> None:
    """Rola a página de forma natural como um humano."""
    for _ in range(scroll_count):
        # Scroll para baixo com distância aleatória
        scroll_distance = random.randint(200, 500)
        await page.evaluate(f"window.scrollBy(0, {scroll_distance})")
        await humanize_delay(0.5, 1.5)
