"""
Notificador via Telegram Bot API.

Envia alertas de novas vagas para um chat/grupo do Telegram.

Setup:
1. Crie um bot com @BotFather no Telegram
2. Pegue o token do bot
3. Inicie uma conversa com o bot
4. Pegue seu chat_id (use /start no bot ou a função get_chat_id)
"""

import json
import os
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
    location: str
    work_model: str  # Remoto, Híbrido, Presencial
    url: str
    platform: str
    salary_min: float | None = None
    salary_max: float | None = None
    skills: list[str] | None = None
    published_date: str | None = None


class TelegramNotifier:
    """
    Envia notificações de vagas via Telegram.

    Exemplo de uso:
        notifier = TelegramNotifier()
        await notifier.send_job_alert(job)
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
                "TELEGRAM_CHAT_ID não configurado. "
                "Use get_updates() para descobrir seu chat_id"
            )

        self.api_url = self.API_BASE.format(token=self.bot_token)
        self._seen_jobs: set[str] = self._load_seen_jobs()

        logger.info("TelegramNotifier inicializado", chat_id=self.chat_id)

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

    async def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """
        Envia uma mensagem de texto para o chat configurado.

        Args:
            text: Texto da mensagem (suporta Markdown)
            parse_mode: "Markdown" ou "HTML"

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
            "disable_web_page_preview": False,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10)
                response.raise_for_status()
                logger.debug("Mensagem enviada com sucesso")
                return True

        except httpx.HTTPStatusError as e:
            logger.error(f"Erro HTTP ao enviar: {e.response.status_code}")
            return False
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem: {e}")
            return False

    async def send_job_alert(self, job: JobNotification, skip_if_seen: bool = True) -> bool:
        """
        Envia alerta de uma nova vaga.

        Args:
            job: Dados da vaga
            skip_if_seen: Se True, não envia se já foi notificada

        Returns:
            True se enviou (ou se pulou por já ter sido vista)
        """
        # Verifica se já foi notificada
        if skip_if_seen and not self.is_new_job(job):
            logger.debug(f"Vaga já notificada: {job.title}")
            return True

        # Formata a mensagem
        message = self._format_job_message(job)

        # Envia
        success = await self.send_message(message)

        if success:
            self.mark_as_seen(job)
            logger.info(f"Notificação enviada: {job.title} @ {job.company}")

        return success

    def _format_job_message(self, job: JobNotification) -> str:
        """Formata a mensagem da vaga para Telegram."""
        # Emojis baseados no modelo de trabalho
        work_emoji = {
            "Remoto": "🏠",
            "Híbrido": "🔄",
            "Presencial": "🏢",
        }.get(job.work_model, "📍")

        # Monta a mensagem
        lines = [
            f"🎯 *Nova Vaga - {job.platform}*",
            "",
            f"*{job.title}*",
            f"🏢 {job.company}",
        ]

        if job.location:
            lines.append(f"{work_emoji} {job.location} ({job.work_model})")
        elif job.work_model:
            lines.append(f"{work_emoji} {job.work_model}")

        # Salário
        if job.salary_min or job.salary_max:
            if job.salary_min and job.salary_max:
                salary_str = f"R$ {job.salary_min:,.0f} - R$ {job.salary_max:,.0f}"
            elif job.salary_max:
                salary_str = f"Até R$ {job.salary_max:,.0f}"
            else:
                salary_str = f"A partir de R$ {job.salary_min:,.0f}"
            lines.append(f"💰 {salary_str}")

        # Skills (top 5)
        if job.skills:
            skills_str = ", ".join(job.skills[:5])
            if len(job.skills) > 5:
                skills_str += f" +{len(job.skills) - 5}"
            lines.append(f"🛠️ {skills_str}")

        # Data
        if job.published_date:
            lines.append(f"📅 {job.published_date}")

        # Link
        lines.append("")
        lines.append(f"[🔗 Ver vaga]({job.url})")

        return "\n".join(lines)

    async def send_batch_summary(
        self,
        jobs: list[JobNotification],
        only_new: bool = True,
    ) -> int:
        """
        Envia um resumo de várias vagas.

        Args:
            jobs: Lista de vagas
            only_new: Se True, filtra apenas vagas novas

        Returns:
            Número de notificações enviadas
        """
        if only_new:
            jobs = [j for j in jobs if self.is_new_job(j)]

        if not jobs:
            logger.info("Nenhuma vaga nova para notificar")
            return 0

        # Envia resumo inicial
        summary = f"📊 *Encontradas {len(jobs)} vagas novas!*\n\nEnviando detalhes..."
        await self.send_message(summary)

        # Envia cada vaga
        sent = 0
        for job in jobs:
            success = await self.send_job_alert(job, skip_if_seen=False)
            if success:
                sent += 1
                self.mark_as_seen(job)

            # Pequeno delay para não atingir rate limit
            import asyncio
            await asyncio.sleep(0.5)

        # Resumo final
        final = f"✅ *Resumo:* {sent} vagas notificadas"
        await self.send_message(final)

        return sent

    async def get_updates(self) -> list[dict]:
        """
        Obtém atualizações do bot (útil para descobrir chat_id).

        Retorna lista de updates com informações de chats.
        """
        url = f"{self.api_url}/getUpdates"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()

                if data.get("ok"):
                    updates = data.get("result", [])
                    for update in updates:
                        if "message" in update:
                            chat = update["message"]["chat"]
                            logger.info(
                                f"Chat encontrado: id={chat['id']}, "
                                f"type={chat['type']}, "
                                f"name={chat.get('first_name', chat.get('title', 'N/A'))}"
                            )
                    return updates

        except Exception as e:
            logger.error(f"Erro ao obter updates: {e}")

        return []

    async def test_connection(self) -> bool:
        """Testa a conexão enviando uma mensagem de teste."""
        test_msg = (
            "🤖 *Pega-Vagas Bot*\n\n"
            "✅ Conexão estabelecida!\n"
            "Você receberá alertas de novas vagas aqui."
        )
        return await self.send_message(test_msg)


async def setup_telegram():
    """Assistente para configurar o Telegram."""
    print("\n🤖 Configuração do Telegram Bot\n")
    print("1. Abra o Telegram e procure por @BotFather")
    print("2. Envie /newbot e siga as instruções")
    print("3. Copie o token do bot\n")

    token = input("Cole o token do bot aqui: ").strip()

    if not token:
        print("❌ Token inválido")
        return

    print("\nAgora, abra o Telegram e envie /start para o seu bot.")
    print("Depois, pressione Enter aqui para continuar...")
    input()

    # Busca o chat_id
    notifier = TelegramNotifier(bot_token=token, chat_id="0")
    updates = await notifier.get_updates()

    if updates:
        chat_id = updates[-1]["message"]["chat"]["id"]
        print(f"\n✅ Chat ID encontrado: {chat_id}")
        print("\nAdicione estas linhas ao seu .env:")
        print(f"TELEGRAM_BOT_TOKEN={token}")
        print(f"TELEGRAM_CHAT_ID={chat_id}")
    else:
        print("\n❌ Nenhum chat encontrado. Envie /start para o bot primeiro.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(setup_telegram())
