"""
Módulo de scrapers - implementações por plataforma.
"""

from src.ingestion.scrapers.base import BaseScraper
from src.ingestion.scrapers.gupy import GupyScraper

__all__ = ["BaseScraper", "GupyScraper"]
