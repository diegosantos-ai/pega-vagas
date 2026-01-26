"""
CLI principal do pipeline Pega-Vagas (Refatorado v2).

Mudança principal: Foco em BUSCA por palavra-chave (Search-First),
removendo a dependência de listas fixas de empresas.

Uso:
    python -m src.pipeline bronze --query "Data Engineer" --max-jobs 100
    python -m src.pipeline silver
    python -m src.pipeline gold
    python -m src.pipeline run
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

import structlog

from src.quality_gate_v2 import QualityGateV2  # Usando V2 por padrão
from src.config.config_loader import config

# Configuração de logging estruturado
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(colors=True),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()



from datetime import datetime, timedelta

async def run_bronze(query: str, max_jobs: int, platform: str = "all") -> list[str]:
    """
    Executa camada Bronze (scraping via busca).
    
    Args:
        query: Termo de busca (ex: "Data Engineer")
        max_jobs: Limite de vagas
        platform: IGNORADO na v3 (sempre roda 'all' scrapers configurados)
    """
    logger.info("Iniciando camada Bronze (Search Mode v3)", query=query, max_jobs=max_jobs)

    saved_files = []
    queries = [q.strip() for q in query.split(",")]
    
    # 1. Gestão de Estado (Date Logic)
    last_run_file = Path("data/.last_run.json")
    since_date = None
    
    if last_run_file.exists():
        try:
            with open(last_run_file, "r") as f:
                data = json.load(f)
                last_ts = data.get("last_run_at")
                if last_ts:
                    since_date = datetime.fromisoformat(last_ts)
                    logger.info(f"Última execução em: {since_date}. Buscando vagas novas...")
        except Exception as e:
            logger.warning(f"Erro lendo .last_run.json: {e}")
            
    if not since_date:
        # Default: 72 horas atrás
        since_date = datetime.now() - timedelta(hours=72)
        logger.info(f"Primeira execução (ou estado perdido). Buscando desde: {since_date} (72h)")

    # 2. Executa Scrapers (One-Shot)
    try:
        from src.ingestion.scrapers.api_scrapers import run_search_scrapers
        
        logger.info("Executando Scrapers de Busca (One-Shot)...")
        files = await run_search_scrapers(queries=queries, max_jobs=max_jobs, since_date=since_date)
        saved_files.extend(files)
        
        # 3. Atualiza Estado se houve sucesso
        with open(last_run_file, "w") as f:
            json.dump({
                "last_run_at": datetime.now().isoformat(),
                "files_count": len(saved_files)
            }, f)
            
    except Exception as e:
        logger.error(f"Erro nos Scrapers: {e}")

    logger.info(f"Bronze finalizada: {len(saved_files)} total de arquivos salvos")
    return saved_files


async def run_silver() -> int:
    """Executa camada Silver (processamento LLM). Mantido compatível."""
    logger.info("Iniciando camada Silver")

    from src.processing import LLMExtractor

    bronze_dir = Path("data/bronze")
    silver_dir = Path("data/silver")
    silver_dir.mkdir(parents=True, exist_ok=True)

    if not bronze_dir.exists():
        logger.warning("Diretório bronze não encontrado")
        return 0

    extractor = LLMExtractor()
    processed = 0

    # Processa recursivamente (suporta subpastas gupy, linkedin, etc)
    for json_file in bronze_dir.rglob("*.json"):
        # Pula arquivos de controle/logs se houver
        if json_file.name.startswith("."): 
            continue

        try:
            # Verifica se já foi processado recentemente (otimização simples)
            out_file = silver_dir / f"{json_file.stem}_processed.json"
            if out_file.exists():
                # Poderíamos checar timestamp, mas por enquanto assume processado
                continue

            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)

            # --- Logica de Normalização de Entrada ---
            
            metadata = data.get("_metadata", {})
            html = data.get("html", "")
            
            # Se não tem HTML, tenta montar um (caso de APIs que retornam texto puro)
            if not html:
                description = data.get("description", data.get("content", ""))
                title_api = data.get("title", data.get("name", ""))
                
                if description:
                    html = f"<h1>{title_api}</h1><div>{description}</div>"

            if not html:
                logger.debug(f"Ignorando arquivo sem conteúdo: {json_file.name}")
                continue

            # Hints para o LLM
            title_hint = data.get("title", data.get("name", ""))
            company_hint = data.get("company", data.get("companyName", metadata.get("company", "")))
            url = data.get("url", data.get("jobUrl", ""))
            platform = metadata.get("platform", "unknown")

            result = await extractor.extract_from_html(
                html,
                url=url,
                platform=platform,
                title_hint=title_hint,
                company_hint=company_hint,
            )

            # Salva Silver
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(result.model_dump(), f, ensure_ascii=False, indent=2, default=str)

            processed += 1
            if processed % 10 == 0:
                logger.info(f"Processados {processed} arquivos...")

        except Exception as e:
            logger.warning(f"Erro ao processar {json_file.name}: {e}")

    logger.info(f"Silver finalizada: {processed} novos arquivos processados")
    return processed


def run_gold() -> int:
    """Executa camada Gold (DuckDB)."""
    logger.info("Iniciando camada Gold")
    from src.analytics import create_star_schema, load_to_gold, run_transforms

    conn = create_star_schema()
    silver_dir = Path("data/silver")
    vagas = []

    for json_file in silver_dir.glob("*_processed.json"):
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)
                vagas.append(data)
        except Exception as e:
            logger.warning(f"Erro leitura gold {json_file.name}: {e}")

    loaded = load_to_gold(conn, vagas)
    run_transforms() # Gera views agregadas
    conn.close()
    
    logger.info(f"Gold finalizada: {loaded} vagas carregadas")
    return loaded


def run_export() -> list[str]:
    """Exporta para Parquet/CSV."""
    from src.analytics.transforms import export_to_parquet
    files = export_to_parquet()
    logger.info(f"Exportados {len(files)} arquivos")
    return files


async def run_notify(platform: str = "all") -> int:
    """Envia notificações Telegram (usa QualityGateV2)."""
    logger.info("Enviando notificações...")
    
    from src.notifications.telegram_v2 import TelegramNotifierV2
    from src.notifications.telegram import JobNotification # Compatibilidade de modelo

    notifier = TelegramNotifierV2()
    
    # Se não configurado, aborta
    if not config.get_telegram_config():
        logger.warning("Telegram não configurado")
        return 0

    silver_dir = Path("data/silver")
    jobs_to_notify = []
    
    # Quality Gate V2
    gate = QualityGateV2()

    for json_file in silver_dir.glob("*_processed.json"):
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)

            vaga = data.get("vaga", data) # Suporta aninhamento antigo e novo
            
            # Adapta para o formato do GateV2
            job_data_for_gate = {
                "title": vaga.get("titulo_normalizado") or vaga.get("titulo_original"),
                "description": vaga.get("descricao", ""),
                "company": vaga.get("empresa", ""),
                "url": vaga.get("url_origem", ""),
            }
            
            # Avaliação
            evaluation = gate.evaluate(job_data_for_gate)
            
            if evaluation.is_valid:
                # Prepara objeto de notificação
                # Extração simples de skills para display
                skills_list = []
                if "skills" in vaga and isinstance(vaga["skills"], list):
                     skills_list = [s.get("nome", s) for s in vaga["skills"] if isinstance(s, dict)]
                
                # Formata salário
                sal_dict = vaga.get("salario", {})
                s_min = sal_dict.get("valor_minimo") if isinstance(sal_dict, dict) else None
                s_max = sal_dict.get("valor_maximo") if isinstance(sal_dict, dict) else None

                job_obj = JobNotification(
                    title=job_data_for_gate["title"],
                    company=job_data_for_gate["company"],
                    location=str(vaga.get("localidade", "")),
                    work_model=vaga.get("modelo_trabalho", "N/A"),
                    url=job_data_for_gate["url"],
                    platform=vaga.get("plataforma", platform),
                    salary_min=s_min,
                    salary_max=s_max,
                    skills=skills_list
                )
                
                # Anexa o score para o notificador usar (se suportado) ou apenas logar
                job_obj.score = evaluation.score 
                
                jobs_to_notify.append(job_obj)
            else:
                logger.debug(f"Rejeitado ({evaluation.score}): {job_data_for_gate['title']}")

        except Exception as e:
            logger.warning(f"Erro preparando notificação de {json_file.name}: {e}")

    if jobs_to_notify:
        logger.info(f"Notificando {len(jobs_to_notify)} vagas aprovadas pelo GateV2")
        sent_count = await notifier.send_batch_summary(jobs_to_notify, only_new=True)
        return sent_count
    else:
        logger.info("Nenhuma vaga qualificada para notificar.")
        return 0


async def run_full_pipeline(query: str, max_jobs: int, platform: str, notify: bool = True) -> None:
    logger.info("=== PIPELINE V2 START ===")
    start = datetime.now()

    await run_bronze(query, max_jobs, platform)
    await run_silver()
    run_gold()
    run_export()

    if notify:
        await run_notify(platform)

    logger.info(f"=== PIPELINE END (Duration: {datetime.now() - start}) ===")


def main():
    parser = argparse.ArgumentParser(description="Pega-Vagas Pipeline V2 (Search-Based)")
    subparsers = parser.add_subparsers(dest="command", help="Comandos")

    # Bronze
    bronze = subparsers.add_parser("bronze")
    bronze.add_argument("--query", default="Data Engineer", help="Lista de termos (csv)")
    bronze.add_argument("--max-jobs", type=int, default=50)
    bronze.add_argument("--platform", default="api")

    # Silver/Gold/Export
    subparsers.add_parser("silver")
    subparsers.add_parser("gold")
    subparsers.add_parser("export")
    
    # Notify
    subparsers.add_parser("notify")

    # Run All
    run = subparsers.add_parser("run")
    run.add_argument("--query", default="Data Engineer")
    run.add_argument("--max-jobs", type=int, default=50)
    run.add_argument("--platform", default="api")
    run.add_argument("--no-notify", action="store_true")

    args = parser.parse_args()

    if args.command == "bronze":
        asyncio.run(run_bronze(args.query, args.max_jobs, args.platform))
    elif args.command == "silver":
        asyncio.run(run_silver())
    elif args.command == "gold":
        run_gold()
    elif args.command == "export":
        run_export()
    elif args.command == "notify":
        asyncio.run(run_notify())
    elif args.command == "run":
        asyncio.run(run_full_pipeline(args.query, args.max_jobs, args.platform, not args.no_notify))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
