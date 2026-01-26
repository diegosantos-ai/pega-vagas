"""
Modelo dimensional Star Schema para análise de vagas.

Implementa as tabelas:
- fact_vagas: Tabela fato com métricas de vagas
- dim_empresa: Dimensão de empresas
- dim_localidade: Dimensão geográfica
- dim_tempo: Dimensão temporal
"""

from datetime import date, datetime
from pathlib import Path

import duckdb
import structlog

logger = structlog.get_logger()

# DDL para criação do Star Schema
STAR_SCHEMA_DDL = """
-- ============================================
-- Dimensão Tempo
-- ============================================
CREATE TABLE IF NOT EXISTS dim_tempo (
    tempo_sk INTEGER PRIMARY KEY,
    data DATE NOT NULL,
    ano INTEGER NOT NULL,
    trimestre INTEGER NOT NULL,
    mes INTEGER NOT NULL,
    semana INTEGER NOT NULL,
    dia_semana INTEGER NOT NULL,
    dia_semana_nome VARCHAR NOT NULL,
    is_fim_semana BOOLEAN NOT NULL
);

-- ============================================
-- Dimensão Empresa
-- ============================================
CREATE TABLE IF NOT EXISTS dim_empresa (
    empresa_sk INTEGER PRIMARY KEY,
    nome VARCHAR NOT NULL,
    nome_normalizado VARCHAR NOT NULL,
    setor VARCHAR,
    primeiro_registro DATE,
    UNIQUE(nome_normalizado)
);

-- ============================================
-- Dimensão Localidade
-- ============================================
CREATE TABLE IF NOT EXISTS dim_localidade (
    localidade_sk INTEGER PRIMARY KEY,
    cidade VARCHAR,
    estado VARCHAR,
    pais VARCHAR NOT NULL DEFAULT 'Brasil',
    regiao VARCHAR,
    UNIQUE(cidade, estado, pais)
);

-- ============================================
-- Tabela Fato de Vagas
-- ============================================
CREATE TABLE IF NOT EXISTS fact_vagas (
    vaga_sk INTEGER PRIMARY KEY,
    
    -- Chaves estrangeiras
    tempo_sk INTEGER REFERENCES dim_tempo(tempo_sk),
    empresa_sk INTEGER REFERENCES dim_empresa(empresa_sk),
    localidade_sk INTEGER REFERENCES dim_localidade(localidade_sk),
    
    -- Atributos degenerados (não precisam de dimensão)
    titulo_original VARCHAR NOT NULL,
    titulo_normalizado VARCHAR NOT NULL,
    senioridade VARCHAR NOT NULL,
    modelo_trabalho VARCHAR NOT NULL,
    plataforma VARCHAR,
    url_origem VARCHAR,
    
    -- Métricas de salário
    salario_min DECIMAL(12,2),
    salario_max DECIMAL(12,2),
    salario_moeda VARCHAR DEFAULT 'BRL',
    
    -- Skills armazenadas como array de strings
    skills VARCHAR[],
    
    -- Metadados
    anos_experiencia_min INTEGER,
    descricao_resumida VARCHAR,
    beneficios VARCHAR[],
    
    -- Auditoria
    data_coleta TIMESTAMP NOT NULL,
    confianca_extracao DECIMAL(3,2)
);

-- ============================================
-- Índices para performance
-- ============================================
CREATE INDEX IF NOT EXISTS idx_fact_titulo ON fact_vagas(titulo_normalizado);
CREATE INDEX IF NOT EXISTS idx_fact_senioridade ON fact_vagas(senioridade);
CREATE INDEX IF NOT EXISTS idx_fact_tempo ON fact_vagas(tempo_sk);
CREATE INDEX IF NOT EXISTS idx_fact_empresa ON fact_vagas(empresa_sk);
"""


def create_star_schema(db_path: str = "data/gold/vagas.duckdb") -> duckdb.DuckDBPyConnection:
    """
    Cria ou conecta ao banco DuckDB com o Star Schema.

    Args:
        db_path: Caminho para o arquivo DuckDB

    Returns:
        Conexão DuckDB
    """
    # Garante que o diretório existe
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = duckdb.connect(db_path)
    conn.execute(STAR_SCHEMA_DDL)

    logger.info("Star Schema criado/verificado", db_path=db_path)
    return conn


def populate_dim_tempo(conn: duckdb.DuckDBPyConnection, start_date: date, end_date: date) -> None:
    """
    Popula a dimensão tempo com datas no intervalo especificado.

    Args:
        conn: Conexão DuckDB
        start_date: Data inicial
        end_date: Data final
    """
    conn.execute(
        """
        INSERT OR IGNORE INTO dim_tempo
        SELECT
            CAST(strftime(d, '%Y%m%d') AS INTEGER) as tempo_sk,
            d as data,
            EXTRACT(YEAR FROM d) as ano,
            EXTRACT(QUARTER FROM d) as trimestre,
            EXTRACT(MONTH FROM d) as mes,
            EXTRACT(WEEK FROM d) as semana,
            EXTRACT(DOW FROM d) as dia_semana,
            CASE EXTRACT(DOW FROM d)
                WHEN 0 THEN 'Domingo'
                WHEN 1 THEN 'Segunda'
                WHEN 2 THEN 'Terça'
                WHEN 3 THEN 'Quarta'
                WHEN 4 THEN 'Quinta'
                WHEN 5 THEN 'Sexta'
                WHEN 6 THEN 'Sábado'
            END as dia_semana_nome,
            EXTRACT(DOW FROM d) IN (0, 6) as is_fim_semana
        FROM generate_series(?, ?, INTERVAL 1 DAY) as t(d)
    """,
        [start_date, end_date],
    )

    logger.debug("dim_tempo populada", start=start_date, end=end_date)


def get_or_create_empresa(
    conn: duckdb.DuckDBPyConnection,
    nome: str,
    setor: str | None = None,
) -> int:
    """
    Obtém ou cria uma empresa na dimensão, retornando a surrogate key.
    """
    nome_normalizado = nome.strip().lower()

    # Tenta encontrar existente
    result = conn.execute(
        "SELECT empresa_sk FROM dim_empresa WHERE nome_normalizado = ?", [nome_normalizado]
    ).fetchone()

    if result:
        return result[0]

    # Cria novo
    result = conn.execute("SELECT COALESCE(MAX(empresa_sk), 0) + 1 FROM dim_empresa").fetchone()
    new_sk = result[0]

    conn.execute(
        """
        INSERT INTO dim_empresa (empresa_sk, nome, nome_normalizado, setor, primeiro_registro)
        VALUES (?, ?, ?, ?, CURRENT_DATE)
    """,
        [new_sk, nome.strip(), nome_normalizado, setor],
    )

    return new_sk


def get_or_create_localidade(
    conn: duckdb.DuckDBPyConnection,
    cidade: str | None,
    estado: str | None,
    pais: str = "Brasil",
) -> int:
    """
    Obtém ou cria uma localidade na dimensão, retornando a surrogate key.
    """
    # Tenta encontrar existente
    result = conn.execute(
        """
        SELECT localidade_sk FROM dim_localidade
        WHERE cidade IS NOT DISTINCT FROM ? AND estado IS NOT DISTINCT FROM ? AND pais = ?
    """,
        [cidade, estado, pais],
    ).fetchone()

    if result:
        return result[0]

    # Determina região
    regiao = _get_regiao_brasil(estado) if pais == "Brasil" else None

    # Cria novo
    result = conn.execute(
        "SELECT COALESCE(MAX(localidade_sk), 0) + 1 FROM dim_localidade"
    ).fetchone()
    new_sk = result[0]

    conn.execute(
        """
        INSERT INTO dim_localidade (localidade_sk, cidade, estado, pais, regiao)
        VALUES (?, ?, ?, ?, ?)
    """,
        [new_sk, cidade, estado, pais, regiao],
    )

    return new_sk


def _get_regiao_brasil(estado: str | None) -> str | None:
    """Retorna a região do Brasil baseado na sigla do estado."""
    if not estado:
        return None

    regioes = {
        "Norte": ["AC", "AP", "AM", "PA", "RO", "RR", "TO"],
        "Nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
        "Centro-Oeste": ["DF", "GO", "MT", "MS"],
        "Sudeste": ["ES", "MG", "RJ", "SP"],
        "Sul": ["PR", "RS", "SC"],
    }

    estado_upper = estado.upper().strip()
    for regiao, estados in regioes.items():
        if estado_upper in estados:
            return regiao
    return None


def load_to_gold(
    conn: duckdb.DuckDBPyConnection,
    vagas: list[dict],
) -> int:
    """
    Carrega vagas processadas na tabela fato.

    Args:
        conn: Conexão DuckDB
        vagas: Lista de dicts com dados de vagas (formato VagaExtractionResult)

    Returns:
        Número de linhas inseridas
    """
    inserted = 0

    for vaga_data in vagas:
        try:
            vaga = vaga_data.get("vaga", vaga_data)
            confianca = vaga_data.get("confianca", 1.0)

            # Resolve surrogate keys
            empresa_sk = get_or_create_empresa(conn, vaga["empresa"], vaga.get("setor_empresa"))

            loc = vaga.get("localidade") or {}
            localidade_sk = get_or_create_localidade(
                conn, loc.get("cidade"), loc.get("estado"), loc.get("pais", "Brasil")
            )

            # Tempo SK baseado na data de coleta
            raw_data_coleta = vaga.get("data_coleta")
            if isinstance(raw_data_coleta, (date, datetime)):
                data_coleta = raw_data_coleta
            else:
                # Se for None ou string
                data_coleta = datetime.fromisoformat(
                    str(raw_data_coleta) if raw_data_coleta else datetime.now().isoformat()
                )

            # Ensure it's a datetime for consistency if needed, or just use it
            # But the code below uses strftime, which works on date too
            tempo_sk = int(data_coleta.strftime("%Y%m%d"))

            # Garante que a data existe na dimensão tempo
            populate_dim_tempo(conn, data_coleta.date(), data_coleta.date())

            # Extrai salário
            salario = vaga.get("salario") or {}

            # Próximo SK para vaga
            result = conn.execute("SELECT COALESCE(MAX(vaga_sk), 0) + 1 FROM fact_vagas").fetchone()
            vaga_sk = result[0]

            # Insere na fact
            conn.execute(
                """
                INSERT INTO fact_vagas (
                    vaga_sk, tempo_sk, empresa_sk, localidade_sk,
                    titulo_original, titulo_normalizado, senioridade, modelo_trabalho,
                    plataforma, url_origem,
                    salario_min, salario_max, salario_moeda,
                    skills, anos_experiencia_min, descricao_resumida, beneficios,
                    data_coleta, confianca_extracao
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                [
                    vaga_sk,
                    tempo_sk,
                    empresa_sk,
                    localidade_sk,
                    vaga.get("titulo_original", ""),
                    vaga.get("titulo_normalizado", "Outro"),
                    vaga.get("senioridade", "Pleno"),
                    vaga.get("modelo_trabalho", "Presencial"),
                    vaga.get("plataforma"),
                    vaga.get("url_origem"),
                    salario.get("valor_minimo"),
                    salario.get("valor_maximo"),
                    salario.get("moeda", "BRL"),
                    vaga.get("skills", []),
                    vaga.get("anos_experiencia_min"),
                    vaga.get("descricao_resumida", ""),
                    vaga.get("beneficios", []),
                    data_coleta,
                    confianca,
                ],
            )

            inserted += 1

        except Exception as e:
            logger.warning(f"Erro ao inserir vaga: {e}")
            continue

    logger.info(f"Carregadas {inserted} vagas na camada Gold")
    return inserted
