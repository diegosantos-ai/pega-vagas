"""
QualityGate v2 - Sistema de Scoring Refatorado
Filtra vagas antes da notificação com regras configuráveis e pontuação.
Foco: Data Engineer, Automação, IA e Análise de Dados - 100% REMOTO
"""

import logging
import re

from pydantic import BaseModel, Field

logger = logging.getLogger("QualityGate_v2")


class JobScore(BaseModel):
    """Modelo de saída da avaliação de qualidade."""

    is_valid: bool
    score: int = Field(ge=0, le=100)
    rejection_reason: str | None = None
    flags: list[str] = []
    details: dict = {}


class QualityGateV2:
    """
    Sistema de scoring para vagas com regras configuráveis.

    Regras principais:
    1. REMOTO é obrigatório (regra de ouro)
    2. Deve estar no Brasil ou ser totalmente remoto
    3. Score mínimo configurável (padrão: 50)
    """

    def __init__(
        self,
        target_roles: list[str] = None,
        min_score_threshold: int = 50,
        strict_remote: bool = True,
    ):
        """
        Args:
            target_roles: Lista de títulos/roles alvo
            min_score_threshold: Pontuação mínima para aprovação (0-100)
            strict_remote: Se True, rejeita qualquer menção de híbrido/presencial
        """
        self.min_score_threshold = min_score_threshold
        self.strict_remote = strict_remote

        # Padrões de detecção de REMOTO (positivos)
        self.REMOTE_POSITIVE = [
            r"\b100%?\s*remoto\b",
            r"\bfully\s*remote\b",
            r"\bfull\s*remote\b",
            r"\bremote\s*first\b",
            r"\btrabalho\s*remoto\b",
            r"\bhome\s*office\b",
            r"\banywhere\s*in\s*brazil\b",
            r"\banywhere\s*in\s*brasil\b",
            r"\bremoto\b(?!.*\b(h[íi]brido|presencial|escrit[óo]rio)\b)",
            r"\bwork\s*from\s*anywhere\b",
            r"\bwork\s*from\s*home\b",
        ]

        # Padrões de REJEIÇÃO (negativos - NUNCA devem passar)
        self.REMOTE_NEGATIVE = [
            r"\bh[íi]brido\b",
            r"\bhybrid\b",
            r"\bpresencial\b",
            r"\bon[\s-]?site\b",
            r"\boffice\s*based\b",
            r"\b\d+\s*(dias?|days?)\s*(no\s*)?(escrit[óo]rio|office)\b",
            r"\bresidir\s*em\b",
            r"\bmust\s*live\s*in\b",
            r"\brequires\s*relocation\b",
            r"\bwork\s*from\s*office\b",
        ]

        # Títulos alvo (Data Engineer, Automação, IA)
        self.target_roles = target_roles or [
            # Data Engineer
            "engenheiro de dados",
            "data engineer",
            "analytics engineer",
            "engenheiro de analytics",
            "arquiteto de dados",
            "data architect",
            "data platform",
            # Automação
            "automation engineer",
            "engenheiro de automação",
            "rpa developer",
            "desenvolvedor rpa",
            # IA / ML
            "ai engineer",
            "engenheiro de ia",
            "machine learning engineer",
            "engenheiro de machine learning",
            "ml engineer",
            # Análise de Dados
            "data analyst",
            "analista de dados",
            "business intelligence",
            "bi analyst",
            # Ciência de Dados
            "data scientist",
            "cientista de dados",
        ]

        # Stack tecnológico esperado (pontos por menção)
        self.tech_stack_points = {
            # Core Data
            "python": 10,
            "sql": 8,
            "spark": 12,
            "airflow": 15,
            "dbt": 10,
            "kafka": 10,
            "databricks": 12,
            # Cloud
            "aws": 8,
            "gcp": 8,
            "azure": 8,
            # IA/ML
            "tensorflow": 12,
            "pytorch": 12,
            "scikit-learn": 10,
            "hugging face": 10,
            "llm": 10,
            "machine learning": 10,
            # Automação
            "rpa": 12,
            "automation": 8,
            "orchestration": 8,
            # Ferramentas
            "docker": 5,
            "kubernetes": 5,
            "git": 3,
            "ci/cd": 8,
        }

    def _check_remote_status(self, description: str, title: str) -> tuple[bool, list[str]]:
        """
        Verifica se a vaga é realmente 100% remota.
        Retorna (is_remote, flags)

        REGRA DE OURO: Se mencionar híbrido/presencial, REJEITA SEMPRE.
        """
        text_blob = (title + " " + description).lower()
        flags = []

        # 1. VERIFICAÇÃO CRÍTICA: Red Flags (Negativos)
        for pattern in self.REMOTE_NEGATIVE:
            if re.search(pattern, text_blob):
                flags.append("HYBRID_OR_PRESENTIAL_DETECTED")
                return False, flags

        # 2. Verifica Green Flags (Positivos)
        has_positive = False
        for pattern in self.REMOTE_POSITIVE:
            if re.search(pattern, text_blob):
                has_positive = True
                flags.append("EXPLICIT_REMOTE_MENTION")
                break

        if not has_positive:
            # Se não menciona explicitamente remoto, é suspeito
            # Mas não rejeita automaticamente (pode estar nos metadados)
            flags.append("NO_EXPLICIT_REMOTE_MENTION")

        return True, flags

    def _check_location(self, description: str, title: str) -> tuple[bool, list[str]]:
        """
        Verifica se a vaga é para Brasil ou totalmente remoto.
        Retorna (is_valid, flags)
        """
        text_blob = (title + " " + description).lower()
        flags = []

        # Locais que indicam Brasil
        brazil_positive = [
            r"\bbrasil\b",
            r"\bbrasileiro\b",
            r"\bbrazil\b",
            r"\bbrazilian\b",
            r"\bsão paulo\b",
            r"\brio de janeiro\b",
            r"\bbelo horizonte\b",
            r"\bcuritiba\b",
            r"\brecife\b",
        ]

        # Locais que indicam fora do Brasil
        brazil_negative = [
            r"\busa\b",
            r"\bunited states\b",
            r"\beuropa\b",
            r"\beurope\b",
            r"\bportugal\b",
            r"\blisboa\b",
            r"\bmadrid\b",
            r"\bbarcelona\b",
            r"\bsingapura\b",
            r"\bsingapore\b",
            r"\btóquio\b",
            r"\btokyo\b",
            r"\brelocation\b",
            r"\brelocate\b",
        ]

        # Verifica negativos (rejeita)
        for pattern in brazil_negative:
            if re.search(pattern, text_blob):
                flags.append("INTERNATIONAL_LOCATION")
                return False, flags

        # Se menciona Brasil explicitamente, aprova
        for pattern in brazil_positive:
            if re.search(pattern, text_blob):
                flags.append("BRAZIL_LOCATION_CONFIRMED")
                return True, flags

        # Se é 100% remoto e não menciona local específico, aprova
        flags.append("REMOTE_NO_LOCATION_RESTRICTION")
        return True, flags

    def _calculate_title_score(self, title: str) -> tuple[int, list[str]]:
        """
        Calcula pontuação baseada no título.
        Retorna (score, flags)
        """
        score = 0
        flags = []
        title_lower = title.lower()

        # Verifica match com target roles
        for role in self.target_roles:
            if role in title_lower:
                score += 40
                flags.append(f"ROLE_MATCH:{role}")
                break

        # Bônus para senioridade
        seniority_bonus = {
            "senior": 10,
            "lead": 15,
            "staff": 15,
            "principal": 15,
            "head": 15,
            "manager": 10,
            "coordenador": 8,
        }

        for term, bonus in seniority_bonus.items():
            if term in title_lower:
                score += bonus
                flags.append(f"SENIORITY:{term}")
                break

        # Penalidade para júnior/estágio
        junior_penalty = {
            "estágio": -20,
            "intern": -20,
            "junior": -10,
            "jr.": -10,
            "jr ": -10,
            "trainee": -15,
        }

        for term, penalty in junior_penalty.items():
            if term in title_lower:
                score += penalty
                flags.append(f"JUNIOR_PENALTY:{term}")
                break

        return max(0, min(score, 50)), flags

    def _calculate_tech_score(self, description: str, title: str) -> tuple[int, list[str]]:
        """
        Calcula pontuação baseada em stack tecnológico.
        Retorna (score, flags)
        """
        score = 0
        flags = []
        text_blob = (title + " " + description).lower()

        found_techs = []
        for tech, points in self.tech_stack_points.items():
            if tech in text_blob:
                score += points
                found_techs.append(tech)

        if found_techs:
            flags.append(f"TECH_STACK:{','.join(found_techs[:5])}")

        # Máximo 50 pontos por stack
        return min(score, 50), flags

    def _calculate_relevance_score(self, title: str, description: str) -> tuple[int, list[str]]:
        """
        Calcula score de relevância geral.
        Retorna (score, flags)
        """
        score = 0
        flags = []

        # Score de título
        title_score, title_flags = self._calculate_title_score(title)
        score += title_score
        flags.extend(title_flags)

        # Score de tech stack
        tech_score, tech_flags = self._calculate_tech_score(description, title)
        score += tech_score
        flags.extend(tech_flags)

        return min(score, 100), flags

    def evaluate(self, job_data: dict) -> JobScore:
        """
        Função principal de avaliação.

        job_data esperado:
        {
            "url": "...",
            "title": "...",
            "description": "...",
            "company": "...",
            "location": "..."
        }
        """
        details = {}
        flags = []

        # Extrai dados
        title = job_data.get("title", "").strip()
        description = job_data.get("description", "").strip()
        url = job_data.get("url", "")

        if not title or not description:
            return JobScore(
                is_valid=False,
                score=0,
                rejection_reason="MISSING_REQUIRED_FIELDS",
                flags=["NO_TITLE_OR_DESCRIPTION"],
            )

        # =====================================================================
        # REGRA DE OURO #1: REMOTO É OBRIGATÓRIO
        # =====================================================================
        is_remote, remote_flags = self._check_remote_status(description, title)
        flags.extend(remote_flags)
        details["remote_check"] = is_remote

        if not is_remote:
            return JobScore(
                is_valid=False,
                score=0,
                rejection_reason="NOT_TRULY_REMOTE",
                flags=flags,
                details=details,
            )

        # =====================================================================
        # REGRA #2: LOCALIZAÇÃO (Brasil ou totalmente remoto)
        # =====================================================================
        is_valid_location, location_flags = self._check_location(description, title)
        flags.extend(location_flags)
        details["location_check"] = is_valid_location

        if not is_valid_location:
            return JobScore(
                is_valid=False,
                score=0,
                rejection_reason="INVALID_LOCATION",
                flags=flags,
                details=details,
            )

        # =====================================================================
        # REGRA #3: SCORE DE RELEVÂNCIA
        # =====================================================================
        relevance_score, relevance_flags = self._calculate_relevance_score(title, description)
        flags.extend(relevance_flags)
        details["relevance_score"] = relevance_score

        if relevance_score < self.min_score_threshold:
            return JobScore(
                is_valid=False,
                score=relevance_score,
                rejection_reason=f"LOW_RELEVANCE (score: {relevance_score} < {self.min_score_threshold})",
                flags=flags,
                details=details,
            )

        # =====================================================================
        # APROVAÇÃO
        # =====================================================================
        return JobScore(
            is_valid=True,
            score=relevance_score,
            flags=flags,
            details=details,
        )


# Teste rápido
if __name__ == "__main__":
    gate = QualityGateV2(min_score_threshold=50)

    # Teste 1: Vaga ruim (híbrida)
    bad_job_1 = {
        "title": "Analista de Suporte Júnior",
        "description": "Venha trabalhar no nosso escritório incrível. Modelo híbrido, 3x na semana.",
        "url": "https://example.com/job1",
    }

    # Teste 2: Vaga boa (Data Engineer remoto)
    good_job = {
        "title": "Senior Data Engineer",
        "description": "Atuar 100% remoto em projetos de IA e automação. Stack: Python, Spark, Airflow, AWS. Contratação CLT Brasil.",
        "url": "https://example.com/job2",
    }

    # Teste 3: Vaga de Automação
    automation_job = {
        "title": "Automation Engineer",
        "description": "Fully remote position. Work on RPA and automation projects. Experience with Python and UiPath required. Based in Brazil.",
        "url": "https://example.com/job3",
    }

    print("=" * 60)
    print("TESTE 1: Vaga Híbrida (deve rejeitar)")
    result1 = gate.evaluate(bad_job_1)
    print(f"Válida: {result1.is_valid}, Score: {result1.score}")
    print(f"Razão: {result1.rejection_reason}")
    print(f"Flags: {result1.flags}")

    print("\n" + "=" * 60)
    print("TESTE 2: Data Engineer Sênior Remoto (deve aprovar)")
    result2 = gate.evaluate(good_job)
    print(f"Válida: {result2.is_valid}, Score: {result2.score}")
    print(f"Flags: {result2.flags}")

    print("\n" + "=" * 60)
    print("TESTE 3: Automation Engineer Remoto (deve aprovar)")
    result3 = gate.evaluate(automation_job)
    print(f"Válida: {result3.is_valid}, Score: {result3.score}")
    print(f"Flags: {result3.flags}")
