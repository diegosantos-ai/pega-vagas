"""
Script para testar disparo de notificações Telegram com vagas do BD.

Uso:
    python test_telegram_dispatch.py              # Envia até 5 vagas (preview)
    python test_telegram_dispatch.py --all        # Envia todas as vagas
    python test_telegram_dispatch.py --limit 10   # Envia até 10 vagas
    python test_telegram_dispatch.py --dry-run    # Mostra sem enviar
    python test_telegram_dispatch.py --no-filter  # Desabilita filtros (debug)
"""

import argparse
import asyncio
from pathlib import Path

import duckdb
from dotenv import load_dotenv

from src.notifications.telegram import JobNotification, TelegramNotifier
from src.processing.validators import is_valid_job

load_dotenv()


def get_jobs_from_db(db_path: str = "data/gold/vagas.duckdb", limit: int = 5) -> list[dict]:
    """Busca vagas do banco DuckDB."""

    # Verifica se o banco existe
    if not Path(db_path).exists():
        print(f"Banco nao encontrado: {db_path}")
        print("Tentando buscar de arquivos silver...")
        return get_jobs_from_silver()

    conn = duckdb.connect(db_path, read_only=True)

    query = f"""
    SELECT 
        f.titulo_original,
        f.titulo_normalizado,
        f.senioridade,
        f.modelo_trabalho,
        f.url_origem,
        f.plataforma,
        f.salario_min,
        f.salario_max,
        f.skills,
        f.data_coleta,
        e.nome as empresa,
        l.cidade,
        l.estado
    FROM fact_vagas f
    LEFT JOIN dim_empresa e ON f.empresa_sk = e.empresa_sk
    LEFT JOIN dim_localidade l ON f.localidade_sk = l.localidade_sk
    ORDER BY f.data_coleta DESC
    LIMIT {limit if limit > 0 else 1000}
    """

    try:
        result = conn.execute(query).fetchall()
        columns = [desc[0] for desc in conn.description]
        jobs = [dict(zip(columns, row, strict=False)) for row in result]
        conn.close()
        return jobs
    except Exception as e:
        print(f"Erro ao consultar banco: {e}")
        conn.close()
        return []


def get_jobs_from_silver(limit: int = 5, apply_filters: bool = True) -> list[dict]:
    """Busca vagas dos arquivos JSON na camada silver.

    Args:
        limit: Máximo de vagas a retornar (0 = sem limite)
        apply_filters: Se True, aplica filtros de remoto e Brasil
    """
    import json

    silver_dir = Path("data/silver")
    jobs = []

    # Carrega todas as vagas primeiro (para aplicar filtros depois)
    all_jobs = []
    for json_file in silver_dir.glob("*_processed.json"):
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)

            vaga = data.get("vaga", {})
            all_jobs.append(
                {
                    "titulo_original": vaga.get("titulo_original", ""),
                    "titulo_normalizado": vaga.get("titulo_normalizado", ""),
                    "senioridade": vaga.get("senioridade", ""),
                    "modelo_trabalho": vaga.get("modelo_trabalho", ""),
                    "localidade": vaga.get("localidade", {}),
                    "url_origem": vaga.get("url_origem", ""),
                    "plataforma": vaga.get("plataforma", ""),
                    "salario_min": vaga.get("salario", {}).get("valor_minimo")
                    if vaga.get("salario")
                    else None,
                    "salario_max": vaga.get("salario", {}).get("valor_maximo")
                    if vaga.get("salario")
                    else None,
                    "skills": vaga.get("skills", []),
                    "empresa": vaga.get("empresa", ""),
                    "descricao_resumida": vaga.get("descricao_resumida", ""),
                }
            )
        except Exception as e:
            print(f"Erro ao ler {json_file.name}: {e}")

    # Aplica filtros de remoto e Brasil
    if apply_filters:
        print("\\nAplicando filtros (remoto + Brasil)...")
        print(f"  Total antes: {len(all_jobs)}")

        valid_jobs = []
        rejected_reasons = {"not_remote": 0, "not_brazil": 0}

        for job in all_jobs:
            is_valid, reason = is_valid_job(job, empresa_validada=True)
            if is_valid:
                valid_jobs.append(job)
            else:
                if "remoto" in reason.lower():
                    rejected_reasons["not_remote"] += 1
                else:
                    rejected_reasons["not_brazil"] += 1

        print(f"  Rejeitadas (nao remoto): {rejected_reasons['not_remote']}")
        print(f"  Rejeitadas (nao Brasil): {rejected_reasons['not_brazil']}")
        print(f"  Validas: {len(valid_jobs)}")

        jobs = valid_jobs
    else:
        jobs = all_jobs

    # Aplica limite
    if limit > 0:
        jobs = jobs[:limit]

    # Extrai cidade/estado da localidade
    for job in jobs:
        loc = job.get("localidade", {})
        if isinstance(loc, dict):
            job["cidade"] = loc.get("cidade")
            job["estado"] = loc.get("estado")
        else:
            job["cidade"] = None
            job["estado"] = None

    return jobs

    return jobs


def job_to_notification(job: dict) -> JobNotification:
    """Converte dict do banco para JobNotification."""

    # Formata localização
    cidade = job.get("cidade")
    estado = job.get("estado")
    if cidade and estado:
        location = f"{cidade}, {estado}"
    elif estado:
        location = estado
    elif job.get("modelo_trabalho") == "Remoto":
        location = "Remoto"
    else:
        location = "Nao informado"

    return JobNotification(
        title=job.get("titulo_normalizado") or job.get("titulo_original", "N/A"),
        company=job.get("empresa", "N/A"),
        location=location,
        work_model=job.get("modelo_trabalho", "N/A"),
        url=job.get("url_origem", ""),
        platform=job.get("plataforma", "N/A"),
        salary_min=job.get("salario_min"),
        salary_max=job.get("salario_max"),
        skills=job.get("skills") if isinstance(job.get("skills"), list) else [],
    )


async def send_jobs(jobs: list[dict], dry_run: bool = False):
    """Envia lista de vagas via Telegram."""

    if not jobs:
        print("Nenhuma vaga encontrada para enviar.")
        return

    print(f"\n{'=' * 60}")
    print(f"VAGAS PARA ENVIAR: {len(jobs)}")
    print(f"{'=' * 60}\n")

    if dry_run:
        print("[DRY-RUN] Mostrando vagas sem enviar:\n")
        for i, job in enumerate(jobs, 1):
            notification = job_to_notification(job)
            print(f"{i}. {notification.title}")
            print(f"   Empresa: {notification.company}")
            print(f"   Local: {notification.location} | {notification.work_model}")
            print(
                f"   Skills: {', '.join(notification.skills[:5]) if notification.skills else 'N/A'}"
            )
            print(
                f"   URL: {notification.url[:60]}..."
                if len(notification.url) > 60
                else f"   URL: {notification.url}"
            )
            print()
        return

    # Inicializa notificador
    try:
        notifier = TelegramNotifier(
            seen_jobs_file="data/.seen_jobs_test.json"  # Arquivo separado para teste
        )
    except ValueError as e:
        print(f"Erro: {e}")
        print("\nConfigure as variaveis de ambiente:")
        print("  TELEGRAM_BOT_TOKEN=seu_token_aqui")
        print("  TELEGRAM_CHAT_ID=seu_chat_id_aqui")
        return

    # Envia mensagem de início
    total = len(jobs)
    await notifier.send_message(
        f"*Teste de Disparo - Pega Vagas*\n\nEnviando {total} vaga(s) do banco de dados...",
        parse_mode="Markdown",
    )

    # Envia cada vaga
    enviadas = 0
    erros = 0

    for i, job in enumerate(jobs, 1):
        notification = job_to_notification(job)
        print(f"[{i}/{total}] Enviando: {notification.title[:40]}...", end=" ")

        # Força envio mesmo se já vista (é teste)
        success = await notifier.send_job_alert(notification, skip_if_seen=False)

        if success:
            print("OK")
            enviadas += 1
        else:
            print("ERRO")
            erros += 1

        # Rate limiting - espera 1s entre mensagens
        if i < total:
            await asyncio.sleep(1)

    # Resumo
    print(f"\n{'=' * 60}")
    print(f"RESUMO: {enviadas} enviadas, {erros} erros")
    print(f"{'=' * 60}")

    await notifier.send_message(
        f"*Teste concluido!*\n\nEnviadas: {enviadas}\nErros: {erros}", parse_mode="Markdown"
    )


def main():
    parser = argparse.ArgumentParser(description="Testa disparo de vagas via Telegram")
    parser.add_argument("--limit", type=int, default=5, help="Limite de vagas (default: 5)")
    parser.add_argument("--all", action="store_true", help="Envia todas as vagas")
    parser.add_argument("--dry-run", action="store_true", help="Mostra sem enviar")
    parser.add_argument(
        "--no-filter", action="store_true", help="Desabilita filtros de remoto/Brasil"
    )
    parser.add_argument("--db", default="data/gold/vagas.duckdb", help="Caminho do banco")
    args = parser.parse_args()

    limit = 0 if args.all else args.limit
    apply_filters = not args.no_filter

    print("Buscando vagas do banco de dados...")
    jobs = get_jobs_from_db(args.db, limit)

    if not jobs:
        print("Nenhuma vaga encontrada no banco. Tentando silver...")
        jobs = get_jobs_from_silver(limit, apply_filters=apply_filters)
    elif apply_filters:
        # Aplica filtros também nos dados do banco
        print("\nAplicando filtros (remoto + Brasil)...")
        print(f"  Total antes: {len(jobs)}")

        valid_jobs = []
        rejected_reasons = {"not_remote": 0, "not_brazil": 0}

        for job in jobs:
            # Converte formato do banco para formato esperado pelo validador
            job_for_validation = {
                "titulo_original": job.get("titulo_original", ""),
                "modelo_trabalho": job.get("modelo_trabalho", ""),
                "localidade": {
                    "cidade": job.get("cidade"),
                    "estado": job.get("estado"),
                    "pais": "Brasil",  # Assumimos Brasil se veio do nosso banco
                },
                "descricao_resumida": job.get("descricao_resumida", ""),
            }
            is_valid, reason = is_valid_job(job_for_validation, empresa_validada=True)
            if is_valid:
                valid_jobs.append(job)
            else:
                if "remoto" in reason.lower():
                    rejected_reasons["not_remote"] += 1
                else:
                    rejected_reasons["not_brazil"] += 1

        print(f"  Rejeitadas (nao remoto): {rejected_reasons['not_remote']}")
        print(f"  Rejeitadas (nao Brasil): {rejected_reasons['not_brazil']}")
        print(f"  Validas: {len(valid_jobs)}")
        jobs = valid_jobs

    print(f"Vagas para envio: {len(jobs)}")

    asyncio.run(send_jobs(jobs, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
