"""
Validador centralizado para vagas.

Define regras de filtragem para:
- Modalidade de trabalho (remoto vs presencial)
- País/região da vaga (Brasil vs exterior)
- Data de publicação (últimos X dias)
"""

import re
from datetime import datetime, timedelta

import structlog

logger = structlog.get_logger()


# =============================================================================
# PADRÕES DE DETECÇÃO
# =============================================================================

# Indicadores POSITIVOS de trabalho remoto
REMOTE_POSITIVE_PATTERNS = [
    r"\b100%?\s*remoto\b",
    r"\bfully\s*remote\b",
    r"\bfull[\s-]*remote\b",
    r"\bremote[\s-]*first\b",
    r"\btrabalho\s*remoto\b",
    r"\bhome[\s-]*office\b",
    r"\banywhere\b",
    r"\bwork\s*from\s*home\b",
    r"\bwfh\b",
    r"\bremote\s*only\b",
    r"\bremoto\s*integral\b",
]

# Indicadores NEGATIVOS (descartam a vaga mesmo que tenha "remoto")
REMOTE_NEGATIVE_PATTERNS = [
    r"\bh[íi]brido\b",
    r"\bhybrid\b",
    r"\bpresencial\b",
    r"\bon[\s-]?site\b",
    r"\boffice[\s-]*based\b",
    r"\b\d+\s*(dias?|days?)\s*(por\s*)?(semana|week|m[êe]s|month)",
    r"\bvisitas?\s*(ao\s*)?(escrit[óo]rio|office)",
    r"\bnear\s*(the\s*)?office\b",
    r"\bmust\s*be\s*(located|based)\b",
]

# Países inválidos (se aparecer na localização, descarta)
INVALID_COUNTRIES = [
    "spain",
    "espanha",
    "españa",
    "portugal",
    "usa",
    "united states",
    "estados unidos",
    "eua",
    "uk",
    "united kingdom",
    "reino unido",
    "inglaterra",
    "germany",
    "alemanha",
    "deutschland",
    "france",
    "frança",
    "italy",
    "itália",
    "italia",
    "netherlands",
    "holanda",
    "canada",
    "canadá",
    "mexico",
    "méxico",
    "argentina",
    "chile",
    "colombia",
    "colômbia",
    "india",
    "índia",
    "ireland",
    "irlanda",
]

# Indicadores de Brasil (validam a vaga)
BRAZIL_POSITIVE_PATTERNS = [
    r"\bbrasil\b",
    r"\bbrazil\b",
    r"\b(são|sao)\s*paulo\b",
    r"\brio\s*(de\s*)?janeiro\b",
    r"\bbelo\s*horizonte\b",
    r"\bcuritiba\b",
    r"\bporto\s*alegre\b",
    r"\bfloripa|florian[óo]polis\b",
    r"\bbras[íi]lia\b",
    r"\brecife\b",
    r"\bsalvador\b",
    r"\bfortaleza\b",
    r"\b[A-Z]{2}\s*[-–]\s*Brasil\b",  # "SP - Brasil"
    r"\bremote\s*[\(\[\-]\s*brazil\b",
    r"\bremoto\s*[\(\[\-]\s*brasil\b",
]


def is_remote_work(text: str, modelo_trabalho: str | None = None) -> bool:
    """
    Verifica se o texto indica trabalho 100% remoto.

    Args:
        text: Texto para análise (título, descrição, localização)
        modelo_trabalho: Campo já extraído pelo LLM (se disponível)

    Returns:
        True se for trabalho remoto válido
    """
    if not text and not modelo_trabalho:
        return False

    # Se LLM já classificou
    if modelo_trabalho:
        modelo_lower = modelo_trabalho.lower().strip()
        if modelo_lower == "remoto":
            return True
        if modelo_lower in ["híbrido", "hibrido", "presencial", "hybrid"]:
            return False

    text_lower = text.lower() if text else ""

    # Primeiro verifica negativos (descartam)
    for pattern in REMOTE_NEGATIVE_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            logger.debug(f"Vaga descartada por padrão negativo: {pattern}")
            return False

    # Depois verifica positivos
    for pattern in REMOTE_POSITIVE_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True

    # Se modelo_trabalho é "Remoto" mas não passou nos padrões, aceita
    if modelo_trabalho and modelo_trabalho.lower() == "remoto":
        return True

    return False


def is_brazil_location(text: str, pais: str | None = None, empresa_validada: bool = False) -> bool:
    """
    Verifica se a vaga é para Brasil.

    Args:
        text: Texto de localização para análise
        pais: Campo de país já extraído (se disponível)
        empresa_validada: Se empresa está na lista de empresas validadas

    Returns:
        True se vaga for para Brasil
    """
    # Se empresa já está validada como tendo operação no Brasil
    if empresa_validada:
        # Mas ainda precisa verificar se a VAGA específica é para Brasil
        # (empresa pode ter vagas em múltiplos países)
        pass

    # Se país já foi extraído
    if pais:
        pais_lower = pais.lower().strip()
        if pais_lower in ["brasil", "brazil", "br"]:
            return True
        # Se é outro país explícito, descarta
        if pais_lower and pais_lower not in ["brasil", "brazil", "br", ""]:
            logger.debug(f"Vaga descartada por país: {pais}")
            return False

    text_lower = text.lower() if text else ""

    # Verifica países inválidos
    for country in INVALID_COUNTRIES:
        # Padrão mais específico para evitar falsos positivos
        pattern = rf"\b{re.escape(country)}\b"
        if re.search(pattern, text_lower, re.IGNORECASE):
            # Exceção: "Remote - Brazil, Spain" - tem Brasil também
            if any(re.search(p, text_lower, re.IGNORECASE) for p in BRAZIL_POSITIVE_PATTERNS):
                continue
            logger.debug(f"Vaga descartada por país inválido: {country}")
            return False

    # Verifica indicadores de Brasil
    for pattern in BRAZIL_POSITIVE_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True

    # Se empresa é validada e não encontrou país inválido, assume Brasil
    if empresa_validada:
        return True

    # Padrão: se não tem indicação clara, assume Brasil (pode ajustar depois)
    # Isso porque a maioria das empresas na nossa lista são brasileiras
    return True


def is_valid_job(job: dict, empresa_validada: bool = False) -> tuple[bool, str]:
    """
    Valida se uma vaga atende todos os critérios.

    Args:
        job: Dicionário com dados da vaga
        empresa_validada: Se empresa está na lista de empresas validadas

    Returns:
        Tuple (é_válida, motivo_rejeição)
    """
    # Extrai campos relevantes
    titulo = job.get("titulo_original", "") or job.get("title", "") or job.get("name", "")
    modelo = job.get("modelo_trabalho", "") or job.get("work_model", "")

    # Localidade pode ser dict ou string
    localidade = job.get("localidade", {})
    if isinstance(localidade, dict):
        pais = localidade.get("pais", "")
        cidade = localidade.get("cidade", "")
        estado = localidade.get("estado", "")
        loc_text = f"{cidade} {estado} {pais}".strip()
    else:
        pais = ""
        loc_text = str(localidade) if localidade else ""

    # Adiciona location de outras fontes (pode ser dict ou string)
    location = job.get("location", "")
    if isinstance(location, dict):
        loc_text += " " + location.get("name", "")
    elif location:
        loc_text += " " + str(location)

    location_name = job.get("location_name", "")
    if location_name:
        loc_text += " " + str(location_name)

    # Descrição para análise adicional
    # Descrição para análise adicional
    descricao = (
        job.get("descricao_resumida", "") or job.get("description", "") or job.get("html", "")
    )

    # Texto combinado para análise
    full_text = f"{titulo} {loc_text} {descricao}"

    # 1. Verificar se é REMOTO
    if not is_remote_work(full_text, modelo):
        return False, f"Não é remoto (modelo: {modelo})"

    # 2. Verificar se é BRASIL
    if not is_brazil_location(loc_text, pais, empresa_validada):
        return False, f"Não é Brasil (localização: {loc_text})"

    return True, "OK"


def filter_jobs(jobs: list[dict], empresa_validada: bool = False) -> list[dict]:
    """
    Filtra lista de vagas aplicando todos os critérios.

    Args:
        jobs: Lista de vagas
        empresa_validada: Se empresa está na lista validada

    Returns:
        Lista filtrada de vagas válidas
    """
    valid_jobs = []
    rejected = {"not_remote": 0, "not_brazil": 0, "other": 0}

    for job in jobs:
        is_valid, reason = is_valid_job(job, empresa_validada)

        if is_valid:
            valid_jobs.append(job)
        else:
            # Categoriza rejeição
            if "remoto" in reason.lower():
                rejected["not_remote"] += 1
            elif "brasil" in reason.lower():
                rejected["not_brazil"] += 1
            else:
                rejected["other"] += 1

            logger.debug(
                "Vaga rejeitada",
                titulo=job.get("titulo_original", job.get("title", ""))[:40],
                motivo=reason,
            )

    logger.info(
        "Filtragem concluída",
        total=len(jobs),
        validas=len(valid_jobs),
        rejeitadas_remoto=rejected["not_remote"],
        rejeitadas_brasil=rejected["not_brazil"],
    )

    return valid_jobs


# =============================================================================
# FILTRO DE DATA
# =============================================================================


def parse_date(date_value) -> datetime | None:
    """
    Converte diferentes formatos de data para datetime.

    Args:
        date_value: String ISO, datetime, ou timestamp

    Returns:
        datetime ou None se não conseguir parsear
    """
    if date_value is None:
        return None

    if isinstance(date_value, datetime):
        return date_value

    if isinstance(date_value, (int, float)):
        # Assume timestamp em segundos
        try:
            return datetime.fromtimestamp(date_value)
        except (ValueError, OSError):
            # Pode ser timestamp em milissegundos
            return datetime.fromtimestamp(date_value / 1000)

    if isinstance(date_value, str):
        # Tenta diferentes formatos
        formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_value, fmt)
            except ValueError:
                continue

    return None


def is_recent_job(job: dict, days: int = 7) -> tuple[bool, str]:
    """
    Verifica se a vaga foi publicada nos últimos X dias.

    Args:
        job: Dicionário com dados da vaga
        days: Número de dias (7 para teste, 1 para produção)

    Returns:
        Tuple (é_recente, motivo)
    """
    # Campos possíveis para data de publicação
    date_fields = [
        "data_publicacao",
        "published_at",
        "publishedAt",
        "created_at",
        "createdAt",
        "posted_on",
        "postedOn",
        "date",
        "updated_at",
        "updatedAt",
    ]

    pub_date = None
    for field in date_fields:
        if job.get(field):
            pub_date = parse_date(job[field])
            if pub_date:
                break

    # Se não tem data, verifica no metadata
    if not pub_date and job.get("_metadata"):
        metadata = job["_metadata"]
        for field in ["scraped_at", "collected_at"]:
            if metadata.get(field):
                pub_date = parse_date(metadata[field])
                if pub_date:
                    break

    # Se ainda não tem data, assume recente (benefício da dúvida)
    if not pub_date:
        logger.debug("Vaga sem data de publicação, assumindo recente")
        return True, "Sem data (assumindo recente)"

    cutoff = datetime.now() - timedelta(days=days)

    if pub_date < cutoff:
        return False, f"Vaga antiga ({pub_date.strftime('%Y-%m-%d')})"

    return True, f"Data válida ({pub_date.strftime('%Y-%m-%d')})"


def is_valid_job_full(
    job: dict,
    empresa_validada: bool = False,
    days: int = 7,
    check_date: bool = True,
) -> tuple[bool, str]:
    """
    Validação completa: remoto + Brasil + data.

    Args:
        job: Dicionário com dados da vaga
        empresa_validada: Se empresa está na lista validada
        days: Período de dias para considerar recente
        check_date: Se deve verificar data de publicação

    Returns:
        Tuple (é_válida, motivo_rejeição)
    """
    # Primeiro verifica remoto e Brasil
    is_valid, reason = is_valid_job(job, empresa_validada)
    if not is_valid:
        return False, reason

    # Depois verifica data
    if check_date:
        is_recent, date_reason = is_recent_job(job, days)
        if not is_recent:
            return False, date_reason

    return True, "OK"
