"""
Testes para normalização de títulos e localidades.
"""

import pytest

from src.processing.normalizers import (
    normalize_job_title,
    normalize_seniority,
    normalize_location,
    parse_location_string,
    TITLE_MAPPINGS,
    SENIORITY_KEYWORDS,
)


class TestNormalizeJobTitle:
    """Testes para normalização de títulos de vagas."""

    # Data Engineer
    @pytest.mark.parametrize("title,expected", [
        ("Data Engineer", "Data Engineer"),
        ("Engenheiro de Dados", "Data Engineer"),
        ("Engenheiro(a) de Dados", "Data Engineer"),
        ("Data Engineer Senior", "Data Engineer"),
        ("Engenheiro de Dados Sênior", "Data Engineer"),
        ("Sr. Data Engineer", "Data Engineer"),
        ("Data Engineer III", "Data Engineer"),
        ("Pessoa Engenheira de Dados", "Data Engineer"),
        ("Data Engineer - Remote", "Data Engineer"),
        ("Engenheiro(a) de Dados Pleno", "Data Engineer"),
    ])
    def test_data_engineer_variations(self, title, expected):
        assert normalize_job_title(title) == expected

    # Data Scientist
    @pytest.mark.parametrize("title,expected", [
        ("Data Scientist", "Data Scientist"),
        ("Cientista de Dados", "Data Scientist"),
        ("Data Scientist Senior", "Data Scientist"),
        ("Cientista de Dados Pleno", "Data Scientist"),
        ("Sr Data Scientist", "Data Scientist"),
        ("Pessoa Cientista de Dados", "Data Scientist"),
    ])
    def test_data_scientist_variations(self, title, expected):
        assert normalize_job_title(title) == expected

    # Data Analyst
    @pytest.mark.parametrize("title,expected", [
        ("Data Analyst", "Data Analyst"),
        ("Analista de Dados", "Data Analyst"),
        ("Analista de Dados Jr", "Data Analyst"),
        ("Data Analyst Pleno", "Data Analyst"),
        ("Pessoa Analista de Dados", "Data Analyst"),
    ])
    def test_data_analyst_variations(self, title, expected):
        assert normalize_job_title(title) == expected

    # BI Analyst
    @pytest.mark.parametrize("title,expected", [
        ("BI Analyst", "BI Analyst"),
        ("Analista de BI", "BI Analyst"),
        ("Business Intelligence Analyst", "BI Analyst"),
        ("Analista de Business Intelligence", "BI Analyst"),
    ])
    def test_bi_analyst_variations(self, title, expected):
        assert normalize_job_title(title) == expected

    # Analytics Engineer
    @pytest.mark.parametrize("title,expected", [
        ("Analytics Engineer", "Analytics Engineer"),
        ("Engenheiro de Analytics", "Analytics Engineer"),
        ("Engenheiro(a) de Analytics", "Analytics Engineer"),
    ])
    def test_analytics_engineer_variations(self, title, expected):
        assert normalize_job_title(title) == expected

    # ML Engineer
    @pytest.mark.parametrize("title,expected", [
        ("Machine Learning Engineer", "Machine Learning Engineer"),
        ("ML Engineer", "Machine Learning Engineer"),
        ("Engenheiro de Machine Learning", "Machine Learning Engineer"),
        ("MLE Senior", "Machine Learning Engineer"),
        ("MLOps Engineer", "Machine Learning Engineer"),
    ])
    def test_ml_engineer_variations(self, title, expected):
        assert normalize_job_title(title) == expected

    # Data Architect
    @pytest.mark.parametrize("title,expected", [
        ("Data Architect", "Data Architect"),
        ("Arquiteto de Dados", "Data Architect"),
        ("Arquiteto(a) de Dados", "Data Architect"),
    ])
    def test_data_architect_variations(self, title, expected):
        assert normalize_job_title(title) == expected

    # Casos que devem retornar "Outro"
    @pytest.mark.parametrize("title", [
        "Software Engineer",
        "Backend Developer",
        "Product Manager",
        "DevOps Engineer",
        "QA Engineer",
        "Gerente de Projetos",
    ])
    def test_non_data_roles(self, title):
        assert normalize_job_title(title) == "Outro"


class TestNormalizeSeniority:
    """Testes para normalização de senioridade."""

    @pytest.mark.parametrize("text,expected", [
        # Junior
        ("Data Engineer Jr", "Junior"),
        ("Analista Junior", "Junior"),
        ("Júnior", "Junior"),
        ("Jr.", "Junior"),
        ("Entry Level", "Junior"),
        ("Trainee", "Junior"),
        ("Estagiário", "Junior"),
        
        # Pleno
        ("Data Engineer Pleno", "Pleno"),
        ("Analista Pleno", "Pleno"),
        ("Mid-level", "Pleno"),
        ("II", "Pleno"),
        
        # Senior
        ("Senior Data Engineer", "Senior"),
        ("Sênior", "Senior"),
        ("Sr.", "Senior"),
        ("III", "Senior"),
        ("Especialista", "Senior"),
        
        # Lead
        ("Lead Data Engineer", "Lead"),
        ("Tech Lead", "Lead"),
        ("Líder Técnico", "Lead"),
        
        # Staff/Principal
        ("Staff Engineer", "Staff"),
        ("Principal Engineer", "Principal"),
    ])
    def test_seniority_extraction(self, text, expected):
        assert normalize_seniority(text) == expected

    def test_seniority_from_experience(self):
        """Testa inferência de senioridade por anos de experiência."""
        assert normalize_seniority("", years_experience=1) == "Junior"
        assert normalize_seniority("", years_experience=3) == "Pleno"
        assert normalize_seniority("", years_experience=6) == "Senior"

    def test_unknown_seniority(self):
        """Testa senioridade não identificável."""
        assert normalize_seniority("Data Engineer") == "Não Informada"
        assert normalize_seniority("Analista de Dados") == "Não Informada"


class TestParseLocationString:
    """Testes para parsing de string de localização."""

    @pytest.mark.parametrize("location_str,expected_city,expected_state", [
        ("São Paulo, SP", "São Paulo", "SP"),
        ("São Paulo - SP", "São Paulo", "SP"),
        ("São Paulo/SP", "São Paulo", "SP"),
        ("São Paulo, SP, Brasil", "São Paulo", "SP"),
        ("Belo Horizonte, MG", "Belo Horizonte", "MG"),
        ("Rio de Janeiro - RJ", "Rio de Janeiro", "RJ"),
        ("Curitiba, PR, Brazil", "Curitiba", "PR"),
        ("Florianópolis / SC", "Florianópolis", "SC"),
    ])
    def test_city_state_parsing(self, location_str, expected_city, expected_state):
        result = parse_location_string(location_str)
        assert result["cidade"] == expected_city
        assert result["estado"] == expected_state

    @pytest.mark.parametrize("location_str", [
        "Remoto",
        "Remote",
        "100% Remoto",
        "Anywhere",
        "Home Office",
    ])
    def test_remote_locations(self, location_str):
        """Localizações remotas devem retornar cidade=None."""
        result = parse_location_string(location_str)
        assert result["cidade"] is None
        assert result["is_remote"] is True

    def test_state_only(self):
        """Testa quando só o estado é informado."""
        result = parse_location_string("SP")
        assert result["estado"] == "SP"
        assert result["cidade"] is None

    def test_brazil_variations(self):
        """Testa variações do nome do Brasil."""
        for loc in ["São Paulo, SP, Brasil", "São Paulo, SP, Brazil", "São Paulo, SP, BR"]:
            result = parse_location_string(loc)
            assert result["pais"] == "Brasil"


class TestNormalizeLocation:
    """Testes para normalização completa de localização."""

    def test_normalize_with_full_info(self):
        """Testa normalização com informações completas."""
        result = normalize_location("São Paulo", "SP", "Brasil")
        assert result["cidade"] == "São Paulo"
        assert result["estado"] == "SP"
        assert result["pais"] == "Brasil"
        assert result["regiao"] == "Sudeste"

    def test_region_mapping(self):
        """Testa mapeamento de regiões."""
        # Sudeste
        assert normalize_location(estado="SP")["regiao"] == "Sudeste"
        assert normalize_location(estado="RJ")["regiao"] == "Sudeste"
        assert normalize_location(estado="MG")["regiao"] == "Sudeste"
        
        # Sul
        assert normalize_location(estado="RS")["regiao"] == "Sul"
        assert normalize_location(estado="SC")["regiao"] == "Sul"
        assert normalize_location(estado="PR")["regiao"] == "Sul"
        
        # Nordeste
        assert normalize_location(estado="BA")["regiao"] == "Nordeste"
        assert normalize_location(estado="PE")["regiao"] == "Nordeste"
        
        # Norte
        assert normalize_location(estado="AM")["regiao"] == "Norte"
        
        # Centro-Oeste
        assert normalize_location(estado="DF")["regiao"] == "Centro-Oeste"
        assert normalize_location(estado="GO")["regiao"] == "Centro-Oeste"

    def test_city_name_normalization(self):
        """Testa normalização de nomes de cidades."""
        # Variações de São Paulo
        assert normalize_location("Sao Paulo")["cidade"] == "São Paulo"
        assert normalize_location("S. Paulo")["cidade"] == "São Paulo"
        
        # Variações de Belo Horizonte
        assert normalize_location("BH")["cidade"] == "Belo Horizonte"
        assert normalize_location("B. Horizonte")["cidade"] == "Belo Horizonte"

    def test_state_name_to_abbrev(self):
        """Testa conversão de nome do estado para sigla."""
        assert normalize_location(estado="São Paulo")["estado"] == "SP"
        assert normalize_location(estado="Minas Gerais")["estado"] == "MG"
        assert normalize_location(estado="Rio Grande do Sul")["estado"] == "RS"
