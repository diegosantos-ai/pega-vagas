"""
Módulo de scrapers - implementações por plataforma.
"""

from src.ingestion.scrapers.base import BaseScraper
from src.ingestion.scrapers.gupy import GupyScraper
from src.ingestion.scrapers.vagas import VagasScraper

__all__ = ["BaseScraper", "GupyScraper", "VagasScraper"]
