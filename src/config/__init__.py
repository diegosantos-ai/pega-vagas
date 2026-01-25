"""
Módulo de configuração do Pega-Vagas.
"""

from src.config.companies import (
    GREENHOUSE_COMPANIES,
    GUPY_COMPANIES,
    LEVER_COMPANIES,
    SMARTRECRUITERS_COMPANIES,
    ATSType,
    Company,
    get_all_companies,
    get_companies_by_ats,
    get_high_priority_companies,
    get_remote_friendly_companies,
)

__all__ = [
    "ATSType",
    "Company",
    "get_all_companies",
    "get_companies_by_ats",
    "get_high_priority_companies",
    "get_remote_friendly_companies",
    "GUPY_COMPANIES",
    "GREENHOUSE_COMPANIES",
    "LEVER_COMPANIES",
    "SMARTRECRUITERS_COMPANIES",
]
