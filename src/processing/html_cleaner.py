"""
Limpeza e pré-processamento de HTML para reduzir tokens enviados ao LLM.

Remove elementos desnecessários (scripts, estilos, navegação)
e extrai apenas o texto relevante do corpo da página.
"""

import re
from typing import Optional

import structlog

logger = structlog.get_logger()

# Tentamos usar trafilatura para extração avançada, fallback para bs4
try:
    from trafilatura import extract as trafilatura_extract

    HAS_TRAFILATURA = True
except ImportError:
    HAS_TRAFILATURA = False

try:
    from bs4 import BeautifulSoup

    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


def clean_html(
    html: str,
    max_chars: int = 15000,
    include_tables: bool = True,
) -> str:
    """
    Limpa HTML removendo elementos desnecessários e extrai texto principal.

    Args:
        html: HTML bruto da página
        max_chars: Limite máximo de caracteres no resultado
        include_tables: Se True, tenta preservar estrutura de tabelas

    Returns:
        Texto limpo e formatado
    """
    if not html:
        return ""

    # Tenta trafilatura primeiro (melhor qualidade)
    if HAS_TRAFILATURA:
        text = _clean_with_trafilatura(html, include_tables)
        if text:
            return _truncate_smart(text, max_chars)

    # Fallback para BeautifulSoup
    if HAS_BS4:
        text = _clean_with_bs4(html)
        if text:
            return _truncate_smart(text, max_chars)

    # Último recurso: regex básico
    return _truncate_smart(_clean_with_regex(html), max_chars)


def _clean_with_trafilatura(html: str, include_tables: bool) -> Optional[str]:
    """Usa trafilatura para extração de alto nível."""
    try:
        text = trafilatura_extract(
            html,
            include_tables=include_tables,
            include_links=False,
            include_images=False,
            include_comments=False,
            deduplicate=True,
            favor_precision=True,
        )
        return text
    except Exception as e:
        logger.debug(f"Trafilatura falhou: {e}")
        return None


def _clean_with_bs4(html: str) -> Optional[str]:
    """Usa BeautifulSoup para limpeza manual."""
    try:
        soup = BeautifulSoup(html, "html.parser")

        # Remove elementos desnecessários
        for element in soup.find_all(
            ["script", "style", "nav", "header", "footer", "aside", "noscript", "iframe"]
        ):
            element.decompose()

        # Remove comentários
        for comment in soup.find_all(string=lambda text: isinstance(text, str) and "<!--" in text):
            comment.extract()

        # Remove elementos com classes típicas de navegação/footer
        noise_classes = [
            "nav",
            "navigation",
            "menu",
            "sidebar",
            "footer",
            "header",
            "cookie",
            "popup",
            "modal",
            "ad",
            "advertisement",
        ]
        for cls in noise_classes:
            for element in soup.find_all(class_=re.compile(cls, re.I)):
                element.decompose()

        # Extrai texto
        text = soup.get_text(separator="\n", strip=True)

        # Limpa linhas em branco excessivas
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text

    except Exception as e:
        logger.debug(f"BeautifulSoup falhou: {e}")
        return None


def _clean_with_regex(html: str) -> str:
    """Limpeza básica com regex (fallback)."""
    # Remove tags script e style
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.I)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.I)

    # Remove todas as tags HTML
    text = re.sub(r"<[^>]+>", " ", html)

    # Decodifica entidades HTML comuns
    text = text.replace("&nbsp;", " ")
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')

    # Remove espaços excessivos
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)

    return text.strip()


def _truncate_smart(text: str, max_chars: int) -> str:
    """
    Trunca texto de forma inteligente, tentando manter sentenças completas.
    """
    if len(text) <= max_chars:
        return text

    # Encontra o último ponto antes do limite
    truncated = text[:max_chars]
    last_period = truncated.rfind(".")

    if last_period > max_chars * 0.7:  # Se o ponto está nos últimos 30%
        return truncated[: last_period + 1]

    # Se não encontrou bom ponto de corte, trunca no espaço mais próximo
    last_space = truncated.rfind(" ")
    if last_space > max_chars * 0.9:
        return truncated[:last_space] + "..."

    return truncated + "..."
