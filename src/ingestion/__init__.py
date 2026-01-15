"""
Módulo de ingestão - Camada Bronze.
Responsável pela coleta de dados via web scraping.
"""

from src.ingestion.browser import BrowserManager
from src.ingestion.proxy_manager import ProxyManager

__all__ = ["BrowserManager", "ProxyManager"]
