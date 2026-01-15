"""
Gerenciador de proxies residenciais para rotação de IP.

Suporta múltiplos provedores:
- Bright Data
- Smartproxy
- IPRoyal
"""

import random
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import structlog

logger = structlog.get_logger()


class ProxyProvider(str, Enum):
    """Provedores de proxy suportados."""

    BRIGHTDATA = "brightdata"
    SMARTPROXY = "smartproxy"
    IPROYAL = "iproyal"
    CUSTOM = "custom"


@dataclass
class ProxyConfig:
    """Configuração de um proxy."""

    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    country: str = "br"  # Código do país
    session_id: Optional[str] = None  # Para sticky sessions

    @property
    def url(self) -> str:
        """Retorna URL formatada para uso no navegador."""
        if self.username and self.password:
            return f"http://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"http://{self.host}:{self.port}"

    @property
    def url_censored(self) -> str:
        """Retorna URL com senha censurada para logs."""
        if self.username:
            return f"http://{self.username}:***@{self.host}:{self.port}"
        return f"http://{self.host}:{self.port}"


class ProxyManager:
    """
    Gerencia pool de proxies residenciais com rotação inteligente.

    Exemplo de uso:
        manager = ProxyManager(
            provider=ProxyProvider.SMARTPROXY,
            username="user",
            password="pass"
        )
        proxy = manager.get_rotating_proxy()
    """

    # Configurações por provedor
    PROVIDER_CONFIGS = {
        ProxyProvider.BRIGHTDATA: {
            "host": "brd.superproxy.io",
            "port": 22225,
            "session_prefix": "session-",
        },
        ProxyProvider.SMARTPROXY: {
            "host": "gate.smartproxy.com",
            "port": 10001,
            "session_prefix": "sessid-",
        },
        ProxyProvider.IPROYAL: {
            "host": "geo.iproyal.com",
            "port": 12321,
            "session_prefix": "session-",
        },
    }

    def __init__(
        self,
        provider: ProxyProvider = ProxyProvider.CUSTOM,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        country: str = "br",
    ):
        """
        Args:
            provider: Provedor de proxy (ou CUSTOM para configuração manual)
            host: Host do proxy (obrigatório se CUSTOM)
            port: Porta do proxy (obrigatório se CUSTOM)
            username: Usuário para autenticação
            password: Senha para autenticação
            country: Código do país para geolocalização
        """
        self.provider = provider
        self.username = username
        self.password = password
        self.country = country

        # Configura host/port baseado no provedor ou usa valores customizados
        if provider == ProxyProvider.CUSTOM:
            if not host or not port:
                raise ValueError("host e port são obrigatórios para provider CUSTOM")
            self.host = host
            self.port = port
        else:
            config = self.PROVIDER_CONFIGS[provider]
            self.host = config["host"]
            self.port = config["port"]

        self._session_counter = 0
        logger.info(
            "ProxyManager inicializado",
            provider=provider.value,
            host=self.host,
            country=country,
        )

    def get_rotating_proxy(self) -> ProxyConfig:
        """
        Retorna um proxy com IP rotativo (muda a cada requisição).
        Ideal para scraping de listagens.
        """
        # Sem session_id, o provedor rotaciona automaticamente
        return ProxyConfig(
            host=self.host,
            port=self.port,
            username=self._build_username(),
            password=self.password,
            country=self.country,
        )

    def get_sticky_proxy(self, duration_minutes: int = 10) -> ProxyConfig:
        """
        Retorna um proxy com IP fixo (sticky session).
        Ideal para navegação em múltiplas páginas da mesma vaga.

        Args:
            duration_minutes: Duração da sessão em minutos
        """
        self._session_counter += 1
        session_id = f"session-{self._session_counter}-{random.randint(1000, 9999)}"

        return ProxyConfig(
            host=self.host,
            port=self.port,
            username=self._build_username(session_id=session_id),
            password=self.password,
            country=self.country,
            session_id=session_id,
        )

    def _build_username(self, session_id: Optional[str] = None) -> Optional[str]:
        """Constrói username com parâmetros do provedor."""
        if not self.username:
            return None

        parts = [self.username]

        # Adiciona país
        if self.country:
            parts.append(f"country-{self.country}")

        # Adiciona sessão se sticky
        if session_id:
            parts.append(session_id)

        return "-".join(parts)

    @classmethod
    def from_url(cls, proxy_url: str) -> "ProxyManager":
        """
        Cria ProxyManager a partir de uma URL de proxy.

        Args:
            proxy_url: URL no formato http://user:pass@host:port
        """
        # Parse da URL
        from urllib.parse import urlparse

        parsed = urlparse(proxy_url)

        return cls(
            provider=ProxyProvider.CUSTOM,
            host=parsed.hostname or "",
            port=parsed.port or 8080,
            username=parsed.username,
            password=parsed.password,
        )


def load_proxy_from_env() -> Optional[ProxyManager]:
    """
    Carrega configuração de proxy das variáveis de ambiente.

    Retorna None se não configurado.
    """
    import os

    from dotenv import load_dotenv

    load_dotenv()

    proxy_url = os.getenv("PROXY_URL")
    if not proxy_url or proxy_url == "http://user:pass@proxy.example.com:8080":
        logger.warning("Proxy não configurado - usando conexão direta")
        return None

    provider_str = os.getenv("PROXY_PROVIDER", "custom").lower()

    try:
        provider = ProxyProvider(provider_str)
    except ValueError:
        provider = ProxyProvider.CUSTOM

    return ProxyManager.from_url(proxy_url)
