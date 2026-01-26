"""
Configuração das empresas alvo para scraping de vagas.

Baseado no estudo de mercado: lista_empresas.md
Organizado por ATS (Applicant Tracking System) para otimizar a coleta.
"""

from dataclasses import dataclass
from enum import Enum


class ATSType(Enum):
    """Tipos de ATS suportados."""

    GUPY = "gupy"
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    SMARTRECRUITERS = "smartrecruiters"
    WORKDAY = "workday"
    LINKEDIN = "linkedin"


@dataclass
class Company:
    """Representa uma empresa alvo."""

    name: str
    ats: ATSType
    identifier: str  # ID ou token usado na API do ATS
    category: str  # Categoria interna (banco, fintech, tech, etc)
    priority: int = 1  # 1 = alta, 2 = média, 3 = baixa
    remote_friendly: bool = False
    notes: str | None = None
    sector: str | None = None  # Setor oficial para dim_empresa


# =============================================================================
# MAPEAMENTO DE SETORES POR CATEGORIA
# =============================================================================
SECTOR_BY_CATEGORY = {
    "banco": "Serviços Financeiros",
    "fintech": "Fintech",
    "tech": "Tecnologia",
    "proptech": "PropTech",
    "games": "Games/Entretenimento",
    "media": "Mídia/Entretenimento",
    "consultoria": "Consultoria/TI",
    "varejo": "Varejo",
    "industria": "Indústria",
    "energia": "Energia",
    "financeiro": "Serviços Financeiros",
    "foodtech": "FoodTech",
    "logistica": "Logística",
    "edtech": "EdTech",
    "healthtech": "HealthTech",
}


def get_sector_for_company(company: "Company") -> str:
    """Retorna o setor oficial de uma empresa baseado na categoria."""
    if company.sector:
        return company.sector
    return SECTOR_BY_CATEGORY.get(company.category, "Outros")


# =============================================================================
# GUPY - Dominante no Brasil
# API: https://portal.api.gupy.io/api/v1/jobs?companyId={id}
# =============================================================================
GUPY_COMPANIES = [
    # --- Bancos e Fintechs ---
    # Nota: Itaú e BB usam sistemas próprios ou Workday, não Gupy
    Company(
        "BTG Pactual",
        ATSType.GUPY,
        "btgpactual",
        "banco",
        1,
        True,
        "Cultura meritocrática, viés quantitativo",
    ),
    Company(
        "C6 Bank",
        ATSType.GUPY,
        "c6bank",
        "fintech",
        1,
        True,
        "Crescimento acelerado, personalização de crédito",
    ),
    Company("Banco Inter", ATSType.GUPY, "bancointer", "fintech", 1, True, "Super App, BH"),
    Company("PicPay", ATSType.GUPY, "picpay", "fintech", 1, True, "Big Data em tempo real"),
    Company("PagBank", ATSType.GUPY, "pagbank", "fintech", 2, True),
    Company("Neon", ATSType.GUPY, "neon", "fintech", 2, True, "Foco classes C e D"),
    Company("Will Bank", ATSType.GUPY, "willbank", "fintech", 2, True, "Fintech nordestina"),
    # --- Tech Companies ---
    Company("iFood", ATSType.GUPY, "ifood", "tech", 1, True, "AI para logística, open source"),
    Company("Globo", ATSType.GUPY, "globo", "media", 1, True, "MediaTech, Big Data streaming"),
    Company("TOTVS", ATSType.GUPY, "totvs", "tech", 2, False, "Maior software ERP Brasil"),
    Company("RD Station", ATSType.GUPY, "rdstation", "tech", 1, True, "Floripa, cultura produto"),
    # --- Varejo e Indústria ---
    Company(
        "Magazine Luiza",
        ATSType.GUPY,
        "magazineluiza",
        "varejo",
        1,
        True,
        "LuizaLabs, case de transformação",
    ),
    Company("Ambev", ATSType.GUPY, "ambev", "industria", 1, False, "App BEES, logística massiva"),
    Company("Ambev Tech", ATSType.GUPY, "ambevtech", "industria", 1, False, "Tech hub da Ambev"),
    Company("Localiza", ATSType.GUPY, "localiza", "varejo", 2, False, "Telemetria veicular"),
    Company("Suzano", ATSType.GUPY, "suzano", "industria", 2, False, "Maior celulose do mundo"),
    Company("B3", ATSType.GUPY, "b3", "financeiro", 1, False, "Bolsa, baixa latência"),
    Company(
        "Grupo Boticário", ATSType.GUPY, "grupoboticario", "varejo", 1, True, "Beleza e cosméticos"
    ),
    Company(
        "RaiaDrogasil",
        ATSType.GUPY,
        "raiadrogasil",
        "varejo",
        1,
        True,
        "Maior rede farmácias do Brasil",
    ),
    Company(
        "Unilever", ATSType.GUPY, "unilever", "industria", 1, True, "FMCG global, dados de consumo"
    ),
    Company("Nestlé", ATSType.GUPY, "nestle", "industria", 1, True, "FMCG global, supply chain"),
    Company("Vale", ATSType.GUPY, "vale", "industria", 1, False, "Mineração, IoT massivo"),
    Company(
        "Heineken", ATSType.GUPY, "heineken", "industria", 2, True, "Bebidas, dados consumidor"
    ),
    Company(
        "Grupo Carrefour",
        ATSType.GUPY,
        "grupocarrefourbrasil",
        "varejo",
        1,
        True,
        "Varejo alimentar, Big Data",
    ),
    Company("Siemens", ATSType.GUPY, "siemens", "industria", 1, True, "Tecnologia industrial, IoT"),
    Company("Vivo Telefônica", ATSType.GUPY, "vivo", "tech", 1, True, "Telecom, dados massivos"),
    # --- Consultorias ---
    Company(
        "Stefanini",
        ATSType.GUPY,
        "stefanini",
        "consultoria",
        3,
        True,
        "Multinacional brasileira TI",
    ),
    Company("Semantix", ATSType.GUPY, "semantix", "consultoria", 2, True, "Big Data e IA"),
    Company("BHS", ATSType.GUPY, "bhs", "consultoria", 3, True, "Parceira Microsoft, MG"),
    Company("IBM", ATSType.GUPY, "ibm", "consultoria", 1, True, "BigTech, Watson AI"),
    Company(
        "Accenture",
        ATSType.GUPY,
        "accenture",
        "consultoria",
        1,
        True,
        "Big Four consultoria, global",
    ),
    Company(
        "Deloitte", ATSType.GUPY, "deloittebrasil", "consultoria", 1, True, "Big Four, analytics"
    ),
]


# =============================================================================
# GREENHOUSE - Startups Tech Maduras
# API: https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true
# =============================================================================
GREENHOUSE_COMPANIES = [
    # --- Fintechs ---
    Company(
        "Nubank", ATSType.GREENHOUSE, "nubank", "fintech", 1, True, "Referência mundial, Clojure"
    ),
    Company("Stone", ATSType.GREENHOUSE, "stone", "fintech", 1, True, "Cultura 'brutal facts'"),
    Company(
        "XP Inc", ATSType.GREENHOUSE, "xpinc", "fintech", 1, True, "Alta performance, Databricks"
    ),
    Company(
        "Creditas",
        ATSType.GREENHOUSE,
        "creditas",
        "fintech",
        1,
        True,
        "Empréstimo com garantia, ML para scoring",
    ),
    # --- Tech Companies ---
    Company(
        "QuintoAndar",
        ATSType.GREENHOUSE,
        "quintoandar",
        "proptech",
        1,
        True,
        "Precificação imóveis",
    ),
    Company(
        "Wildlife Studios",
        ATSType.GREENHOUSE,
        "wildlifestudios",
        "games",
        1,
        True,
        "Games, telemetria global",
    ),
    Company("Gympass (Wellhub)", ATSType.GREENHOUSE, "gympass", "tech", 1, True, "Global, inglês"),
    Company(
        "Hotmart",
        ATSType.GREENHOUSE,
        "hotmart",
        "tech",
        1,
        True,
        "Unicórnio BH, economia criadores",
    ),
    Company(
        "Loggi",
        ATSType.GREENHOUSE,
        "loggi",
        "logistica",
        1,
        True,
        "Logística, algoritmos roteirização",
    ),
    Company("Neoway", ATSType.GREENHOUSE, "neoway", "tech", 1, True, "Big Data B2B, Floripa"),
    # --- Consultorias ---
    Company(
        "ThoughtWorks",
        ATSType.GREENHOUSE,
        "thoughtworks",
        "consultoria",
        1,
        True,
        "Excelência engenharia",
    ),
    Company(
        "CI&T",
        ATSType.GREENHOUSE,
        "ciaboratoryinc",
        "consultoria",
        1,
        True,
        "Multinacional BR, Lean Digital",
    ),
]


# =============================================================================
# LEVER - Empresas Menores/Internacionais
# API: https://api.lever.co/v0/postings/{company}?mode=json
# =============================================================================
LEVER_COMPANIES = [
    Company("Stripe", ATSType.LEVER, "stripe", "fintech", 1, True, "Pagamentos global"),
    Company("Figma", ATSType.LEVER, "figma", "tech", 1, True, "Design tools"),
    Company("Notion", ATSType.LEVER, "notion", "tech", 1, True, "Produtividade"),
    Company("Vercel", ATSType.LEVER, "vercel", "tech", 1, True, "Frontend cloud"),
    Company("Supabase", ATSType.LEVER, "supabase", "tech", 1, True, "Open source Firebase"),
]


# =============================================================================
# SMARTRECRUITERS
# API: https://api.smartrecruiters.com/v1/companies/{id}/postings?country=br
# =============================================================================
SMARTRECRUITERS_COMPANIES = [
    Company(
        "Serasa Experian",
        ATSType.SMARTRECRUITERS,
        "serasaexperian",
        "financeiro",
        1,
        False,
        "Bureau de crédito",
    ),
    Company(
        "Keyrus Brasil",
        ATSType.SMARTRECRUITERS,
        "keyrus",
        "consultoria",
        2,
        True,
        "Data Intelligence",
    ),
]


# =============================================================================
# WORKDAY - Multinacionais (mais difícil de scrapar)
# Requer interceptação de requests
# =============================================================================
WORKDAY_COMPANIES = [
    Company(
        "Bradesco", ATSType.WORKDAY, "bradesco", "banco", 1, False, "Azure, cultura tradicional"
    ),
    Company(
        "Santander Brasil", ATSType.WORKDAY, "santander", "banco", 1, False, "Integração global"
    ),
    Company(
        "Natura &Co", ATSType.WORKDAY, "naturaco", "varejo", 2, False, "Cosméticos, dados globais"
    ),
    Company("Avanade", ATSType.WORKDAY, "avanade", "consultoria", 2, True, "Microsoft/Accenture"),
]


# =============================================================================
# LINKEDIN JOBS - Fallback e empresas sem ATS conhecido
# =============================================================================
LINKEDIN_COMPANIES = [
    Company(
        "Mercado Livre", ATSType.LINKEDIN, "mercadolibre", "tech", 1, True, "Maior AL, Eightfold"
    ),
    Company("Google Brasil", ATSType.LINKEDIN, "google", "tech", 1, True, "BigTech"),
    Company("Microsoft Brasil", ATSType.LINKEDIN, "microsoft", "tech", 1, True, "BigTech"),
    Company("Amazon Brasil", ATSType.LINKEDIN, "amazon", "tech", 1, True, "BigTech, AWS"),
    Company("Meta Brasil", ATSType.LINKEDIN, "meta", "tech", 1, True, "BigTech"),
    Company("Spotify", ATSType.LINKEDIN, "spotify", "tech", 1, True, "Streaming, dados"),
    Company("Netflix", ATSType.LINKEDIN, "netflix", "tech", 1, True, "Streaming, ML"),
]


# =============================================================================
# AGREGADORES
# =============================================================================
def get_all_companies() -> list[Company]:
    """Retorna todas as empresas configuradas."""
    return (
        GUPY_COMPANIES
        + GREENHOUSE_COMPANIES
        + LEVER_COMPANIES
        + SMARTRECRUITERS_COMPANIES
        + WORKDAY_COMPANIES
        + LINKEDIN_COMPANIES
    )


def get_companies_by_ats(ats: ATSType) -> list[Company]:
    """Retorna empresas filtradas por tipo de ATS."""
    return [c for c in get_all_companies() if c.ats == ats]


def get_high_priority_companies() -> list[Company]:
    """Retorna empresas de alta prioridade (priority=1)."""
    return [c for c in get_all_companies() if c.priority == 1]


def get_remote_friendly_companies() -> list[Company]:
    """Retorna empresas que costumam ter vagas remotas."""
    return [c for c in get_all_companies() if c.remote_friendly]


# Estatísticas
if __name__ == "__main__":
    all_companies = get_all_companies()
    print(f"Total de empresas configuradas: {len(all_companies)}")
    print(f"  - Gupy: {len(GUPY_COMPANIES)}")
    print(f"  - Greenhouse: {len(GREENHOUSE_COMPANIES)}")
    print(f"  - Lever: {len(LEVER_COMPANIES)}")
    print(f"  - SmartRecruiters: {len(SMARTRECRUITERS_COMPANIES)}")
    print(f"  - Workday: {len(WORKDAY_COMPANIES)}")
    print(f"  - LinkedIn: {len(LINKEDIN_COMPANIES)}")
    print(f"\nAlta prioridade: {len(get_high_priority_companies())}")
    print(f"Remote-friendly: {len(get_remote_friendly_companies())}")
