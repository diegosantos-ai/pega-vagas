import logging
import re

import requests
from pydantic import BaseModel, Field

# Configuração de Logger
logger = logging.getLogger("QualityGate")

class JobScore(BaseModel):
    """Modelo de saída da avaliação de qualidade."""
    is_valid: bool
    score: int = Field(ge=0, le=100)
    rejection_reason: str | None = None
    flags: list[str] = []

class QualityGate:
    """
    Filtra vagas antes da notificação.
    Regras baseadas no arquivo 'agents.md'.
    """

    def __init__(self, target_roles: list[str] = None, check_links: bool = False):
        """
        Args:
            target_roles: Lista de títulos de vagas alvo
            check_links: Se True, verifica se o link da vaga está ativo (lento, pode dar falsos positivos)
        """
        # Flag para verificação de links (desabilitada por padrão)
        self.check_links = check_links
        
        # Definições trazidas do seu agents.md
        self.REMOTE_POSITIVE = [
            r"\b100%?\s*remoto\b", r"\bfully\s*remote\b", r"\bfull\s*remote\b",
            r"\bremote\s*first\b", r"\btrabalho\s*remoto\b", r"\bhome\s*office\b",
            r"\banywhere\b", r"\bremoto\b(?!.*\b(h[íi]brido|presencial|escrit[óo]rio)\b)",
        ]
        
        self.REMOTE_NEGATIVE = [
            r"\bh[íi]brido\b", r"\bhybrid\b", r"\bpresencial\b", r"\bon[\s-]?site\b",
            r"\boffice\s*based\b", r"\b\d+\s*(dias?|days?)\s*(no\s*)?(escrit[óo]rio|office)\b",
            r"\bresidir\s*em\b", r"\bmust\s*live\s*in\b"
        ]

        # Seus alvos de transição de carreira
        self.target_roles = target_roles or [
            "engenheiro de dados", "data engineer", "analytics engineer", 
            "arquiteto de dados", "data platform", "ai engineer"
        ]

    def _check_link_alive(self, url: str) -> bool:
        """
        Verifica se o link ainda existe (Head Request).
        Evita enviar 404 para o Telegram.
        """
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/91.0.4472.124 Safari/537.36"
                )
            }
            # Timeout curto para não travar o pipeline
            response = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
            
            # Gupy e outros ATS costumam redirecionar para página de login ou home quando a vaga fecha
            if response.status_code >= 400:
                return False
            
            # Verificação extra: se a URL final mudou drasticamente (ex: redirecionou para home)
            # Isso requer logica customizada por ATS, mas o status code já ajuda 80%
            return True
        except Exception as e:
            logger.warning(f"Erro ao verificar link {url}: {e}")
            return False # Na dúvida, assume quebrado ou instável

    def _analyze_remote_status(self, description: str, title: str) -> tuple[bool, list[str]]:
        """
        Aplica Regex para validar se é realmente remoto.
        Retorna (is_remote, flags)
        """
        text_blob = (title + " " + description).lower()
        flags = []
        
        # 1. Verifica Red Flags (Negativos)
        for pattern in self.REMOTE_NEGATIVE:
            if re.search(pattern, text_blob):
                # Exceção: Às vezes dizem "Não é híbrido" - mas regex simples falha nisso.
                # Assumimos conservadorismo: se fala híbrido, tá fora.
                return False, ["DETECTED_HYBRID_OR_PRESENTIAL"]

        # 2. Verifica Green Flags (Positivos)
        has_positive = False
        for pattern in self.REMOTE_POSITIVE:
            if re.search(pattern, text_blob):
                has_positive = True
                break
        
        if not has_positive:
            # Se não diz explicitamente que é remoto, marcamos como suspeito
            flags.append("NO_EXPLICIT_REMOTE_MENTION")
            # Não reprova automaticamente pois pode estar nos metadados, mas penaliza
        
        return True, flags

    def _calculate_relevance_score(self, title: str, description: str) -> int:
        """
        Calcula quão alinhada a vaga está com o objetivo (Engenharia de Dados/IA).
        """
        score = 0
        text_blob = (title + " " + description).lower()
        
        # Peso alto para Título (Title match é rei)
        title_lower = title.lower()
        if any(role in title_lower for role in self.target_roles):
            score += 50
        elif "dados" in title_lower or "data" in title_lower:
            score += 20 # Genérico, mas ok
        
        # Peso para Stack Tecnológica (mencionado no README/Projeto)
        tech_stack = ["python", "sql", "spark", "airflow", "aws", "databricks", "dbt", "kafka"]
        found_techs = sum(1 for tech in tech_stack if tech in text_blob)
        score += min(found_techs * 5, 30) # Máximo 30 pontos por stack
        
        # Penalidades (Júnior ou Estágio se você quer manter renda)
        if any(term in title_lower for term in ["estágio", "intern", "junior", "jr.", "jr "]):
            score -= 20 # Você tem experiência de gestão, Jr pode não pagar o que você quer
        
        # Bônus para Senioridade/Gestão (seu background)
        seniority_terms = ["senior", "lead", "staff", "principal", "head", "manager", "coord"]
        if any(term in title_lower for term in seniority_terms):
            score += 10

        return max(0, min(score, 100))

    def evaluate(self, job_data: dict) -> JobScore:
        """
        Função principal chamada pelo pipeline.
        
        Esperado job_data:
        {
            "url": "...",
            "title": "...",
            "description": "...",
            "company": "...",
            "original_location": "..."
        }
        """
        
        # 1. Check de Link (Rápido)
        if self.check_links and not self._check_link_alive(job_data.get("url", "")):
            return JobScore(is_valid=False, score=0, rejection_reason="BROKEN_LINK")

        description = job_data.get("description", "")
        title = job_data.get("title", "")
        
        # 2. Check de Remoto (Regra de Ouro)
        is_remote_candidate, remote_flags = self._analyze_remote_status(description, title)
        
        if not is_remote_candidate:
             return JobScore(
                 is_valid=False, 
                 score=0, 
                 rejection_reason="NOT_TRULY_REMOTE", 
                 flags=remote_flags
             )

        # 3. Check de Brasil (Regra do agents.md)
        # Se a descrição tiver "work permit required for USA" ou "Lisbon", descarta.
        invalid_locations = [
            "portugal", "lisbon", "lisboa", "madrid", "barcelona", "miami", "relocation"
        ]
        if any(loc in description.lower() for loc in invalid_locations):
             return JobScore(
                 is_valid=False, 
                 score=0, 
                 rejection_reason="INTERNATIONAL_RELOCATION"
             )

        # 4. Score de Relevância
        relevance = self._calculate_relevance_score(title, description)
        
        # Defina seu limiar de corte. Ex: 40.
        if relevance < 40:
            return JobScore(
                is_valid=False, 
                score=relevance, 
                rejection_reason="LOW_RELEVANCE",
                flags=remote_flags
            )

        return JobScore(is_valid=True, score=relevance, flags=remote_flags)

# Exemplo de uso simulado (pode rodar este arquivo diretamente para testar)
if __name__ == "__main__":
    gate = QualityGate()
    
    # Caso 1: Vaga Lixo
    bad_job = {
        "url": "https://gupy.io/vaga-que-nao-existe", # Assuma que falha ou é híbrida
        "title": "Analista de Suporte Júnior",
        "description": (
            "Venha trabalhar no nosso escritório incrível. "
            "Modelo híbrido, 3x na semana."
        )
    }
    
    # Caso 2: Vaga Ouro
    good_job = {
        "url": "https://google.com", # Link que funciona só pra teste
        "title": "Senior Data Engineer",
        "description": "Atuar 100% remoto em projetos de IA. Stack: Python, Spark, AWS. Contratação CLT Brasil."
    }
    
    print(f"Avaliação Bad Job: {gate.evaluate(bad_job)}")
    print(f"Avaliação Good Job: {gate.evaluate(good_job)}")