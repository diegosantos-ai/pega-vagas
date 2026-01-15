"""
Extrator de dados estruturados via LLM.

Usa Gemini ou GPT para extrair informações de vagas a partir de HTML,
retornando dados validados pelo schema Pydantic.
"""

import json
import os
from abc import ABC, abstractmethod
from typing import Optional

import structlog
from dotenv import load_dotenv
from pydantic import ValidationError

from src.processing.html_cleaner import clean_html
from src.schemas.job import VagaEmprego, VagaExtractionResult

load_dotenv()
logger = structlog.get_logger()


# Prompt de sistema para extração de vagas
SYSTEM_PROMPT = """Você é um especialista em extração de dados de vagas de emprego.
Sua tarefa é analisar o HTML/texto de uma vaga e extrair informações estruturadas.

REGRAS IMPORTANTES:
1. NUNCA invente informações. Se não encontrar um dado, use null.

2. TÍTULO NORMALIZADO - Use EXATAMENTE uma dessas categorias:
   - "Data Engineer" (Engenheiro de Dados)
   - "Data Analyst" (Analista de Dados)
   - "Data Scientist" (Cientista de Dados)
   - "Analytics Engineer" (Engenheiro de Analytics)
   - "Machine Learning Engineer" (Engenheiro de ML)
   - "BI Analyst" (Analista de BI)
   - "Data Architect" (Arquiteto de Dados)
   - "Outro" (se não se encaixar em nenhuma acima)

3. SENIORIDADE - Infira baseado em:
   - Palavras-chave: "Jr", "Junior", "Pleno", "Senior", "Lead", "Staff", "Principal"
   - Anos de experiência: 0-2 = Junior, 2-5 = Pleno, 5+ = Senior
   - Use: "Junior", "Pleno", "Senior", "Lead", "Staff" ou "Não Informada"

4. MODELO DE TRABALHO - Identifique corretamente:
   - "Remoto" = trabalho 100% remoto, home office, remote, anywhere
   - "Híbrido" = híbrido, presencial parcial, alguns dias no escritório
   - "Presencial" = presencial, on-site, no escritório
   - ATENÇÃO: Se mencionar "remoto" ou "100% remoto", use "Remoto"

5. Para salários:
   - Converta tudo para base MENSAL
   - Se em USD, mantenha USD (não converta para BRL)
   - Separe salário base de bônus quando possível

6. Para skills, retorne uma LISTA PLANA de strings (ex: ["Python", "SQL", "AWS"]).

7. Para beneficios, retorne uma lista de strings. Se vazio, retorne [].

IMPORTANTE: Retorne APENAS o JSON válido, sem texto adicional."""


def get_json_schema() -> dict:
    """Retorna o JSON Schema do modelo VagaEmprego para o LLM."""
    return VagaExtractionResult.model_json_schema()


class BaseLLMClient(ABC):
    """Interface abstrata para clientes LLM."""

    @abstractmethod
    async def extract(self, html_content: str) -> dict:
        """Extrai dados estruturados do HTML."""
        pass


class GeminiClient(BaseLLMClient):
    """Cliente para Google Gemini API (novo SDK google-genai)."""

    def __init__(self, model: str = "gemini-2.0-flash"):
        from google import genai
        from google.genai import types

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY não configurada")

        self.client = genai.Client(api_key=api_key)
        self.model_name = model
        self.types = types
        logger.info("Gemini client inicializado (novo SDK)", model=model)

    async def extract(self, html_content: str) -> dict:
        """Extrai dados usando Gemini (novo SDK)."""
        prompt = f"""{SYSTEM_PROMPT}

Analise esta vaga de emprego e extraia os dados estruturados:

---
{html_content}
---

Retorne um JSON com os campos: vaga (VagaEmprego), confianca (float 0-1), campos_incertos (lista)."""

        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=self.types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        return json.loads(response.text)


class OpenAIClient(BaseLLMClient):
    """Cliente para OpenAI API."""

    def __init__(self, model: str = "gpt-4o-mini"):
        from openai import AsyncOpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY não configurada")

        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        logger.info("OpenAI client inicializado", model=model)

    async def extract(self, html_content: str) -> dict:
        """Extrai dados usando OpenAI."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Analise esta vaga e extraia os dados:\n\n{html_content}",
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.1,  # Baixa temperatura para consistência
        )
        return json.loads(response.choices[0].message.content)


class LLMExtractor:
    """
    Orquestra a extração de dados de vagas via LLM.

    Exemplo de uso:
        extractor = LLMExtractor()
        result = await extractor.extract_from_html(html_content)
        print(result.vaga.titulo_normalizado)
    """

    def __init__(
        self,
        provider: str = "gemini",
        model: Optional[str] = None,
        max_retries: int = 3,
    ):
        """
        Args:
            provider: "gemini" ou "openai"
            model: Nome do modelo (usa default se None)
            max_retries: Tentativas em caso de falha de validação
        """
        self.max_retries = max_retries

        # Escolhe cliente baseado no provider
        if provider == "gemini":
            self.client = GeminiClient(model=model or "gemini-2.0-flash")
        elif provider == "openai":
            self.client = OpenAIClient(model=model or "gpt-4o-mini")
        else:
            raise ValueError(f"Provider desconhecido: {provider}")

        logger.info("LLMExtractor inicializado", provider=provider)

    async def extract_from_html(
        self,
        html_content: str,
        url: Optional[str] = None,
        platform: Optional[str] = None,
        title_hint: Optional[str] = None,
        company_hint: Optional[str] = None,
    ) -> VagaExtractionResult:
        """
        Extrai dados estruturados de uma vaga a partir do HTML.

        Args:
            html_content: HTML bruto da página
            url: URL de origem (para metadados)
            platform: Plataforma de origem (para metadados)

        Returns:
            VagaExtractionResult com dados validados
        """
        # 1. Limpa HTML (remove scripts, estilos, etc.)
        cleaned_text = clean_html(html_content)
        logger.debug("HTML limpo", chars_original=len(html_content), chars_limpo=len(cleaned_text))

        # 2. Extrai via LLM com retry
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                raw_result = await self.client.extract(cleaned_text)

                # Heurística de correção: se o JSON for a vaga direta (sem wrapper)
                if "vaga" not in raw_result and "titulo" in raw_result:
                    raw_result = {
                        "vaga": raw_result,
                        "confianca": 0.8,
                        "campos_incertos": []
                    }
                
                # Normalização de campos
                vaga_dict = raw_result.get("vaga", raw_result)
                
                # Mapeia titulo -> titulo_original
                if "titulo" in vaga_dict and "titulo_original" not in vaga_dict:
                    vaga_dict["titulo_original"] = vaga_dict.pop("titulo")
                
                # Garante titulo_normalizado
                if "titulo_normalizado" not in vaga_dict:
                     vaga_dict["titulo_normalizado"] = "Outro"
                     
                # Garante empresa (se não vier no JSON, o hint lá embaixo preenche, mas precisa passar na validação se for obrigatório)
                if "empresa" not in vaga_dict:
                    vaga_dict["empresa"] = "Empresa Confidencial" # Placeholder, será substituído pelo hint
                
                # Garante senioridade
                if "senioridade" not in vaga_dict or vaga_dict["senioridade"] is None:
                    vaga_dict["senioridade"] = "Não Informada"
                
                # Normaliza modelo_de_trabalho -> modelo_trabalho
                if "modelo_de_trabalho" in vaga_dict and "modelo_trabalho" not in vaga_dict:
                    vaga_dict["modelo_trabalho"] = vaga_dict.pop("modelo_de_trabalho")
                
                # Normaliza salario_base -> salario
                if "salario_base" in vaga_dict and "salario" not in vaga_dict:
                    vaga_dict["salario"] = vaga_dict.pop("salario_base")
                
                # Atualiza raw_result se foi modificado via referência ou atribuição
                if "vaga" in raw_result:
                    raw_result["vaga"] = vaga_dict
                else:
                    raw_result = {"vaga": vaga_dict, "confianca": 0.8, "campos_incertos": []}    

                # 3. Valida com Pydantic
                result = VagaExtractionResult.model_validate(raw_result)

                # 4. Adiciona metadados
                if url:
                    result.vaga.url_origem = url
                if platform:
                    result.vaga.plataforma = platform
                if title_hint and not result.vaga.titulo_original:
                     result.vaga.titulo_original = title_hint
                if company_hint and not result.vaga.empresa:
                     result.vaga.empresa = company_hint

                logger.info(
                    "Extração bem-sucedida",
                    titulo=result.vaga.titulo_normalizado,
                    confianca=result.confianca,
                )
                return result

            except ValidationError as e:
                last_error = e
                logger.warning(
                    f"Validação falhou (tentativa {attempt}/{self.max_retries})",
                    errors=str(e),
                )
                # Poderia adicionar feedback ao prompt aqui (retry with feedback)

            except Exception as e:
                last_error = e
                logger.error(f"Erro na extração: {e}")

        # Todas as tentativas falharam
        raise ExtractionError(f"Falha após {self.max_retries} tentativas: {last_error}")


class ExtractionError(Exception):
    """Erro durante extração via LLM."""

    pass


def load_extractor_from_env() -> LLMExtractor:
    """Carrega extractor baseado nas variáveis de ambiente."""
    model = os.getenv("LLM_MODEL", "gemini-2.0-flash")

    if "gemini" in model.lower():
        provider = "gemini"
    elif "gpt" in model.lower():
        provider = "openai"
    else:
        provider = "gemini"  # Default

    return LLMExtractor(provider=provider, model=model)
