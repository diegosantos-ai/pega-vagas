
"""
CLI principal do pipeline Pega-Vagas.

Uso:
    python -m src.pipeline bronze --query "Data Engineer"
    python -m src.pipeline silver
    python -m src.pipeline gold
    python -m src.pipeline run  # Executa tudo
"""
from src.quality_gate import QualityGate

import argparse
import asyncio
import json
import sys
from datetime import date, datetime
from pathlib import Path

import structlog

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


async def run_bronze(query: str, max_jobs: int, platform: str) -> list[str]:
    """Executa camada Bronze (scraping)."""
    logger.info("Iniciando camada Bronze", query=query, max_jobs=max_jobs, platform=platform)

    saved_files = []

    # =========================================================================
    # SCRAPERS DE API (mais rápidos e confiáveis)
    # =========================================================================
    if platform in ("all", "api", "greenhouse", "lever", "smartrecruiters"):
        try:
            from src.ingestion.scrapers.api_scrapers import (
                GreenhouseAPIScraper,
                LeverAPIScraper,
                SmartRecruitersAPIScraper,
                GupyAPIScraper,
            )
            from src.config.companies import get_companies_by_ats, ATSType

            # Greenhouse (Nubank, Stone, XP, etc)
            if platform in ("all", "api", "greenhouse"):
                try:
                    scraper = GreenhouseAPIScraper()
                    files = await scraper.run(query=query, max_jobs_per_company=max_jobs)
                    saved_files.extend(files)
                    logger.info(f"Greenhouse: {len(files)} vagas coletadas")
                except Exception as e:
                    logger.error(f"Erro no Greenhouse: {e}")

            # Lever (Stripe, Figma, etc)
            if platform in ("all", "api", "lever"):
                try:
                    scraper = LeverAPIScraper()
                    files = await scraper.run(query=query, max_jobs_per_company=max_jobs)
                    saved_files.extend(files)
                    logger.info(f"Lever: {len(files)} vagas coletadas")
                except Exception as e:
                    logger.error(f"Erro no Lever: {e}")

            # SmartRecruiters (Serasa, Keyrus)
            if platform in ("all", "api", "smartrecruiters"):
                try:
                    scraper = SmartRecruitersAPIScraper()
                    files = await scraper.run(query=query, max_jobs_per_company=max_jobs)
                    saved_files.extend(files)
                    logger.info(f"SmartRecruiters: {len(files)} vagas coletadas")
                except Exception as e:
                    logger.error(f"Erro no SmartRecruiters: {e}")

            # Gupy API (Itaú, iFood, Magalu, etc)
            if platform in ("all", "api", "gupy-api"):
                try:
                    scraper = GupyAPIScraper()
                    files = await scraper.run(query=query, max_jobs_per_company=max_jobs)
                    saved_files.extend(files)
                    logger.info(f"Gupy API: {len(files)} vagas coletadas")
                except Exception as e:
                    logger.error(f"Erro no Gupy API: {e}")

        except Exception as e:
            logger.error(f"Erro nos scrapers de API: {e}")

    # =========================================================================
    # SCRAPERS DE NAVEGADOR (fallback, mais lentos)
    # =========================================================================
    if platform in ("gupy", "vagas", "linkedin"):
        from src.ingestion import BrowserManager
        from src.ingestion.scrapers.gupy import GupyScraper
        from src.ingestion.scrapers.vagas import VagasScraper

        try:
            async with BrowserManager(headless=True) as browser:
                # Gupy Scraper (navegador)
                if platform == "gupy":
                    try:
                        scraper = GupyScraper(browser)
                        files = await scraper.run(query=query, max_jobs=max_jobs)
                        saved_files.extend(files)
                    except Exception as e:
                        logger.error(f"Erro no scraping Gupy: {e}")

                # Vagas.com.br Scraper
                if platform == "vagas":
                    try:
                        scraper = VagasScraper(browser)
                        files = await scraper.run(query=query, max_jobs=max_jobs)
                        saved_files.extend(files)
                    except Exception as e:
                        logger.error(f"Erro no scraping Vagas: {e}")

                # LinkedIn Scraper
                if platform == "linkedin":
                    try:
                        from src.ingestion.scrapers.linkedin import LinkedInScraper
                        scraper = LinkedInScraper(browser)
                        files = await scraper.run(query=query, max_jobs=max_jobs)
                        saved_files.extend(files)
                    except Exception as e:
                        logger.error(f"Erro no scraping LinkedIn: {e}")

        except Exception as e:
            logger.error(f"Erro ao iniciar navegador: {e}")

    logger.info(f"Bronze finalizada: {len(saved_files)} arquivos salvos")
    return saved_files


async def run_silver() -> int:
    """Executa camada Silver (processamento LLM)."""
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

    # Processa cada arquivo JSON da Bronze
    for json_file in bronze_dir.rglob("*.json"):
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)

            # Normaliza diferentes formatos de dados bronze:
            # 1. Browser scraper: {html, url, title, company, _metadata}
            # 2. API scraper: {content/description, absolute_url/url, title/name, _metadata}
            
            metadata = data.get("_metadata", {})
            
            # Obtém HTML/conteúdo
            html = data.get("html", "")
            if not html:
                # Formato API - monta HTML a partir dos campos
                content = data.get("content", data.get("description", ""))
                name = data.get("name", data.get("title", ""))
                location = data.get("location", {})
                loc_name = location.get("name", "") if isinstance(location, dict) else str(location)
                
                if content or name:
                    # Cria um HTML mínimo para o LLM processar
                    html = f"""
                    <h1>{name}</h1>
                    <p><strong>Localização:</strong> {loc_name}</p>
                    <div>{content}</div>
                    """
            
            if not html:
                logger.debug(f"Sem conteúdo para processar: {json_file.name}")
                continue

            # Obtém hints
            title_hint = data.get("title", data.get("name", ""))
            company_hint = data.get("company", metadata.get("company", ""))
            url = data.get("url", data.get("absolute_url", data.get("hostedUrl", "")))
            platform = metadata.get("platform", data.get("platform", ""))

            result = await extractor.extract_from_html(
                html,
                url=url,
                platform=platform,
                title_hint=title_hint,
                company_hint=company_hint,
            )

            # Salva na Silver
            out_file = silver_dir / f"{json_file.stem}_processed.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(result.model_dump(), f, ensure_ascii=False, indent=2, default=str)

            processed += 1
            logger.debug(f"Processado: {json_file.name}")

        except Exception as e:
            logger.warning(f"Erro ao processar {json_file}: {e}")

    logger.info(f"Silver finalizada: {processed} arquivos processados")
    return processed


def run_gold() -> int:
    """Executa camada Gold (DuckDB transforms)."""
    logger.info("Iniciando camada Gold")

    from src.analytics import create_star_schema, load_to_gold, run_transforms

    # Cria/conecta ao banco
    conn = create_star_schema()

    # Carrega dados da Silver
    silver_dir = Path("data/silver")
    vagas = []

    for json_file in silver_dir.glob("*_processed.json"):
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)
                vagas.append(data)
        except Exception as e:
            logger.warning(f"Erro ao ler {json_file}: {e}")

    # Carrega no Star Schema
    loaded = load_to_gold(conn, vagas)

    # Cria views analíticas
    run_transforms()

    conn.close()
    logger.info(f"Gold finalizada: {loaded} vagas carregadas")
    return loaded


def run_export() -> list[str]:
    """Exporta dados para Parquet."""
    logger.info("Exportando para Parquet")

    from src.analytics.transforms import export_to_parquet

    files = export_to_parquet()
    logger.info(f"Exportados {len(files)} arquivos")
    return files


async def run_notify(platform: str = "all") -> int:
    """Envia notificações de vagas novas via Telegram."""
    logger.info("Enviando notificações", platform=platform)

    from src.notifications.telegram import JobNotification, TelegramNotifier

    try:
        notifier = TelegramNotifier()
    except ValueError as e:
        logger.error(f"Telegram não configurado: {e}")
        return 0

    # Carrega vagas da Silver para notificar
    silver_dir = Path("data/silver")
    jobs = []

    for json_file in silver_dir.glob("*_processed.json"):
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)

            vaga = data.get("vaga", data)

            # FILTRO: Apenas vagas REMOTAS
            work_model = vaga.get("modelo_trabalho", "")
            if work_model != "Remoto":
                # Logger debug opcional para saber o que foi filtrado
                # logger.debug(f"Ignorando vaga não-remota: {vaga.get('titulo_original')}")
                continue


            # QualityGate: valida vaga antes de notificar
            gate = QualityGate()
            avaliacao = gate.evaluate({
                "url": vaga.get("url_origem", ""),
                "title": vaga.get("titulo_normalizado", vaga.get("titulo_original", "")),
                "description": vaga.get("descricao", ""),
                "company": vaga.get("empresa", ""),
                "original_location": vaga.get("localidade", "")
            })
            if not (avaliacao.is_valid and avaliacao.score >= 40):
                logger.info(f"Vaga descartada pelo QualityGate: {avaliacao.rejection_reason}")
                continue

            skills = []
            if vaga.get("skills"):
                skills = [s.get("nome", s) if isinstance(s, dict) else s for s in vaga["skills"][:5]]

            job = JobNotification(
                title=vaga.get("titulo_normalizado", vaga.get("titulo_original", "N/A")),
                company=vaga.get("empresa", "N/A"),
                location=vaga.get("localidade", {}).get("cidade", "") if isinstance(vaga.get("localidade"), dict) else "",
                work_model=vaga.get("modelo_trabalho", ""),
                url=vaga.get("url_origem", ""),
                platform=vaga.get("plataforma", platform),
                salary_min=vaga.get("salario", {}).get("valor_minimo") if isinstance(vaga.get("salario"), dict) else None,
                salary_max=vaga.get("salario", {}).get("valor_maximo") if isinstance(vaga.get("salario"), dict) else None,
                skills=skills,
            )
            jobs.append(job)

        except Exception as e:
            logger.warning(f"Erro ao preparar notificação {json_file}: {e}")

    if not jobs:
        logger.info("Nenhuma vaga para notificar")
        return 0

    # Envia notificações
    sent = await notifier.send_batch_summary(jobs, only_new=True)
    logger.info(f"Notificações enviadas: {sent}")
    return sent


async def run_full_pipeline(query: str, max_jobs: int, platform: str, notify: bool = True) -> None:
    """Executa pipeline completo."""
    logger.info("=== INICIANDO PIPELINE COMPLETO ===")
    start = datetime.now()

    # Bronze
    await run_bronze(query, max_jobs, platform)

    # Silver
    await run_silver()

    # Gold
    run_gold()

    # Export
    run_export()

    # Notificar (se configurado)
    if notify:
        try:
            await run_notify(platform)
        except Exception as e:
            logger.warning(f"Erro nas notificações: {e}")

    duration = datetime.now() - start
    logger.info(f"=== PIPELINE FINALIZADO em {duration} ===")


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline Pega-Vagas - Coleta e análise de vagas de tecnologia"
    )

    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # Comando: bronze
    bronze_parser = subparsers.add_parser("bronze", help="Executa scraping")
    bronze_parser.add_argument("--query", default="Data Engineer", help="Termo de busca")
    bronze_parser.add_argument("--max-jobs", type=int, default=50, help="Máximo de vagas")
    bronze_parser.add_argument("--platform", default="all", help="Plataforma alvo")

    # Comando: silver
    subparsers.add_parser("silver", help="Executa processamento LLM")

    # Comando: gold
    subparsers.add_parser("gold", help="Executa transformações DuckDB")

    # Comando: export
    subparsers.add_parser("export", help="Exporta para Parquet")

    # Comando: notify
    notify_parser = subparsers.add_parser("notify", help="Envia notificações Telegram")
    notify_parser.add_argument("--platform", default="all", help="Filtrar por plataforma")

    # Comando: run
    run_parser = subparsers.add_parser("run", help="Executa pipeline completo")
    run_parser.add_argument("--query", default="Data Engineer", help="Termo de busca")
    run_parser.add_argument("--max-jobs", type=int, default=50, help="Máximo de vagas")
    run_parser.add_argument("--platform", default="all", help="Plataforma alvo")
    run_parser.add_argument("--no-notify", action="store_true", help="Não enviar notificações")

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
        asyncio.run(run_notify(args.platform))
    elif args.command == "run":
        asyncio.run(run_full_pipeline(args.query, args.max_jobs, args.platform, not args.no_notify))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

