"""
Transformações e agregações analíticas sobre o Star Schema.

Queries pré-definidas para análises comuns de mercado de trabalho.
"""

from pathlib import Path

import duckdb
import structlog

logger = structlog.get_logger()


def run_transforms(db_path: str = "data/gold/vagas.duckdb") -> None:
    """
    Executa transformações e cria views analíticas.

    Args:
        db_path: Caminho para o banco DuckDB
    """
    conn = duckdb.connect(db_path)

    # View: Resumo de vagas por título e senioridade
    conn.execute("""
        CREATE OR REPLACE VIEW vw_vagas_por_titulo AS
        SELECT
            titulo_normalizado,
            senioridade,
            COUNT(*) as total_vagas,
            AVG(salario_min) as salario_min_medio,
            AVG(salario_max) as salario_max_medio,
            COUNT(CASE WHEN modelo_trabalho = 'Remoto' THEN 1 END) as vagas_remotas,
            ROUND(
                100.0 * COUNT(CASE WHEN modelo_trabalho = 'Remoto' THEN 1 END) / COUNT(*), 1
            ) as pct_remoto
        FROM fact_vagas
        GROUP BY titulo_normalizado, senioridade
        ORDER BY total_vagas DESC
    """)

    # View: Skills mais demandadas
    conn.execute("""
        CREATE OR REPLACE VIEW vw_top_skills AS
        SELECT
            skill as skill_nome,
            'Geral' as skill_categoria,
            COUNT(*) as ocorrencias,
            ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM fact_vagas), 1) as pct_vagas
        FROM fact_vagas, UNNEST(skills) as t(skill)
        GROUP BY skill
        ORDER BY ocorrencias DESC
    """)

    # View: Co-ocorrência de skills com Python
    conn.execute("""
        CREATE OR REPLACE VIEW vw_skills_com_python AS
        SELECT
            s2 as skill,
            COUNT(*) as ocorrencias
        FROM fact_vagas f,
             UNNEST(f.skills) as t1(s1),
             UNNEST(f.skills) as t2(s2)
        WHERE s1 = 'Python' AND s2 != 'Python'
        GROUP BY s2
        ORDER BY ocorrencias DESC
        LIMIT 20
    """)

    # View: Vagas por empresa
    conn.execute("""
        CREATE OR REPLACE VIEW vw_vagas_por_empresa AS
        SELECT
            e.nome as empresa,
            e.setor,
            COUNT(*) as total_vagas,
            AVG(f.salario_max) as salario_max_medio,
            COUNT(DISTINCT f.titulo_normalizado) as cargos_diferentes
        FROM fact_vagas f
        JOIN dim_empresa e ON f.empresa_sk = e.empresa_sk
        GROUP BY e.nome, e.setor
        ORDER BY total_vagas DESC
    """)

    # View: Evolução temporal
    conn.execute("""
        CREATE OR REPLACE VIEW vw_evolucao_temporal AS
        SELECT
            t.ano,
            t.mes,
            t.semana,
            COUNT(*) as vagas_coletadas,
            AVG(f.salario_max) as salario_medio
        FROM fact_vagas f
        JOIN dim_tempo t ON f.tempo_sk = t.tempo_sk
        GROUP BY t.ano, t.mes, t.semana
        ORDER BY t.ano, t.mes, t.semana
    """)

    # View: Distribuição geográfica
    conn.execute("""
        CREATE OR REPLACE VIEW vw_vagas_por_regiao AS
        SELECT
            l.regiao,
            l.estado,
            l.cidade,
            COUNT(*) as total_vagas,
            AVG(f.salario_max) as salario_medio,
            ROUND(
                100.0 * COUNT(CASE WHEN f.modelo_trabalho = 'Remoto' THEN 1 END) / COUNT(*), 1
            ) as pct_remoto
        FROM fact_vagas f
        JOIN dim_localidade l ON f.localidade_sk = l.localidade_sk
        WHERE l.pais = 'Brasil'
        GROUP BY l.regiao, l.estado, l.cidade
        ORDER BY total_vagas DESC
    """)

    conn.close()
    logger.info("Views analíticas criadas/atualizadas")


def export_to_parquet(
    db_path: str = "data/gold/vagas.duckdb",
    output_dir: str = "data/gold/parquet",
) -> list[str]:
    """
    Exporta tabelas e views para arquivos Parquet.

    Args:
        db_path: Caminho para o banco DuckDB
        output_dir: Diretório de saída para os arquivos Parquet

    Returns:
        Lista de arquivos exportados
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    conn = duckdb.connect(db_path)

    # Lista de tabelas/views para exportar
    exports = [
        "fact_vagas",
        "dim_empresa",
        "dim_localidade",
        "dim_tempo",
        "vw_vagas_por_titulo",
        "vw_top_skills",
        "vw_vagas_por_empresa",
        "vw_vagas_por_regiao",
    ]

    exported_files = []

    for table_name in exports:
        try:
            output_file = output_path / f"{table_name}.parquet"
            conn.execute(f"COPY {table_name} TO '{output_file}' (FORMAT PARQUET)")
            exported_files.append(str(output_file))
            logger.debug(f"Exportado: {table_name}")
        except Exception as e:
            logger.warning(f"Falha ao exportar {table_name}: {e}")

    conn.close()
    logger.info(f"Exportados {len(exported_files)} arquivos Parquet")
    return exported_files


def query_top_skills(
    db_path: str = "data/gold/vagas.duckdb",
    limit: int = 20,
    categoria: str | None = None,
) -> list[dict]:
    """
    Retorna as skills mais demandadas.

    Args:
        db_path: Caminho para o banco DuckDB
        limit: Número máximo de resultados
        categoria: Filtrar por categoria (linguagem, framework, cloud, etc.)

    Returns:
        Lista de dicts com nome, categoria, ocorrencias
    """
    conn = duckdb.connect(db_path, read_only=True)

    query = """
        SELECT skill_nome, skill_categoria, ocorrencias, pct_vagas
        FROM vw_top_skills
    """

    if categoria:
        query += f" WHERE skill_categoria = '{categoria}'"

    query += f" LIMIT {limit}"

    result = conn.execute(query).fetchall()
    conn.close()

    return [
        {
            "nome": row[0],
            "categoria": row[1],
            "ocorrencias": row[2],
            "pct_vagas": row[3],
        }
        for row in result
    ]


def query_salary_by_title(
    db_path: str = "data/gold/vagas.duckdb",
) -> list[dict]:
    """
    Retorna estatísticas salariais por título e senioridade.

    Returns:
        Lista de dicts com titulo, senioridade, salario_medio, total_vagas
    """
    conn = duckdb.connect(db_path, read_only=True)

    result = conn.execute("""
        SELECT
            titulo_normalizado,
            senioridade,
            total_vagas,
            salario_min_medio,
            salario_max_medio,
            pct_remoto
        FROM vw_vagas_por_titulo
        ORDER BY titulo_normalizado, 
            CASE senioridade 
                WHEN 'Estagio' THEN 1
                WHEN 'Junior' THEN 2
                WHEN 'Pleno' THEN 3
                WHEN 'Senior' THEN 4
                WHEN 'Lead' THEN 5
                WHEN 'Staff' THEN 6
                WHEN 'Principal' THEN 7
            END
    """).fetchall()

    conn.close()

    return [
        {
            "titulo": row[0],
            "senioridade": row[1],
            "total_vagas": row[2],
            "salario_min_medio": row[3],
            "salario_max_medio": row[4],
            "pct_remoto": row[5],
        }
        for row in result
    ]
