"""
Módulo de scrapers - implementações por plataforma.
"""

# Compatibilidade para quem importar 'src.ingestion.scrapers'
from src.ingestion.scrapers.api_scrapers import GupySearchScraper, run_search_scrapers
from src.ingestion.scrapers.base import BaseScraper
from src.ingestion.scrapers.gupy import GupyScraper
from src.ingestion.scrapers.vagas import VagasScraper
from src.ingestion.scrapers.workday import WorkdayScraper

__all__ = [
    "BaseScraper",
    "GupySearchScraper",
    "GupyScraper",
    "VagasScraper",
    "WorkdayScraper",
    "run_search_scrapers",
]
