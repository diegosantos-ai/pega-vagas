import asyncio
import structlog
from src.notifications.telegram import TelegramNotifier, JobNotification

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(colors=True),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)

async def test_notify():
    print("Iniciando teste de notificação...")
    notifier = TelegramNotifier()
    
    job = JobNotification(
        title="Senior Data Engineer (Teste)",
        company="Empresa Teste",
        location="Remoto",
        work_model="Remoto",
        url="https://google.com",
        platform="teste",
        salary_min=15000,
        salary_max=20000,
        skills=["Python", "SQL", "AWS"]
    )
    
    # Força envio ignorando cache
    print("Enviando vaga de teste...")
    success = await notifier.send_job_alert(job, skip_if_seen=False)
    print(f"Resultado: {success}")

if __name__ == "__main__":
    asyncio.run(test_notify())
