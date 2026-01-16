"""
Funções de normalização para títulos de vagas, senioridade e localização.

Este módulo resolve o problema de muitas vagas sendo classificadas como "Outro"
e melhora a extração de dados geográficos.
"""

import re
from typing import Optional


# =============================================================================
# MAPEAMENTOS DE TÍTULOS
# =============================================================================

TITLE_MAPPINGS = {
    "Data Engineer": [
        r"data\s*engineer",
        r"engenheiro\(?a?\)?\s*(de\s+)?dados",
        r"pessoa\s+engenheira?\s*(de\s+)?dados",
        r"data\s*eng\b",
        r"de\s*-\s*data\s*engineer",
    ],
    "Data Scientist": [
        r"data\s*scientist",
        r"cientista\s*(de\s+)?dados",
        r"pessoa\s+cientista\s*(de\s+)?dados",
        r"ds\s*-\s*data\s*scien",
    ],
    "Data Analyst": [
        r"data\s*analyst",
        r"analista\s*(de\s+)?dados",
        r"pessoa\s+analista\s*(de\s+)?dados",
        r"data\s*analytics\s*analyst",
    ],
    "BI Analyst": [
        r"\bbi\s*analyst",
        r"analista\s*(de\s+)?bi\b",
        r"business\s*intelligence\s*analyst",
        r"analista\s*(de\s+)?business\s*intelligence",
        r"analista\s*(de\s+)?intelig[eê]ncia\s*(de\s+)?neg[oó]cios?",
    ],
    "Analytics Engineer": [
        r"analytics\s*engineer",
        r"engenheiro\(?a?\)?\s*(de\s+)?analytics",
        r"pessoa\s+engenheira?\s*(de\s+)?analytics",
    ],
    "Machine Learning Engineer": [
        r"machine\s*learning\s*engineer",
        r"ml\s*engineer",
        r"mle\b",
        r"engenheiro\(?a?\)?\s*(de\s+)?machine\s*learning",
        r"engenheiro\(?a?\)?\s*(de\s+)?ml\b",
        r"mlops\s*engineer",
        r"ai\s*engineer",
        r"engenheiro\(?a?\)?\s*(de\s+)?ia\b",
    ],
    "Data Architect": [
        r"data\s*architect",
        r"arquiteto\(?a?\)?\s*(de\s+)?dados",
        r"pessoa\s+arquiteta?\s*(de\s+)?dados",
    ],
    "Full Stack Developer": [
        r"full[\s-]*stack",
        r"desenvolvedor\(?a?\)?\s*(de\s+)?full[\s-]*stack",
        r"pessoa\s+desenvolvedora?\s*full[\s-]*stack",
        r"dev\s*full[\s-]*stack",
        r"software\s*engineer\s*full[\s-]*stack",
        r"engenheiro\(?a?\)?\s*(de\s+)?software\s*full[\s-]*stack",
    ],
    "Back End Developer": [
        r"back[\s-]*end",
        r"backend",
        r"desenvolvedor\(?a?\)?\s*(de\s+)?back[\s-]*end",
        r"pessoa\s+desenvolvedora?\s*back[\s-]*end",
        r"dev\s*back[\s-]*end",
        r"software\s*engineer\s*back[\s-]*end",
        r"engenheiro\(?a?\)?\s*(de\s+)?software\s*back[\s-]*end",
        r"desenvolvedor\(?a?\)?\s*backend",
    ],
}


def normalize_job_title(title: str) -> str:
    """
    Normaliza o título da vaga para uma categoria padrão.
    
    Args:
        title: Título original da vaga
        
    Returns:
        Categoria normalizada ou "Outro"
    """
    if not title:
        return "Outro"
    
    title_lower = title.lower().strip()
    
    # Tenta match com cada categoria
    for normalized_title, patterns in TITLE_MAPPINGS.items():
        for pattern in patterns:
            if re.search(pattern, title_lower, re.IGNORECASE):
                return normalized_title
    
    return "Outro"


# =============================================================================
# MAPEAMENTOS DE SENIORIDADE
# =============================================================================

SENIORITY_KEYWORDS = {
    "Junior": [
        r"\bjr\.?\b",
        r"\bjunior\b",
        r"\bjúnior\b",
        r"\bentry\s*level\b",
        r"\btrainee\b",
        r"\bestagi[áa]rio\b",
        r"\bi\b(?!\s*-)",  # I sozinho, mas não "I -"
    ],
    "Pleno": [
        r"\bpleno\b",
        r"\bmid[\s-]*level\b",
        r"\bii\b",
        r"\b2\b(?=\s|$)",
    ],
    "Senior": [
        r"\bsr\.?\b",
        r"\bsenior\b",
        r"\bsênior\b",
        r"\biii\b",
        r"\b3\b(?=\s|$)",
        r"\bespecialista\b",
    ],
    "Lead": [
        r"\blead\b",
        r"\blíder\b",
        r"\btech\s*lead\b",
        r"\bteam\s*lead\b",
    ],
    "Staff": [
        r"\bstaff\b",
    ],
    "Principal": [
        r"\bprincipal\b",
        r"\biv\b",
        r"\b4\b(?=\s|$)",
    ],
}


def normalize_seniority(text: str, years_experience: Optional[int] = None) -> str:
    """
    Extrai e normaliza a senioridade a partir do texto ou experiência.
    
    Args:
        text: Texto contendo indicadores de senioridade (título, descrição)
        years_experience: Anos de experiência (para inferência)
        
    Returns:
        Senioridade normalizada ou "Não Informada"
    """
    if text:
        text_lower = text.lower().strip()
        
        # Ordem de prioridade (mais específico primeiro)
        for seniority in ["Principal", "Staff", "Lead", "Senior", "Pleno", "Junior"]:
            patterns = SENIORITY_KEYWORDS[seniority]
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return seniority
    
    # Inferência por anos de experiência
    if years_experience is not None:
        if years_experience <= 2:
            return "Junior"
        elif years_experience <= 5:
            return "Pleno"
        else:
            return "Senior"
    
    return "Não Informada"


# =============================================================================
# MAPEAMENTOS GEOGRÁFICOS
# =============================================================================

# Estados brasileiros com suas siglas
STATE_MAPPINGS = {
    # Siglas já são válidas
    "AC": "AC", "AL": "AL", "AP": "AP", "AM": "AM", "BA": "BA",
    "CE": "CE", "DF": "DF", "ES": "ES", "GO": "GO", "MA": "MA",
    "MT": "MT", "MS": "MS", "MG": "MG", "PA": "PA", "PB": "PB",
    "PR": "PR", "PE": "PE", "PI": "PI", "RJ": "RJ", "RN": "RN",
    "RS": "RS", "RO": "RO", "RR": "RR", "SC": "SC", "SP": "SP",
    "SE": "SE", "TO": "TO",
    
    # Nomes completos
    "acre": "AC",
    "alagoas": "AL",
    "amapá": "AP",
    "amapa": "AP",
    "amazonas": "AM",
    "bahia": "BA",
    "ceará": "CE",
    "ceara": "CE",
    "distrito federal": "DF",
    "espírito santo": "ES",
    "espirito santo": "ES",
    "goiás": "GO",
    "goias": "GO",
    "maranhão": "MA",
    "maranhao": "MA",
    "mato grosso": "MT",
    "mato grosso do sul": "MS",
    "minas gerais": "MG",
    "pará": "PA",
    "para": "PA",
    "paraíba": "PB",
    "paraiba": "PB",
    "paraná": "PR",
    "parana": "PR",
    "pernambuco": "PE",
    "piauí": "PI",
    "piaui": "PI",
    "rio de janeiro": "RJ",
    "rio grande do norte": "RN",
    "rio grande do sul": "RS",
    "rondônia": "RO",
    "rondonia": "RO",
    "roraima": "RR",
    "santa catarina": "SC",
    "são paulo": "SP",
    "sao paulo": "SP",
    "sergipe": "SE",
    "tocantins": "TO",
}

# Regiões por estado
REGION_BY_STATE = {
    # Norte
    "AC": "Norte", "AP": "Norte", "AM": "Norte", "PA": "Norte",
    "RO": "Norte", "RR": "Norte", "TO": "Norte",
    
    # Nordeste
    "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste",
    "PB": "Nordeste", "PE": "Nordeste", "PI": "Nordeste", "RN": "Nordeste",
    "SE": "Nordeste",
    
    # Centro-Oeste
    "DF": "Centro-Oeste", "GO": "Centro-Oeste", "MT": "Centro-Oeste",
    "MS": "Centro-Oeste",
    
    # Sudeste
    "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
    
    # Sul
    "PR": "Sul", "RS": "Sul", "SC": "Sul",
}

# Normalização de nomes de cidades
CITY_NORMALIZATIONS = {
    "sao paulo": "São Paulo",
    "s. paulo": "São Paulo",
    "sp": None,  # SP sozinho é estado, não cidade
    "belo horizonte": "Belo Horizonte",
    "bh": "Belo Horizonte",
    "b. horizonte": "Belo Horizonte",
    "rio de janeiro": "Rio de Janeiro",
    "rj": None,  # RJ sozinho é estado
    "porto alegre": "Porto Alegre",
    "poa": "Porto Alegre",
    "curitiba": "Curitiba",
    "ctba": "Curitiba",
    "florianópolis": "Florianópolis",
    "florianopolis": "Florianópolis",
    "floripa": "Florianópolis",
    "brasília": "Brasília",
    "brasilia": "Brasília",
    "bsb": "Brasília",
    "recife": "Recife",
    "fortaleza": "Fortaleza",
    "salvador": "Salvador",
    "campinas": "Campinas",
}

# Indicadores de trabalho remoto
REMOTE_INDICATORS = [
    r"\bremoto\b",
    r"\bremote\b",
    r"\bhome\s*office\b",
    r"\banywhere\b",
    r"\b100%\s*remoto\b",
    r"\bfully\s*remote\b",
    r"\btrabalho\s*remoto\b",
]


def parse_location_string(location_str: str) -> dict:
    """
    Faz parsing de uma string de localização.
    
    Exemplos de entrada:
    - "São Paulo, SP"
    - "São Paulo - SP"
    - "São Paulo, SP, Brasil"
    - "Remoto"
    
    Returns:
        Dict com cidade, estado, pais, is_remote
    """
    result = {
        "cidade": None,
        "estado": None,
        "pais": "Brasil",
        "regiao": None,
        "is_remote": False,
    }
    
    if not location_str:
        return result
    
    location_str = location_str.strip()
    
    # Verifica se é remoto
    for pattern in REMOTE_INDICATORS:
        if re.search(pattern, location_str, re.IGNORECASE):
            result["is_remote"] = True
            return result
    
    # Normaliza separadores
    # "São Paulo - SP" -> "São Paulo, SP"
    normalized = re.sub(r'\s*[-/]\s*', ', ', location_str)
    
    # Remove "Brasil", "Brazil", "BR" do final
    normalized = re.sub(r',?\s*(brasil|brazil|br)\s*$', '', normalized, flags=re.IGNORECASE)
    
    # Split por vírgula
    parts = [p.strip() for p in normalized.split(',') if p.strip()]
    
    if len(parts) == 0:
        return result
    
    if len(parts) == 1:
        # Pode ser só estado ou só cidade
        part = parts[0].upper()
        if part in STATE_MAPPINGS:
            result["estado"] = STATE_MAPPINGS[part]
        else:
            # Assume que é cidade
            result["cidade"] = parts[0]
    
    elif len(parts) >= 2:
        # Primeiro é cidade, segundo é estado
        cidade_raw = parts[0]
        estado_raw = parts[1].strip().upper()
        
        # Normaliza estado
        if estado_raw in STATE_MAPPINGS:
            result["estado"] = STATE_MAPPINGS[estado_raw]
        elif estado_raw.lower() in STATE_MAPPINGS:
            result["estado"] = STATE_MAPPINGS[estado_raw.lower()]
        
        # Normaliza cidade
        cidade_lower = cidade_raw.lower()
        if cidade_lower in CITY_NORMALIZATIONS:
            result["cidade"] = CITY_NORMALIZATIONS[cidade_lower]
        else:
            # Mantém com capitalização adequada
            result["cidade"] = cidade_raw.title()
    
    # Adiciona região baseada no estado
    if result["estado"] and result["estado"] in REGION_BY_STATE:
        result["regiao"] = REGION_BY_STATE[result["estado"]]
    
    return result


def normalize_location(
    cidade: Optional[str] = None,
    estado: Optional[str] = None,
    pais: Optional[str] = None,
) -> dict:
    """
    Normaliza informações de localização.
    
    Args:
        cidade: Nome da cidade
        estado: Sigla ou nome do estado
        pais: Nome do país
        
    Returns:
        Dict normalizado com cidade, estado, pais, regiao
    """
    result = {
        "cidade": None,
        "estado": None,
        "pais": pais or "Brasil",
        "regiao": None,
    }
    
    # Normaliza estado
    if estado:
        estado_upper = estado.upper().strip()
        estado_lower = estado.lower().strip()
        
        if estado_upper in STATE_MAPPINGS:
            result["estado"] = STATE_MAPPINGS[estado_upper]
        elif estado_lower in STATE_MAPPINGS:
            result["estado"] = STATE_MAPPINGS[estado_lower]
        else:
            result["estado"] = estado_upper if len(estado) == 2 else estado
    
    # Normaliza cidade
    if cidade:
        cidade_lower = cidade.lower().strip()
        if cidade_lower in CITY_NORMALIZATIONS:
            normalized = CITY_NORMALIZATIONS[cidade_lower]
            result["cidade"] = normalized if normalized else cidade.title()
        else:
            result["cidade"] = cidade.title()
    
    # Adiciona região
    if result["estado"] and result["estado"] in REGION_BY_STATE:
        result["regiao"] = REGION_BY_STATE[result["estado"]]
    
    return result


def extract_location_from_text(text: str) -> dict:
    """
    Tenta extrair localização de um texto livre.
    
    Útil para descrições de vagas que mencionam localização inline.
    
    Args:
        text: Texto livre (descrição da vaga, requisitos, etc)
        
    Returns:
        Dict com cidade, estado, pais, regiao, is_remote
    """
    result = {
        "cidade": None,
        "estado": None,
        "pais": "Brasil",
        "regiao": None,
        "is_remote": False,
    }
    
    if not text:
        return result
    
    text_lower = text.lower()
    
    # Verifica se é remoto
    for pattern in REMOTE_INDICATORS:
        if re.search(pattern, text, re.IGNORECASE):
            result["is_remote"] = True
    
    # Padrões comuns de localização - mais restritivos para evitar falsos positivos
    patterns = [
        # "em São Paulo, SP" - cidade com 1-3 palavras antes do estado
        r"(?:em|at|in|localização:?|local:?)\s+([A-Za-zÀ-ú]+(?:\s+[A-Za-zÀ-ú]+){0,2})[,\s]+([A-Z]{2})\b",
        # "São Paulo - SP" - cidade com 1-3 palavras
        r"\b([A-Z][a-zà-ú]+(?:\s+[A-Za-zÀ-ú]+){0,2})\s*[-–]\s*([A-Z]{2})\b",
        # "São Paulo/SP" 
        r"\b([A-Z][a-zà-ú]+(?:\s+[A-Za-zÀ-ú]+){0,2})/([A-Z]{2})\b",
        # "São Paulo, SP" - padrão mais comum
        r"\b([A-Z][a-zà-ú]+(?:\s+[A-Za-zÀ-ú]+){0,2}),\s*([A-Z]{2})\b",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            cidade = match.group(1).strip()
            estado = match.group(2).upper()
            
            if estado in STATE_MAPPINGS:
                result["estado"] = estado
                result["cidade"] = cidade.title()
                result["regiao"] = REGION_BY_STATE.get(estado)
                break
    
    return result
