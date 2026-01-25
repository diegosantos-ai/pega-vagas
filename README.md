<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen" alt="PRs Welcome">
</p>

<h1 align="center">🎯 Pega-Vagas</h1>

<p align="center">
  <strong>Pipeline de Engenharia de Dados para coleta, validação e notificação de vagas de tecnologia 100% remotas para o Brasil.</strong>
</p>

---

## 📋 Visão Geral

**Pega-Vagas** é um pipeline automatizado que:

- 🔍 **Coleta** vagas de múltiplas APIs (Gupy, Greenhouse, etc.)
- 🤖 **Processa** descrições com LLM (Gemini) para extração estruturada
- 🛡️ **Filtra** vagas não-remotas, híbridas ou irrelevantes (QualityGate)
- 📲 **Notifica** apenas vagas relevantes via Telegram
- 📊 **Armazena** dados em formato analítico (DuckDB + Parquet)

### Arquitetura Medallion

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Bronze    │───▶│   Silver    │───▶│ QualityGate │───▶│    Gold     │───▶│  Telegram   │
│  (Raw JSON) │    │ (LLM Parse) │    │  (Filtros)  │    │  (DuckDB)   │    │(Notificação)│
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

---

## 🚀 Quick Start

### 1. Clone e Instale

```bash
git clone https://github.com/diegosantos-ai/pega-vagas.git
cd pega-vagas
pip install -e ".[dev]"
```

### 2. Configure Variáveis de Ambiente

```bash
cp .env.example .env
# Edite .env com suas chaves
```

**Variáveis obrigatórias:**

| Variável | Descrição |
|----------|-----------|
| `GOOGLE_API_KEY` | Chave da API Gemini ([obter aqui](https://aistudio.google.com/apikey)) |
| `TELEGRAM_BOT_TOKEN` | Token do bot ([@BotFather](https://t.me/BotFather)) |
| `TELEGRAM_CHAT_ID` | ID do grupo/canal de notificações |

### 3. Execute o Pipeline

```bash
# Pipeline completo
python -m src.pipeline run

# Ou etapas isoladas
python -m src.pipeline bronze --query "Data Engineer"
python -m src.pipeline silver
python -m src.pipeline gold
python -m src.pipeline notify
```

---

## 🔄 GitHub Actions (Automação)

O pipeline executa automaticamente a cada 3 horas via GitHub Actions.

### Configurar Secrets

Vá em **Settings > Secrets and variables > Actions** e adicione:

| Secret | Valor |
|--------|-------|
| `GOOGLE_API_KEY` | Sua chave Gemini |
| `TELEGRAM_BOT_TOKEN` | Token do bot |
| `TELEGRAM_CHAT_ID` | ID do grupo |
| `PROXY_URL` | (Opcional) Proxy residencial |

### Executar Manualmente

1. Vá em **Actions > Job Scraping Pipeline**
2. Clique em **Run workflow**
3. Configure parâmetros (query, max_jobs, dry_run)
4. Clique em **Run workflow**

---

## 🛠️ Tecnologias

| Componente | Tecnologia | Descrição |
|------------|------------|-----------|
| **Scraping** | httpx + APIs | Coleta rápida e confiável |
| **LLM** | Google Gemini | Extração estruturada de dados |
| **Validação** | QualityGate + Pydantic | Filtros de qualidade |
| **Storage** | DuckDB + Parquet | OLAP local |
| **Notificação** | Telegram Bot API | Envio de vagas |
| **CI/CD** | GitHub Actions | Automação completa |
| **Logging** | structlog | Logs estruturados |

---

## 📁 Estrutura do Projeto

```
pega-vagas/
├── .github/workflows/     # GitHub Actions
│   └── scrape.yaml        # Pipeline automático
├── src/
│   ├── pipeline.py        # Orquestrador principal
│   ├── quality_gate.py    # Filtros de qualidade
│   ├── notifications/     # Telegram notifier
│   ├── ingestion/         # Scrapers de API
│   ├── config/            # Empresas e settings
│   ├── processing/        # LLM extraction
│   ├── analytics/         # DuckDB transforms
│   └── schemas/           # Modelos Pydantic
├── data/
│   ├── bronze/            # Dados brutos
│   ├── silver/            # Dados processados
│   └── gold/              # Star Schema
├── tests/                 # Testes automatizados
├── config.yaml            # Configurações
├── agents.md              # Contexto para agentes IA
└── pyproject.toml         # Dependências
```

---

## 📊 Fontes de Dados

| Plataforma | Método | Status |
|------------|--------|--------|
| **Gupy** | API v1 | ✅ Funcionando |
| **Greenhouse** | API pública | ✅ Funcionando |
| Lever | API | ❌ Migrado |
| SmartRecruiters | API | ⚠️ Sem vagas BR |

### Empresas Monitoradas

**Gupy:** BTG Pactual, C6 Bank, Banco Inter, PicPay, iFood, Globo, Magazine Luiza, Ambev, Localiza, B3, e mais...

**Greenhouse:** QuintoAndar, Gympass (Wellhub), Wildlife, ThoughtWorks, VTEX, Loft, Cloudwalk

---

## 🛡️ QualityGate

O QualityGate filtra automaticamente vagas que não atendem aos critérios:

### ✅ Aceitas
- 100% remoto / Full remote / Remote first
- Trabalho remoto / Home office
- Anywhere in Brazil

### ❌ Rejeitadas
- Híbrido / Hybrid
- Presencial / On-site
- X dias no escritório
- Residir em [cidade específica]

---

## 📈 Análises Disponíveis

Após executar o pipeline, você pode fazer queries analíticas:

```sql
-- Top skills mais demandadas
SELECT * FROM vw_top_skills LIMIT 10;

-- Vagas por título e senioridade
SELECT * FROM vw_vagas_por_titulo;

-- Skills que aparecem com Python
SELECT * FROM vw_skills_com_python;

-- Distribuição por região
SELECT * FROM vw_vagas_por_regiao;
```

---

## 🧪 Testes

```bash
# Executar testes
pytest tests/ -v

# Com coverage
pytest tests/ --cov=src

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

---

## ⚖️ Conformidade LGPD

Este pipeline foi desenhado com **Privacy by Design**:

- ✅ Coleta apenas dados públicos (sem login)
- ✅ Minimização de dados pessoais
- ✅ Anonimização automática de recrutadores
- ✅ Não coleta dados sensíveis
- ✅ Respeita rate limiting das plataformas

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Veja [CONTRIBUTING.md](CONTRIBUTING.md) para detalhes.

```bash
# Setup de desenvolvimento
pip install -e ".[dev]"

# Antes de commitar
ruff check src/ tests/
pytest tests/ -v
```

---

## 📄 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.

---

## 📞 Suporte

- 📖 **Documentação:** [agents.md](agents.md) - Contexto técnico detalhado
- 🐛 **Issues:** [GitHub Issues](https://github.com/diegosantos-ai/pega-vagas/issues)
- 💬 **Discussões:** [GitHub Discussions](https://github.com/diegosantos-ai/pega-vagas/discussions)

---

<p align="center">
  Desenvolvido com ❤️ para a comunidade de dados brasileira.
</p>
