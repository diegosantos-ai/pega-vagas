"""
Módulo de scrapers - implementações por plataforma.
"""

from src.ingestion.scrapers.api_scrapers import (
    GreenhouseAPIScraper,
    GupyAPIScraper,
    LeverAPIScraper,
    SmartRecruitersAPIScraper,
)
from src.ingestion.scrapers.base import BaseScraper
from src.ingestion.scrapers.gupy import GupyScraper
from src.ingestion.scrapers.vagas import VagasScraper
from src.ingestion.scrapers.workday import WorkdayScraper

__all__ = [
    "BaseScraper",
    "GupyScraper",
    "VagasScraper",
    "WorkdayScraper",
    "GupyAPIScraper",
    "GreenhouseAPIScraper",
    "LeverAPIScraper",
    "SmartRecruitersAPIScraper",
]
