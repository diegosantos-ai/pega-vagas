
# 🎯 Pega-Vagas

Pipeline de Engenharia de Dados para coleta, validação e notificação de vagas de tecnologia **100% remotas** para o Brasil.

## 📋 Visão Geral

Pipeline automatizado para:
- Coletar vagas de APIs (Gupy, Greenhouse, etc)
- Filtrar por remoto, Brasil, título e qualidade (QualityGate)
- Deduplicar e validar links
- Notificar apenas vagas relevantes via Telegram

Arquitetura baseada em **Medallion** (Bronze/Silver/Gold) + QualityGate:

```
API Scraping → Bronze (raw JSON) → Silver (LLM/validação) → QualityGate → Telegram
```

## 🚀 Quick Start

```bash
# 1. Clone e instale
git clone https://github.com/seu-usuario/pega-vagas.git
cd pega-vagas
pip install -e ".[dev]"

# 2. Instale o navegador (opcional)
playwright install firefox

# 3. Configure variáveis (.env)
cp .env.example .env
# Edite .env com suas chaves de API e Telegram

# 4. Execute pipeline completo
python -m src.pipeline run

# 5. (Opcional) Teste etapas isoladas
python -m src.pipeline bronze --query "Data Engineer"
python -m src.pipeline silver
python -m src.pipeline gold
python -m src.pipeline notify
```


## 🛠️ Tecnologias & Componentes

| Componente     | Tecnologia/Arquivo         | Descrição |
|----------------|---------------------------|-----------|
| Scraping       | API (Gupy, Greenhouse)    | Coleta rápida e confiável |
| Validação      | QualityGate (src/quality_gate.py) | Filtra vagas não-remotas, links quebrados, baixa relevância |
| Orquestração   | src/pipeline.py           | Pipeline principal (bronze/silver/gold/notify) |
| Notificação    | Telegram Bot API          | Envio de vagas validadas |
| Processamento  | DuckDB, Parquet           | OLAP local, exportação |
| Logging        | structlog                 | Logs estruturados |
| Configuração   | dotenv (.env)             | Tokens e segredos |


## 📊 Arquitetura do Pipeline

### 🥉 Bronze (Raw)
- Dados brutos coletados das APIs (JSON)
- Metadados de coleta

### 🥈 Silver (LLM/Validação)
- Dados estruturados via LLM
- Validados por schema Pydantic

### 🛡️ QualityGate
- Filtro de vagas não-remotas, links quebrados, irrelevantes
- Implementado em src/quality_gate.py

### 🥇 Gold (Curated)
- Star Schema dimensional (DuckDB)
- Exportação para Parquet

### 📲 Notificação
- Apenas vagas aprovadas pelo QualityGate são enviadas ao Telegram

## 📈 Análises Disponíveis

```sql
-- Top skills mais demandadas
SELECT * FROM vw_top_skills LIMIT 10;

-- Salários por cargo e senioridade
SELECT * FROM vw_vagas_por_titulo;

-- Skills que mais aparecem com Python
SELECT * FROM vw_skills_com_python;

-- Distribuição geográfica
SELECT * FROM vw_vagas_por_regiao;
```

## ⚙️ Configuração

### Variáveis de Ambiente

```bash
# LLM (escolha um)
GOOGLE_API_KEY=...      # Gemini (recomendado)
OPENAI_API_KEY=...      # OpenAI

# Proxy Residencial (opcional mas recomendado)
PROXY_URL=http://user:pass@host:port

# Rate Limiting
SCRAPE_DELAY_MIN=2
SCRAPE_DELAY_MAX=5
MAX_JOBS_PER_RUN=100
```

### GitHub Secrets (para Actions)

- `GOOGLE_API_KEY`: Chave da API Gemini
- `PROXY_URL`: URL do proxy residencial
- `ALERT_WEBHOOK_URL`: (opcional) Webhook para alertas


## 📁 Estrutura do Projeto

```
pega-vagas/
├── src/
│   ├── pipeline.py           # Pipeline principal (bronze/silver/gold/notify)
│   ├── quality_gate.py       # QualityGate: filtro de vagas
│   ├── notifications/        # Telegram notifier
│   ├── ingestion/            # Scrapers de API
│   ├── config/               # Empresas e settings
│   ├── processing/           # LLM extraction
│   ├── analytics/            # DuckDB transforms
│   └── schemas/              # Modelos Pydantic
├── data/
│   ├── bronze/               # Dados brutos
│   ├── silver/               # Dados processados
│   └── gold/                 # Star Schema/Parquet
└── tests/                    # Testes automatizados
```


## ⚖️ Conformidade LGPD

Este pipeline foi desenhado com **Privacy by Design**:

- ✅ Coleta apenas dados públicos (sem login)
- ✅ Minimização de dados pessoais
- ✅ Anonimização automática de recrutadores
- ✅ Não coleta dados sensíveis
- ✅ Respeita rate limiting das plataformas

## 📄 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.

---

Desenvolvido com ❤️ para a comunidade de dados brasileira.

---

### ℹ️ Observações
- O QualityGate bloqueia vagas híbridas, links quebrados, títulos irrelevantes e oportunidades fora do Brasil.
- Só vagas 100% remotas e relevantes chegam ao Telegram.
- Veja agents.md para regras detalhadas de filtragem.
