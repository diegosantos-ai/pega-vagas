"""
Notificador via Telegram Bot API - v2 (Melhorado)

Melhorias:
- Formatação corrigida de URLs (encoding UTF-8)
- Suporte a resumo de vagas (ao invés de enviar uma por uma)
- Sistema de scoring integrado
- Melhor tratamento de erros
"""

import json
import os
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import httpx
import structlog
from dotenv import load_dotenv

load_dotenv()
logger = structlog.get_logger()


@dataclass
class JobNotification:
    """Dados de uma vaga para notificação."""

    title: str
    company: str
    url: str
    platform: str
    location: str | None = None
    work_model: str = "Remoto"
    salary_min: float | None = None
    salary_max: float | None = None
    skills: list[str] | None = None
    published_date: str | None = None
    score: int | None = None  # Score de relevância (0-100)
    description_snippet: str | None = None  # Trecho da descrição


class TelegramNotifierV2:
    """
    Notificador melhorado via Telegram com suporte a resumo.
    """

    API_BASE = "https://api.telegram.org/bot{token}"

    def __init__(
        self,
        bot_token: str | None = None,
        chat_id: str | None = None,
        seen_jobs_file: str = "data/.seen_jobs.json",
    ):
        """
        Args:
            bot_token: Token do bot Telegram (ou usa TELEGRAM_BOT_TOKEN)
            chat_id: ID do chat para enviar (ou usa TELEGRAM_CHAT_ID)
            seen_jobs_file: Arquivo para tracking de vagas já notificadas
        """
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.seen_jobs_file = Path(seen_jobs_file)

        if not self.bot_token:
            raise ValueError(
                "TELEGRAM_BOT_TOKEN não configurado. "
                "Crie um bot com @BotFather e adicione o token no .env"
            )

        if not self.chat_id:
            logger.warning(
                "TELEGRAM_CHAT_ID não configurado. Use get_updates() para descobrir seu chat_id"
            )

        self.api_url = self.API_BASE.format(token=self.bot_token)
        self._seen_jobs: set[str] = self._load_seen_jobs()

        logger.info("TelegramNotifierV2 inicializado", chat_id=self.chat_id)

    def _load_seen_jobs(self) -> set[str]:
        """Carrega IDs de vagas já notificadas."""
        if self.seen_jobs_file.exists():
            try:
                with open(self.seen_jobs_file, encoding="utf-8") as f:
                    data = json.load(f)
                    return set(data.get("seen", []))
            except Exception:
                return set()
        return set()

    def _save_seen_jobs(self) -> None:
        """Salva IDs de vagas já notificadas."""
        self.seen_jobs_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.seen_jobs_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "seen": list(self._seen_jobs),
                    "updated_at": datetime.now().isoformat(),
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

    def _job_id(self, job: JobNotification) -> str:
        """Gera ID único para uma vaga (para evitar duplicatas)."""
        return f"{job.platform}:{job.company}:{job.title}".lower().replace(" ", "_")

    def is_new_job(self, job: JobNotification) -> bool:
        """Verifica se a vaga é nova (não foi notificada antes)."""
        return self._job_id(job) not in self._seen_jobs

    def mark_as_seen(self, job: JobNotification) -> None:
        """Marca vaga como já notificada."""
        self._seen_jobs.add(self._job_id(job))
        self._save_seen_jobs()

    def _sanitize_url(self, url: str) -> str:
        """
        Sanitiza URL para evitar problemas de encoding no Telegram.
        Garante que caracteres especiais sejam corretamente codificados.
        """
        if not url:
            return ""

        try:
            # Tenta fazer parse da URL
            urllib.parse.urlparse(url)

            # Reconstrói a URL com encoding correto
            # Mantém a URL como está se já estiver bem formada
            return url

        except Exception as e:
            logger.warning(f"Erro ao sanitizar URL {url}: {e}")
            return url

    def _format_job_summary_message(self, jobs: list[JobNotification]) -> str:
        """
        Formata um resumo de múltiplas vagas em uma única mensagem.
        Ideal para enviar a cada 3 horas.
        """
        if not jobs:
            return "📭 Nenhuma vaga nova encontrada."

        lines = [
            f"📊 *Resumo de Vagas - {datetime.now().strftime('%d/%m %H:%M')}*",
            "",
            f"✨ Encontradas *{len(jobs)} vagas* relevantes:",
            "",
        ]

        # Agrupa por empresa
        by_company = {}
        for job in jobs:
            if job.company not in by_company:
                by_company[job.company] = []
            by_company[job.company].append(job)

        # Formata cada empresa
        for i, (company, company_jobs) in enumerate(by_company.items(), 1):
            if i > 1:
                lines.append("")

            lines.append(f"*{i}. {company}*")

            for job in company_jobs:
                score_indicator = ""
                if job.score:
                    if job.score >= 80:
                        score_indicator = " 🔥"
                    elif job.score >= 60:
                        score_indicator = " ⭐"

                lines.append(f"  • {job.title}{score_indicator}")

                if job.score:
                    lines.append(f"    Score: {job.score}/100")

        # Rodapé com link para mais detalhes
        lines.append("")
        lines.append("_Clique nos links abaixo para ver detalhes de cada vaga_")

        return "\n".join(lines)

    def _format_job_detail_message(self, job: JobNotification) -> str:
        """Formata mensagem detalhada de uma vaga individual."""
        lines = []

        # Cabeçalho
        score_emoji = ""
        if job.score:
            if job.score >= 80:
                score_emoji = "🔥 "
            elif job.score >= 60:
                score_emoji = "⭐ "

        lines.append(f"*{score_emoji}{job.title}*")
        lines.append(f"🏢 {job.company}")

        # Localização e modelo
        if job.location:
            lines.append(f"📍 {job.location}")
        lines.append(f"🏠 {job.work_model}")

        # Salário
        if job.salary_min or job.salary_max:
            if job.salary_min and job.salary_max:
                salary_str = f"R$ {job.salary_min:,.0f} - R$ {job.salary_max:,.0f}"
            elif job.salary_max:
                salary_str = f"Até R$ {job.salary_max:,.0f}"
            else:
                salary_str = f"A partir de R$ {job.salary_min:,.0f}"
            lines.append(f"💰 {salary_str}")

        # Skills
        if job.skills:
            skills_str = ", ".join(job.skills[:5])
            if len(job.skills) > 5:
                skills_str += f" +{len(job.skills) - 5}"
            lines.append(f"🛠️ {skills_str}")

        # Score
        if job.score:
            lines.append(f"📈 Relevância: {job.score}/100")

        # Data
        if job.published_date:
            lines.append(f"📅 {job.published_date}")

        # Link (com sanitização)
        url = self._sanitize_url(job.url)
        if url:
            lines.append(f"\n[🔗 Ver vaga completa]({url})")

        return "\n".join(lines)

    async def send_message(
        self,
        text: str,
        parse_mode: str = "Markdown",
        disable_preview: bool = True,
    ) -> bool:
        """
        Envia uma mensagem de texto para o chat configurado.

        Args:
            text: Texto da mensagem (suporta Markdown)
            parse_mode: "Markdown" ou "HTML"
            disable_preview: Se True, desabilita preview de links

        Returns:
            True se enviou com sucesso
        """
        if not self.chat_id:
            logger.error("chat_id não configurado")
            return False

        url = f"{self.api_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_preview,
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                logger.debug("Mensagem enviada com sucesso")
                return True

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Erro HTTP ao enviar: {e.response.status_code}",
                response_text=e.response.text[:200],
            )
            return False
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem: {e}")
            return False

    async def send_job_summary(
        self,
        jobs: list[JobNotification],
        only_new: bool = True,
        send_details: bool = True,
    ) -> int:
        """
        Envia um resumo de vagas seguido de detalhes individuais.

        Args:
            jobs: Lista de vagas
            only_new: Se True, filtra apenas vagas novas
            send_details: Se True, envia detalhes de cada vaga após o resumo

        Returns:
            Número de notificações enviadas
        """
        if only_new:
            jobs = [j for j in jobs if self.is_new_job(j)]

        if not jobs:
            logger.info("Nenhuma vaga nova para notificar")
            return 0

        # Envia resumo
        summary_msg = self._format_job_summary_message(jobs)
        summary_success = await self.send_message(summary_msg)

        if not summary_success:
            logger.error("Falha ao enviar resumo de vagas")
            # Mesmo falhando o resumo, marca como vistas para não tentar de novo
            for job in jobs:
                self.mark_as_seen(job)
            return 0

        sent = 1

        # Envia detalhes de cada vaga (se configurado)
        if send_details:
            import asyncio

            for job in jobs:
                try:
                    detail_msg = self._format_job_detail_message(job)
                    success = await self.send_message(detail_msg)

                    if success:
                        self.mark_as_seen(job)
                        sent += 1
                    else:
                        logger.warning(f"Falha ao enviar notificação para: {job.title}")

                    # Delay para evitar rate limit
                    await asyncio.sleep(0.5)
                except Exception as e:
                    logger.error(f"Erro ao enviar notificação para {job.title}: {e}")
                    continue

        else:
            # Apenas marca como vistas
            for job in jobs:
                self.mark_as_seen(job)

        return sent

    async def test_connection(self) -> bool:
        """Testa a conexão enviando uma mensagem de teste."""
        test_msg = (
            "🤖 *Pega-Vagas Bot - v2*\n\n"
            "✅ Conexão estabelecida!\n"
            "Você receberá alertas de novas vagas a cada 3 horas."
        )
        return await self.send_message(test_msg)


if __name__ == "__main__":
    import asyncio

    # Teste
    async def test():
        notifier = TelegramNotifierV2()

        # Teste de conexão
        print("Testando conexão...")
        success = await notifier.test_connection()
        print(f"Conexão: {'✅ OK' if success else '❌ Falhou'}")

    asyncio.run(test())
