"""
Schemas Pydantic para validação e estruturação de dados de vagas.
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class Salario(BaseModel):
    """
    Representa informações salariais normalizadas para base mensal.
    Valores são convertidos automaticamente pelo LLM a partir de formatos como:
    - "R$ 15.000/mês"
    - "100k/ano"
    - "USD 50/hour"
    """

    valor_minimo: float | None = Field(
        default=None,
        description="Valor numérico do salário mínimo mensal. Normalizado para BRL quando possível.",
    )
    valor_maximo: float | None = Field(
        default=None,
        description="Valor numérico do salário máximo mensal. Normalizado para BRL quando possível.",
    )
    moeda: Literal["BRL", "USD", "EUR", "GBP"] = Field(
        default="BRL",
        description="Código ISO da moeda original.",
    )
    inclui_bonus: bool = Field(
        default=False,
        description="True se o valor informado inclui bônus ou variável.",
    )


class Habilidade(BaseModel):
    """
    Representa uma habilidade técnica ou soft skill extraída da vaga.
    """

    nome: str = Field(
        description="Nome normalizado da tecnologia ou habilidade (ex: Python, SQL, AWS).",
    )
    categoria: Literal[
        "linguagem",
        "framework",
        "cloud",
        "database",
        "ferramenta",
        "metodologia",
        "soft_skill",
    ] = Field(
        description="Categoria da habilidade.",
    )
    obrigatoriedade: bool = Field(
        default=True,
        description="True se for requisito obrigatório, False se for desejável.",
    )


class Localidade(BaseModel):
    """
    Representa a localização geográfica da vaga.
    """

    cidade: str | None = Field(default=None, description="Nome da cidade.")
    estado: str | None = Field(default=None, description="Sigla do estado (ex: SP, RJ).")
    pais: str = Field(default="Brasil", description="Nome do país.")


class VagaEmprego(BaseModel):
    """
    Schema principal para uma vaga de emprego estruturada.
    Este schema é usado pelo LLM para extrair informações do HTML bruto.
    """

    # Identificação
    titulo_original: str = Field(
        description="Título original da vaga como aparece no anúncio.",
    )
    titulo_normalizado: str | None = Field(
        default="Outro",
        description="Título normalizado para categorização.",
    )
    senioridade: str | None = Field(
        default=None,
        description="Nível de senioridade inferido do título ou requisitos.",
    )

    # Empresa
    empresa: str = Field(description="Nome da empresa contratante.")
    setor_empresa: str | None = Field(
        default=None, description="Setor de atuação da empresa (ex: Fintech, E-commerce)."
    )

    # Localização
    localidade: Localidade | None = Field(default=None, description="Localização da vaga.")
    modelo_trabalho: str | None = Field(
        default="Presencial",
        description="Modelo de trabalho (Remoto, Hibrido, Presencial).",
    )

    # Remuneração
    salario: Salario | None = Field(
        default=None,
        description="Informações salariais quando disponíveis.",
    )

    # Requisitos
    skills: list[str] = Field(
        default_factory=list,
        description="Lista de habilidades técnicas e soft skills (ex: Python, SQL, Comunicação).",
    )
    anos_experiencia_min: int | None = Field(
        default=None,
        description="Anos mínimos de experiência exigidos.",
    )

    # Conteúdo
    descricao_resumida: str | None = Field(
        default=None,
        description="Resumo de 2-3 frases sobre a vaga e responsabilidades.",
    )
    beneficios: list[str] = Field(
        default_factory=list,
        description="Lista de benefícios mencionados.",
    )

    # Metadados (preenchidos pelo pipeline, não pelo LLM)
    url_origem: str | None = Field(default=None, description="URL original da vaga.")
    plataforma: str | None = Field(
        default=None, description="Plataforma de origem (LinkedIn, Gupy, etc)."
    )
    data_coleta: date | None = Field(default=None, description="Data da coleta.")


class VagaExtractionResult(BaseModel):
    """
    Resultado da extração de uma vaga pelo LLM.
    Inclui a vaga extraída e metadados de confiança.
    """

    vaga: VagaEmprego = Field(description="Dados estruturados da vaga.")
    confianca: float = Field(
        ge=0.0,
        le=1.0,
        description="Score de confiança da extração (0-1).",
    )
    campos_incertos: list[str] = Field(
        default_factory=list,
        description="Lista de campos onde houve incerteza na extração.",
    )
