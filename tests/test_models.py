"""
Testes para os modelos analíticos (Star Schema DuckDB).
"""

import duckdb
import pytest

from src.analytics.models import (
    STAR_SCHEMA_DDL,
    create_star_schema,
    get_or_create_empresa,
    get_or_create_localidade,
)


@pytest.fixture
def temp_db():
    """Cria um banco DuckDB temporário para testes."""
    # Usa in-memory database para evitar problemas de arquivo no Windows
    conn = duckdb.connect(":memory:")
    yield conn, ":memory:"
    conn.close()


class TestStarSchemaCreation:
    """Testes para criação do Star Schema."""

    def test_create_tables(self, temp_db):
        """Testa criação das tabelas do Star Schema."""
        conn, _ = temp_db
        
        # Executa DDL
        for statement in STAR_SCHEMA_DDL.split(";"):
            if statement.strip():
                conn.execute(statement)
        
        # Verifica tabelas criadas
        tables = conn.execute("SHOW TABLES").fetchall()
        table_names = [t[0] for t in tables]
        
        assert "dim_tempo" in table_names
        assert "dim_empresa" in table_names
        assert "dim_localidade" in table_names
        assert "fact_vagas" in table_names

    def test_dim_tempo_columns(self, temp_db):
        """Testa colunas da dimensão tempo."""
        conn, _ = temp_db
        
        for statement in STAR_SCHEMA_DDL.split(";"):
            if statement.strip():
                conn.execute(statement)
        
        # Verifica estrutura
        columns = conn.execute("DESCRIBE dim_tempo").fetchall()
        column_names = [c[0] for c in columns]
        
        assert "tempo_sk" in column_names
        assert "data" in column_names
        assert "ano" in column_names
        assert "mes" in column_names

    def test_fact_vagas_columns(self, temp_db):
        """Testa colunas da tabela fato."""
        conn, _ = temp_db
        
        for statement in STAR_SCHEMA_DDL.split(";"):
            if statement.strip():
                conn.execute(statement)
        
        columns = conn.execute("DESCRIBE fact_vagas").fetchall()
        column_names = [c[0] for c in columns]
        
        assert "vaga_sk" in column_names
        assert "tempo_sk" in column_names
        assert "empresa_sk" in column_names
        assert "titulo_normalizado" in column_names
        assert "skills" in column_names


class TestDimensionInserts:
    """Testes para inserção nas dimensões."""

    def test_insert_empresa(self, temp_db):
        """Testa inserção de empresa."""
        conn, _ = temp_db
        
        for statement in STAR_SCHEMA_DDL.split(";"):
            if statement.strip():
                conn.execute(statement)
        
        # Insere empresa
        conn.execute("""
            INSERT INTO dim_empresa (empresa_sk, nome, nome_normalizado, setor)
            VALUES (1, 'Nubank', 'nubank', 'Fintech')
        """)
        
        # Verifica
        result = conn.execute("SELECT * FROM dim_empresa WHERE empresa_sk = 1").fetchone()
        assert result[1] == "Nubank"
        assert result[3] == "Fintech"

    def test_insert_localidade(self, temp_db):
        """Testa inserção de localidade."""
        conn, _ = temp_db
        
        for statement in STAR_SCHEMA_DDL.split(";"):
            if statement.strip():
                conn.execute(statement)
        
        conn.execute("""
            INSERT INTO dim_localidade (localidade_sk, cidade, estado, pais, regiao)
            VALUES (1, 'São Paulo', 'SP', 'Brasil', 'Sudeste')
        """)
        
        result = conn.execute("SELECT * FROM dim_localidade WHERE localidade_sk = 1").fetchone()
        assert result[1] == "São Paulo"
        assert result[2] == "SP"


class TestSkillsArray:
    """Testes para o campo de skills como array."""

    def test_insert_skills_array(self, temp_db):
        """Testa inserção de skills como array."""
        conn, _ = temp_db
        
        for statement in STAR_SCHEMA_DDL.split(";"):
            if statement.strip():
                conn.execute(statement)
        
        # Insere dependências
        conn.execute("""
            INSERT INTO dim_tempo (tempo_sk, data, ano, trimestre, mes, semana, dia_semana, dia_semana_nome, is_fim_semana)
            VALUES (1, '2026-01-15', 2026, 1, 1, 3, 4, 'Quinta', false)
        """)
        conn.execute("""
            INSERT INTO dim_empresa (empresa_sk, nome, nome_normalizado)
            VALUES (1, 'Test', 'test')
        """)
        conn.execute("""
            INSERT INTO dim_localidade (localidade_sk, pais)
            VALUES (1, 'Brasil')
        """)
        
        # Insere vaga com skills
        conn.execute("""
            INSERT INTO fact_vagas (
                vaga_sk, tempo_sk, empresa_sk, localidade_sk,
                titulo_original, titulo_normalizado, senioridade, modelo_trabalho,
                skills, data_coleta
            )
            VALUES (
                1, 1, 1, 1,
                'Data Engineer', 'Data Engineer', 'Senior', 'Remoto',
                ['Python', 'SQL', 'AWS', 'Spark'], NOW()
            )
        """)
        
        # Verifica skills
        result = conn.execute("SELECT skills FROM fact_vagas WHERE vaga_sk = 1").fetchone()
        skills = result[0]
        assert "Python" in skills
        assert "AWS" in skills
        assert len(skills) == 4

    def test_unnest_skills(self, temp_db):
        """Testa UNNEST de skills para análise."""
        conn, _ = temp_db
        
        for statement in STAR_SCHEMA_DDL.split(";"):
            if statement.strip():
                conn.execute(statement)
        
        # Setup
        conn.execute("""
            INSERT INTO dim_tempo VALUES (1, '2026-01-15', 2026, 1, 1, 3, 4, 'Quinta', false)
        """)
        conn.execute("INSERT INTO dim_empresa VALUES (1, 'Test', 'test', NULL, NULL)")
        conn.execute("INSERT INTO dim_localidade VALUES (1, NULL, NULL, 'Brasil', NULL)")
        
        # Insere 2 vagas
        conn.execute("""
            INSERT INTO fact_vagas (vaga_sk, tempo_sk, empresa_sk, localidade_sk,
                titulo_original, titulo_normalizado, senioridade, modelo_trabalho, skills, data_coleta)
            VALUES 
                (1, 1, 1, 1, 'DE', 'Data Engineer', 'Senior', 'Remoto', ['Python', 'SQL'], NOW()),
                (2, 1, 1, 1, 'DS', 'Data Scientist', 'Pleno', 'Remoto', ['Python', 'R'], NOW())
        """)
        
        # Conta skills
        result = conn.execute("""
            SELECT skill, COUNT(*) as cnt
            FROM fact_vagas, UNNEST(skills) as t(skill)
            GROUP BY skill
            ORDER BY cnt DESC
        """).fetchall()
        
        # Python aparece em 2 vagas
        python_count = next(r[1] for r in result if r[0] == "Python")
        assert python_count == 2
