"""
Pipeline simplificado para coleta de vagas.

Fluxo: Plataformas/Empresas → Filtro (Remoto + Brasil + Data) → JSON → Telegram

Uso:
    python -m src.simple_pipeline                    # Modo teste (7 dias)
    python -m src.simple_pipeline --mode prod        # Modo produção (24h)
    python -m src.simple_pipeline --dry-run          # Preview sem enviar
    python -m src.simple_pipeline --platforms-only   # Só plataformas
    python -m src.simple_pipeline --companies-only   # Só empresas foco
"""

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import structlog
from dotenv import load_dotenv

from src.config.companies import (
    get_all_companies,
    get_companies_by_ats,
    ATSType,
)
from src.ingestion.scrapers.api_scrapers import (
    GupyAPIScraper,
    GreenhouseAPIScraper,
    LeverAPIScraper,
    SmartRecruitersAPIScraper,
)
from src.processing.validators import is_valid_job_full
from src.processing.normalizers import normalize_job_title, normalize_seniority

load_dotenv()
logger = structlog.get_logger()


# Títulos de vagas alvo (PT-BR e EN)
JOB_TITLES = [
    # Data Engineering
    "Data Engineer",
    "Engenheiro de Dados",
    "Engenheira de Dados",
    # Data Science
    "Data Scientist",
    "Cientista de Dados",
    # Data Analysis
    "Data Analyst",
    "Analista de Dados",
    # Development (Senior)
    "Full Stack",
    "Desenvolvedor Full Stack",
    "Desenvolvedora Full Stack",
    "Back End",
    "Backend",
    "Desenvolvedor Back End",
    "Desenvolvedora Back End",
]


class SimplePipeline:
    """
    Pipeline simplificado para coleta de vagas.
    
    Estratégia:
    1. Busca nas plataformas (qualquer empresa que atenda critérios)
    2. Busca nas empresas foco (vai direto nas páginas de carreira)
    3. Unifica e deduplica
    4. Filtra (remoto + Brasil + data)
    5. Salva JSON local
    6. Notifica via Telegram
    """
    
    def __init__(
        self,
        mode: str = "test",
        output_dir: str = "data/jobs",
    ):
        """
        Args:
            mode: "test" (7 dias) ou "prod" (24h)
            output_dir: Diretório para salvar vagas
        """
        self.mode = mode
        self.days = 7 if mode == "test" else 1
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Arquivo de vagas já enviadas
        self.sent_file = self.output_dir / "sent_jobs.json"
        self._load_sent_jobs()
        
    def _load_sent_jobs(self):
        """Carrega lista de vagas já enviadas."""
        if self.sent_file.exists():
            with open(self.sent_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.sent_jobs = set(data.get("sent", []))
        else:
            self.sent_jobs = set()
    
    def _save_sent_jobs(self):
        """Salva lista de vagas já enviadas."""
        with open(self.sent_file, "w", encoding="utf-8") as f:
            json.dump({
                "sent": list(self.sent_jobs),
                "updated_at": datetime.now().isoformat(),
            }, f, indent=2)
    
    def _generate_job_id(self, job: dict) -> str:
        """Gera ID único para uma vaga."""
        platform = job.get("_metadata", {}).get("platform", "unknown")
        company = job.get("company", job.get("_metadata", {}).get("company", "unknown"))
        title = job.get("title", job.get("name", "unknown"))
        job_id = job.get("id", job.get("job_id", ""))
        
        # Normaliza
        company = company.lower().replace(" ", "_")[:30]
        title = title.lower().replace(" ", "_")[:30]
        
        return f"{platform}:{company}:{title}:{job_id}"
    
    async def search_platforms(self) -> list[dict]:
        """
        Busca vagas nas plataformas (qualquer empresa).
        
        Busca por título de vaga, retorna qualquer empresa que tenha.
        """
        all_jobs = []
        
        # Gupy - maior plataforma BR
        try:
            scraper = GupyAPIScraper(output_dir="data/jobs/raw")
            # Busca por cada título
            for title in ["Data Engineer", "Analista de Dados", "Cientista de Dados"]:
                jobs = await self._search_gupy_by_title(scraper, title)
                all_jobs.extend(jobs)
        except Exception as e:
            logger.error("Erro na busca Gupy", error=str(e))
        
        logger.info(f"Plataformas: {len(all_jobs)} vagas brutas coletadas")
        return all_jobs
    
    async def _search_gupy_by_title(self, scraper: GupyAPIScraper, title: str) -> list[dict]:
        """Busca vagas por título na Gupy (qualquer empresa)."""
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # API de busca geral da Gupy (v1 é a que funciona!)
                url = "https://portal.api.gupy.io/api/v1/jobs"
                params = {
                    "jobName": title,  # Parâmetro correto para v1
                    "limit": 50,
                    "isRemoteWork": "true",  # Filtro de remoto para v1
                }
                
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    jobs = data.get("data", [])
                    
                    # Adiciona metadata
                    for job in jobs:
                        job["_metadata"] = {
                            "platform": "gupy",
                            "company": job.get("careerPageName", ""),
                            "scraped_at": datetime.now().isoformat(),
                        }
                        job["title"] = job.get("name", "")
                        job["company"] = job.get("careerPageName", "")
                        job["url"] = job.get("jobUrl", "")
                    
                    return jobs
        except Exception as e:
            logger.warning(f"Erro busca Gupy por {title}", error=str(e))
        
        return []
    
    async def search_focus_companies(self) -> list[dict]:
        """
        Busca vagas nas empresas foco (vai direto na página de carreira).
        
        Usa a lista de empresas em companies.py.
        """
        all_jobs = []
        
        # Greenhouse - API mais confiável
        try:
            scraper = GreenhouseAPIScraper(output_dir="data/jobs/raw")
            companies = get_companies_by_ats(ATSType.GREENHOUSE)
            
            for company in companies:
                jobs = await scraper.fetch_jobs(
                    company,
                    remote_only=True,
                    brazil_only=True,
                )
                all_jobs.extend(jobs)
                await asyncio.sleep(0.5)  # Rate limiting
                
        except Exception as e:
            logger.error("Erro no Greenhouse", error=str(e))
        
        # Lever
        try:
            scraper = LeverAPIScraper(output_dir="data/jobs/raw")
            companies = get_companies_by_ats(ATSType.LEVER)
            
            for company in companies:
                jobs = await scraper.fetch_jobs(company)
                all_jobs.extend(jobs)
                await asyncio.sleep(0.5)
                
        except Exception as e:
            logger.error("Erro no Lever", error=str(e))
        
        # SmartRecruiters
        try:
            scraper = SmartRecruitersAPIScraper(output_dir="data/jobs/raw")
            companies = get_companies_by_ats(ATSType.SMARTRECRUITERS)
            
            for company in companies:
                jobs = await scraper.fetch_jobs(company)
                all_jobs.extend(jobs)
                await asyncio.sleep(0.5)
                
        except Exception as e:
            logger.error("Erro no SmartRecruiters", error=str(e))
        
        logger.info(f"Empresas foco: {len(all_jobs)} vagas brutas coletadas")
        return all_jobs
    
    def deduplicate(self, jobs: list[dict]) -> list[dict]:
        """Remove vagas duplicadas baseado no ID gerado."""
        seen = set()
        unique = []
        
        for job in jobs:
            job_id = self._generate_job_id(job)
            if job_id not in seen:
                seen.add(job_id)
                job["_job_id"] = job_id
                unique.append(job)
        
        logger.info(f"Deduplicacao: {len(jobs)} -> {len(unique)}")
        return unique
    
    def filter_jobs(self, jobs: list[dict]) -> list[dict]:
        """
        Aplica filtros: remoto + Brasil + data + título.
        """
        valid = []
        stats = {
            "not_remote": 0,
            "not_brazil": 0,
            "old": 0,
            "wrong_title": 0,
        }
        
        for job in jobs:
            # 1. Verifica título
            title = job.get("title", job.get("name", ""))
            normalized_title = normalize_job_title(title)
            
            # Aceita apenas títulos de interesse
            valid_titles = [
                "Data Engineer", "Data Scientist", "Data Analyst",
                "Full Stack Developer", "Back End Developer",
                "Machine Learning Engineer", "Analytics Engineer",
                "BI Analyst", "Data Architect",
            ]
            
            if normalized_title == "Outro":
                # Verifica se o título contém keywords
                title_lower = title.lower()
                if not any(kw in title_lower for kw in ["data", "dados", "full stack", "backend", "back end"]):
                    stats["wrong_title"] += 1
                    continue
            
            # 2. Verifica remoto + Brasil + data
            is_valid, reason = is_valid_job_full(
                job,
                empresa_validada=True,  # Empresas da lista são validadas
                days=self.days,
                check_date=True,
            )
            
            if not is_valid:
                if "remoto" in reason.lower():
                    stats["not_remote"] += 1
                elif "brasil" in reason.lower():
                    stats["not_brazil"] += 1
                elif "antiga" in reason.lower():
                    stats["old"] += 1
                continue
            
            # 3. Verifica se já foi enviada
            job_id = job.get("_job_id", self._generate_job_id(job))
            if job_id in self.sent_jobs:
                continue
            
            # Adiciona normalização
            job["titulo_normalizado"] = normalized_title
            job["senioridade"] = normalize_seniority(title)
            valid.append(job)
        
        logger.info(
            "Filtragem concluída",
            total=len(jobs),
            validas=len(valid),
            **stats
        )
        return valid
    
    def save_jobs(self, jobs: list[dict]) -> Path:
        """Salva vagas válidas em JSON."""
        if not jobs:
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"vagas_{timestamp}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({
                "collected_at": datetime.now().isoformat(),
                "mode": self.mode,
                "days_filter": self.days,
                "total_jobs": len(jobs),
                "jobs": jobs,
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Vagas salvas em {filepath}")
        return filepath
    
    async def notify(self, jobs: list[dict], dry_run: bool = False) -> int:
        """
        Envia vagas para Telegram.
        
        Returns:
            Número de vagas enviadas com sucesso
        """
        if not jobs:
            logger.info("Nenhuma vaga para notificar")
            return 0
        
        if dry_run:
            logger.info(f"[DRY-RUN] {len(jobs)} vagas seriam enviadas")
            for job in jobs[:5]:
                print(f"  - {job.get('title', 'N/A')} @ {job.get('company', 'N/A')}")
            if len(jobs) > 5:
                print(f"  ... e mais {len(jobs) - 5} vagas")
            return 0
        
        try:
            from src.notifications.telegram import TelegramNotifier, JobNotification
            
            notifier = TelegramNotifier()
            sent_count = 0
            
            for job in jobs:
                notification = JobNotification(
                    title=job.get("titulo_normalizado", job.get("title", "N/A")),
                    company=job.get("company", "N/A"),
                    location="Remoto - Brasil",
                    work_model="Remoto",
                    url=job.get("url", ""),
                    platform=job.get("_metadata", {}).get("platform", "N/A"),
                    skills=[],
                )
                
                success = await notifier.send_job_alert(notification, skip_if_seen=False)
                
                if success:
                    # Marca como enviada
                    job_id = job.get("_job_id", self._generate_job_id(job))
                    self.sent_jobs.add(job_id)
                    sent_count += 1
                
                # Rate limiting
                await asyncio.sleep(1)
            
            # Salva lista de enviadas
            self._save_sent_jobs()
            
            logger.info(f"Telegram: {sent_count}/{len(jobs)} vagas enviadas")
            return sent_count
            
        except Exception as e:
            logger.error(f"Erro ao notificar Telegram", error=str(e))
            return 0
    
    async def run(
        self,
        platforms: bool = True,
        companies: bool = True,
        dry_run: bool = False,
    ) -> dict:
        """
        Executa o pipeline completo.
        
        Args:
            platforms: Buscar em plataformas (qualquer empresa)
            companies: Buscar em empresas foco
            dry_run: Preview sem enviar
            
        Returns:
            Estatísticas da execução
        """
        logger.info(f"Iniciando pipeline (modo={self.mode}, dias={self.days})")
        
        all_jobs = []
        
        # 1. Coleta
        if platforms:
            platform_jobs = await self.search_platforms()
            all_jobs.extend(platform_jobs)
        
        if companies:
            company_jobs = await self.search_focus_companies()
            all_jobs.extend(company_jobs)
        
        if not all_jobs:
            logger.warning("Nenhuma vaga coletada")
            return {"total": 0, "valid": 0, "sent": 0}
        
        # 2. Deduplica
        unique_jobs = self.deduplicate(all_jobs)
        
        # 3. Filtra
        valid_jobs = self.filter_jobs(unique_jobs)
        
        # 4. Salva
        if valid_jobs:
            self.save_jobs(valid_jobs)
        
        # 5. Notifica
        sent = await self.notify(valid_jobs, dry_run=dry_run)
        
        return {
            "total": len(all_jobs),
            "unique": len(unique_jobs),
            "valid": len(valid_jobs),
            "sent": sent,
        }


async def main():
    parser = argparse.ArgumentParser(description="Pipeline simplificado de vagas")
    parser.add_argument(
        "--mode", choices=["test", "prod"], default="test",
        help="Modo de execução: test (7 dias) ou prod (24h)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview sem enviar para Telegram"
    )
    parser.add_argument(
        "--platforms-only", action="store_true",
        help="Buscar apenas em plataformas"
    )
    parser.add_argument(
        "--companies-only", action="store_true",
        help="Buscar apenas em empresas foco"
    )
    args = parser.parse_args()
    
    # Determina o que buscar
    platforms = True
    companies = True
    
    if args.platforms_only:
        companies = False
    elif args.companies_only:
        platforms = False
    
    # Executa
    pipeline = SimplePipeline(mode=args.mode)
    stats = await pipeline.run(
        platforms=platforms,
        companies=companies,
        dry_run=args.dry_run,
    )
    
    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO DA EXECUÇÃO")
    print("=" * 60)
    print(f"Modo: {args.mode} ({pipeline.days} dias)")
    print(f"Total coletadas: {stats['total']}")
    print(f"Após deduplicação: {stats.get('unique', 'N/A')}")
    print(f"Válidas (remoto+Brasil+data): {stats['valid']}")
    print(f"Enviadas ao Telegram: {stats['sent']}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
