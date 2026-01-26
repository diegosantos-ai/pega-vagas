"""
Carregador de configuração centralizado.
Lê config.yaml e fornece acesso tipado aos parâmetros.
"""

from pathlib import Path
from typing import Any

import structlog
import yaml

logger = structlog.get_logger()


class ConfigLoader:
    """Gerencia configuração centralizada do projeto."""

    _instance = None
    _config: dict[str, Any] = {}

    def __new__(cls):
        """Singleton pattern para garantir uma única instância."""
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """Carrega config.yaml do diretório raiz do projeto."""
        config_path = Path(__file__).parent.parent.parent / "config.yaml"

        if not config_path.exists():
            logger.warning(f"config.yaml não encontrado em {config_path}")
            logger.info("Usando configuração padrão")
            self._config = self._get_default_config()
            return

        try:
            with open(config_path, encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
            logger.info(f"Configuração carregada de {config_path}")
        except Exception as e:
            logger.error(f"Erro ao carregar config.yaml: {e}")
            self._config = self._get_default_config()

    @staticmethod
    def _get_default_config() -> dict[str, Any]:
        """Retorna configuração padrão."""
        return {
            "search_terms": {
                "data_engineer": ["Data Engineer", "Engenheiro de Dados"],
                "automation": ["Automation Engineer", "Engenheiro de Automação"],
                "ai_ml": ["AI Engineer", "Machine Learning Engineer"],
                "data_analyst": ["Data Analyst", "Analista de Dados"],
                "data_scientist": ["Data Scientist", "Cientista de Dados"],
            },
            "quality_gate": {
                "min_score_threshold": 50,
                "strict_remote": True,
            },
            "schedule": {
                "frequency_hours": 3,
                "timezone": "America/Sao_Paulo",
            },
            "scraping": {
                "max_jobs_per_run": 100,
                "max_jobs_per_company": 50,
            },
            "telegram": {
                "message_format": "detailed",
                "send_summary_only": True,
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtém valor de configuração por chave (suporta notação de ponto).

        Exemplos:
            config.get("quality_gate.min_score_threshold")
            config.get("schedule.frequency_hours")
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value if value is not None else default

    def get_search_terms(self) -> list[str]:
        """Retorna lista plana de todos os termos de busca."""
        search_terms = self.get("search_terms", {})
        all_terms = []

        for category, terms in search_terms.items():
            if isinstance(terms, list):
                all_terms.extend(terms)

        return all_terms

    def get_remote_patterns(self) -> tuple[list[str], list[str]]:
        """Retorna padrões de remoto (positivos, negativos)."""
        qg = self.get("quality_gate", {})
        positive = qg.get("remote_positive_patterns", [])
        negative = qg.get("remote_negative_patterns", [])
        return positive, negative

    def get_brazil_patterns(self) -> tuple[list[str], list[str]]:
        """Retorna padrões de localização Brasil (positivos, negativos)."""
        qg = self.get("quality_gate", {})
        positive = qg.get("brazil_positive_patterns", [])
        negative = qg.get("brazil_negative_patterns", [])
        return positive, negative

    def get_tech_stack(self) -> dict[str, int]:
        """Retorna dicionário de stack tecnológico com pontos."""
        qg = self.get("quality_gate", {})
        return qg.get("tech_stack_points", {})

    def get_min_score_threshold(self) -> int:
        """Retorna pontuação mínima para aprovação."""
        return self.get("quality_gate.min_score_threshold", 50)

    def get_frequency_hours(self) -> int:
        """Retorna frequência de execução em horas."""
        return self.get("schedule.frequency_hours", 3)

    def get_max_jobs(self) -> int:
        """Retorna máximo de vagas por execução."""
        return self.get("scraping.max_jobs_per_run", 100)

    def get_platforms(self) -> list[str]:
        """Retorna plataformas a executar."""
        return self.get("scraping.platforms", ["api"])

    def get_llm_model(self) -> str:
        """Retorna modelo LLM a usar."""
        return self.get("llm.model", "gemini-2.0-flash")

    def get_telegram_config(self) -> dict[str, Any]:
        """Retorna configuração do Telegram."""
        return self.get("telegram", {})

    def is_dry_run(self) -> bool:
        """Retorna se está em modo dry-run."""
        return self.get("experimental.dry_run", False)

    def __repr__(self):
        return f"<ConfigLoader loaded={bool(self._config)}>"


# Singleton global
config = ConfigLoader()


if __name__ == "__main__":
    # Teste
    cfg = ConfigLoader()
    print("Search Terms:", cfg.get_search_terms()[:3])
    print("Min Score:", cfg.get_min_score_threshold())
    print("Frequency:", cfg.get_frequency_hours())
    print("Platforms:", cfg.get_platforms())
