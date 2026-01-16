"""
Testes para as transformações analíticas.
"""

import duckdb
import pytest

from src.analytics.models import STAR_SCHEMA_DDL


@pytest.fixture
def populated_db():
    """Cria banco com dados de exemplo para testes de transforms."""
    # Usa in-memory database para evitar problemas de arquivo no Windows
    conn = duckdb.connect(":memory:")
    
    # Cria schema
    for statement in STAR_SCHEMA_DDL.split(";"):
        if statement.strip():
            conn.execute(statement)
    
    # Popula dimensões
    conn.execute("""
        INSERT INTO dim_tempo VALUES 
            (1, '2026-01-15', 2026, 1, 1, 3, 4, 'Quinta', false),
            (2, '2026-01-16', 2026, 1, 1, 3, 5, 'Sexta', false)
    """)
    
    conn.execute("""
        INSERT INTO dim_empresa VALUES 
            (1, 'Nubank', 'nubank', 'Fintech', '2026-01-01'),
            (2, 'iFood', 'ifood', 'FoodTech', '2026-01-01'),
            (3, 'Magazine Luiza', 'magazineluiza', 'Varejo', '2026-01-01')
    """)
    
    conn.execute("""
        INSERT INTO dim_localidade VALUES 
            (1, 'São Paulo', 'SP', 'Brasil', 'Sudeste'),
            (2, 'Belo Horizonte', 'MG', 'Brasil', 'Sudeste'),
            (3, NULL, NULL, 'Brasil', NULL)
    """)
    
    # Popula fatos
    conn.execute("""
        INSERT INTO fact_vagas (
            vaga_sk, tempo_sk, empresa_sk, localidade_sk,
            titulo_original, titulo_normalizado, senioridade, modelo_trabalho,
            salario_min, salario_max, skills, data_coleta
        ) VALUES 
            (1, 1, 1, 3, 'Data Engineer Senior', 'Data Engineer', 'Senior', 'Remoto', 
             15000, 25000, ['Python', 'SQL', 'AWS', 'Spark'], NOW()),
            (2, 1, 1, 3, 'Data Scientist Pleno', 'Data Scientist', 'Pleno', 'Remoto',
             12000, 18000, ['Python', 'SQL', 'R', 'TensorFlow'], NOW()),
            (3, 1, 2, 1, 'Engenheiro de Dados', 'Data Engineer', 'Pleno', 'Híbrido',
             10000, 15000, ['Python', 'SQL', 'GCP', 'Airflow'], NOW()),
            (4, 2, 3, 2, 'Analista de Dados Jr', 'Data Analyst', 'Junior', 'Presencial',
             5000, 7000, ['SQL', 'Excel', 'Power BI'], NOW()),
            (5, 2, 2, 1, 'ML Engineer Senior', 'Machine Learning Engineer', 'Senior', 'Remoto',
             20000, 30000, ['Python', 'PyTorch', 'AWS', 'MLOps'], NOW())
    """)
    
    yield conn, ":memory:"
    
    conn.close()


class TestViewVagasPorTitulo:
    """Testes para a view de vagas por título."""

    def test_create_view(self, populated_db):
        """Testa criação da view."""
        conn, _ = populated_db
        
        conn.execute("""
            CREATE OR REPLACE VIEW vw_vagas_por_titulo AS
            SELECT
                titulo_normalizado,
                senioridade,
                COUNT(*) as total_vagas,
                AVG(salario_min) as salario_min_medio,
                AVG(salario_max) as salario_max_medio,
                COUNT(CASE WHEN modelo_trabalho = 'Remoto' THEN 1 END) as vagas_remotas
            FROM fact_vagas
            GROUP BY titulo_normalizado, senioridade
        """)
        
        result = conn.execute("SELECT * FROM vw_vagas_por_titulo").fetchall()
        assert len(result) > 0

    def test_count_by_title(self, populated_db):
        """Testa contagem por título."""
        conn, _ = populated_db
        
        result = conn.execute("""
            SELECT titulo_normalizado, COUNT(*) as cnt
            FROM fact_vagas
            GROUP BY titulo_normalizado
            ORDER BY cnt DESC
        """).fetchall()
        
        # Data Engineer tem 2 vagas
        de_count = next(r[1] for r in result if r[0] == "Data Engineer")
        assert de_count == 2


class TestViewTopSkills:
    """Testes para a view de top skills."""

    def test_skill_frequency(self, populated_db):
        """Testa frequência de skills."""
        conn, _ = populated_db
        
        result = conn.execute("""
            SELECT skill, COUNT(*) as cnt
            FROM fact_vagas, UNNEST(skills) as t(skill)
            GROUP BY skill
            ORDER BY cnt DESC
            LIMIT 5
        """).fetchall()
        
        # Python é a skill mais comum (4 vagas)
        assert result[0][0] == "Python"
        assert result[0][1] == 4
        
        # SQL também aparece em 4 vagas
        sql_count = next(r[1] for r in result if r[0] == "SQL")
        assert sql_count == 4


class TestViewSkillsComPython:
    """Testes para co-ocorrência de skills com Python."""

    def test_cooccurrence(self, populated_db):
        """Testa skills que aparecem junto com Python."""
        conn, _ = populated_db
        
        result = conn.execute("""
            SELECT s2 as skill, COUNT(*) as ocorrencias
            FROM fact_vagas f,
                 UNNEST(f.skills) as t1(s1),
                 UNNEST(f.skills) as t2(s2)
            WHERE s1 = 'Python' AND s2 != 'Python'
            GROUP BY s2
            ORDER BY ocorrencias DESC
        """).fetchall()
        
        # SQL aparece em todas as vagas com Python
        skills = [r[0] for r in result]
        assert "SQL" in skills
        assert "AWS" in skills


class TestViewVagasPorEmpresa:
    """Testes para vagas por empresa."""

    def test_vagas_por_empresa(self, populated_db):
        """Testa contagem de vagas por empresa."""
        conn, _ = populated_db
        
        result = conn.execute("""
            SELECT e.nome, e.setor, COUNT(*) as total
            FROM fact_vagas f
            JOIN dim_empresa e ON f.empresa_sk = e.empresa_sk
            GROUP BY e.nome, e.setor
            ORDER BY total DESC
        """).fetchall()
        
        # Nubank e iFood têm 2 vagas cada
        nubank = next(r for r in result if r[0] == "Nubank")
        assert nubank[2] == 2
        assert nubank[1] == "Fintech"


class TestViewVagasPorRegiao:
    """Testes para distribuição geográfica."""

    def test_vagas_por_regiao(self, populated_db):
        """Testa distribuição por região."""
        conn, _ = populated_db
        
        result = conn.execute("""
            SELECT l.regiao, l.estado, COUNT(*) as total
            FROM fact_vagas f
            JOIN dim_localidade l ON f.localidade_sk = l.localidade_sk
            GROUP BY l.regiao, l.estado
        """).fetchall()
        
        assert len(result) > 0


class TestSalarioAnalysis:
    """Testes para análises de salário."""

    def test_salario_medio_por_senioridade(self, populated_db):
        """Testa média salarial por senioridade."""
        conn, _ = populated_db
        
        result = conn.execute("""
            SELECT senioridade, 
                   AVG(salario_min) as min_medio,
                   AVG(salario_max) as max_medio
            FROM fact_vagas
            WHERE salario_max IS NOT NULL
            GROUP BY senioridade
            ORDER BY max_medio DESC
        """).fetchall()
        
        # Senior deve ter maior salário
        assert result[0][0] == "Senior"

    def test_salario_por_titulo(self, populated_db):
        """Testa salário por título."""
        conn, _ = populated_db
        
        result = conn.execute("""
            SELECT titulo_normalizado, AVG(salario_max) as media
            FROM fact_vagas
            WHERE salario_max IS NOT NULL
            GROUP BY titulo_normalizado
            ORDER BY media DESC
        """).fetchall()
        
        # ML Engineer tem maior média
        assert result[0][0] == "Machine Learning Engineer"
