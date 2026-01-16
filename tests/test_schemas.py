"""
Testes para os schemas Pydantic de validação de vagas.
"""

import pytest
from pydantic import ValidationError

from src.schemas.job import (
    Habilidade,
    Localidade,
    Salario,
    VagaEmprego,
    VagaExtractionResult,
)


class TestSalario:
    """Testes para o schema de Salário."""

    def test_salario_completo(self):
        """Testa criação de salário com todos os campos."""
        salario = Salario(
            valor_minimo=10000.0,
            valor_maximo=15000.0,
            moeda="BRL",
            inclui_bonus=False,
        )
        assert salario.valor_minimo == 10000.0
        assert salario.valor_maximo == 15000.0
        assert salario.moeda == "BRL"
        assert salario.inclui_bonus is False

    def test_salario_apenas_maximo(self):
        """Testa salário com apenas valor máximo."""
        salario = Salario(valor_maximo=20000.0)
        assert salario.valor_minimo is None
        assert salario.valor_maximo == 20000.0
        assert salario.moeda == "BRL"  # default

    def test_salario_moeda_usd(self):
        """Testa salário em dólar."""
        salario = Salario(valor_minimo=5000.0, moeda="USD")
        assert salario.moeda == "USD"

    def test_salario_moeda_invalida(self):
        """Testa que moeda inválida gera erro."""
        with pytest.raises(ValidationError):
            Salario(valor_minimo=10000.0, moeda="INVALID")


class TestLocalidade:
    """Testes para o schema de Localidade."""

    def test_localidade_completa(self):
        """Testa localidade com cidade e estado."""
        loc = Localidade(cidade="São Paulo", estado="SP", pais="Brasil")
        assert loc.cidade == "São Paulo"
        assert loc.estado == "SP"
        assert loc.pais == "Brasil"

    def test_localidade_apenas_pais(self):
        """Testa localidade apenas com país (remoto internacional)."""
        loc = Localidade(pais="Brasil")
        assert loc.cidade is None
        assert loc.estado is None
        assert loc.pais == "Brasil"

    def test_localidade_default_brasil(self):
        """Testa que o país padrão é Brasil."""
        loc = Localidade(cidade="Curitiba", estado="PR")
        assert loc.pais == "Brasil"


class TestVagaEmprego:
    """Testes para o schema principal de Vaga."""

    def test_vaga_minima(self):
        """Testa vaga com apenas campos obrigatórios."""
        vaga = VagaEmprego(
            titulo_original="Data Engineer Senior",
            empresa="TechCorp",
        )
        assert vaga.titulo_original == "Data Engineer Senior"
        assert vaga.empresa == "TechCorp"
        assert vaga.titulo_normalizado == "Outro"  # default
        assert vaga.skills == []

    def test_vaga_completa(self):
        """Testa vaga com todos os campos preenchidos."""
        vaga = VagaEmprego(
            titulo_original="Engenheiro de Dados Sênior",
            titulo_normalizado="Data Engineer",
            senioridade="Senior",
            empresa="Nubank",
            setor_empresa="Fintech",
            localidade=Localidade(cidade="São Paulo", estado="SP"),
            modelo_trabalho="Remoto",
            salario=Salario(valor_minimo=15000, valor_maximo=25000),
            skills=["Python", "SQL", "AWS", "Spark"],
            anos_experiencia_min=5,
            descricao_resumida="Vaga para engenheiro de dados sênior com foco em pipelines.",
            beneficios=["VR", "Plano de Saúde", "PLR"],
            url_origem="https://nubank.com.br/vagas/123",
            plataforma="Greenhouse",
        )
        assert vaga.titulo_normalizado == "Data Engineer"
        assert vaga.senioridade == "Senior"
        assert vaga.modelo_trabalho == "Remoto"
        assert len(vaga.skills) == 4
        assert "Python" in vaga.skills

    def test_vaga_skills_lista_vazia(self):
        """Testa que skills pode ser lista vazia."""
        vaga = VagaEmprego(
            titulo_original="Analista",
            empresa="Empresa X",
            skills=[],
        )
        assert vaga.skills == []

    def test_vaga_modelo_trabalho_valido(self):
        """Testa modelos de trabalho válidos."""
        for modelo in ["Remoto", "Híbrido", "Presencial"]:
            vaga = VagaEmprego(
                titulo_original="Dev",
                empresa="X",
                modelo_trabalho=modelo,
            )
            assert vaga.modelo_trabalho == modelo


class TestVagaExtractionResult:
    """Testes para o resultado da extração."""

    def test_extraction_result_valido(self):
        """Testa resultado de extração válido."""
        result = VagaExtractionResult(
            vaga=VagaEmprego(
                titulo_original="Data Engineer",
                empresa="Nubank",
            ),
            confianca=0.95,
            campos_incertos=["salario"],
        )
        assert result.confianca == 0.95
        assert "salario" in result.campos_incertos

    def test_extraction_confianca_limites(self):
        """Testa que confiança deve estar entre 0 e 1."""
        # Confiança válida
        result = VagaExtractionResult(
            vaga=VagaEmprego(titulo_original="Dev", empresa="X"),
            confianca=0.5,
        )
        assert result.confianca == 0.5

        # Confiança inválida (> 1)
        with pytest.raises(ValidationError):
            VagaExtractionResult(
                vaga=VagaEmprego(titulo_original="Dev", empresa="X"),
                confianca=1.5,
            )

        # Confiança inválida (< 0)
        with pytest.raises(ValidationError):
            VagaExtractionResult(
                vaga=VagaEmprego(titulo_original="Dev", empresa="X"),
                confianca=-0.1,
            )
