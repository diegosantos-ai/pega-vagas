"""
Validador centralizado para vagas.

Define regras de filtragem para:
- Modalidade de trabalho (remoto vs presencial)
- País/região da vaga (Brasil vs exterior)
"""

import re
from typing import Optional

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
    "spain", "espanha", "españa",
    "portugal",
    "usa", "united states", "estados unidos", "eua",
    "uk", "united kingdom", "reino unido", "inglaterra",
    "germany", "alemanha", "deutschland",
    "france", "frança",
    "italy", "itália", "italia",
    "netherlands", "holanda",
    "canada", "canadá",
    "mexico", "méxico",
    "argentina",
    "chile",
    "colombia", "colômbia",
    "india", "índia",
    "ireland", "irlanda",
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


def is_remote_work(text: str, modelo_trabalho: Optional[str] = None) -> bool:
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


def is_brazil_location(
    text: str,
    pais: Optional[str] = None,
    empresa_validada: bool = False
) -> bool:
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
    titulo = job.get("titulo_original", "") or job.get("title", "")
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
    
    # Adiciona location de outras fontes
    loc_text += " " + job.get("location", "")
    loc_text += " " + job.get("location_name", "")
    
    # Descrição para análise adicional
    descricao = job.get("descricao_resumida", "") or job.get("description", "")
    
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
                motivo=reason
            )
    
    logger.info(
        "Filtragem concluída",
        total=len(jobs),
        validas=len(valid_jobs),
        rejeitadas_remoto=rejected["not_remote"],
        rejeitadas_brasil=rejected["not_brazil"],
    )
    
    return valid_jobs
