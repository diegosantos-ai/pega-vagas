# Pega Vagas - Contexto para Agentes IA

> **Última atualização:** 2026-01-24  
> **Versão:** 2.0

Este documento define regras e contexto para sessões futuras de desenvolvimento.

---

## 🎯 Objetivo do Projeto

Coletar vagas de **Data Engineering** e áreas relacionadas de empresas relevantes para o mercado brasileiro, com foco em oportunidades **100% remotas** para profissionais baseados no **Brasil**.

### Títulos de vagas monitorados:
- Data Engineer / Engenheiro de Dados
- Analytics Engineer / Engenheiro de Analytics
- Data Analyst / Analista de Dados
- Data Scientist / Cientista de Dados
- AI/ML Engineer / Engenheiro de IA
- Automation Engineer / Engenheiro de Automação

---

## 📁 Arquitetura do Projeto

```
pega-vagas/
├── .github/workflows/     # GitHub Actions (CI/CD)
│   ├── scrape.yaml        # Pipeline de coleta (a cada 3h)
│   └── ci.yaml            # Testes e lint em PRs
├── src/
│   ├── pipeline.py        # Pipeline principal (USE ESTE)
│   ├── quality_gate.py    # Filtro de qualidade obrigatório
│   ├── notifications/     # Telegram notifier
│   ├── ingestion/         # Scrapers de API
│   ├── config/            # Empresas e settings
│   ├── processing/        # LLM extraction
│   ├── analytics/         # DuckDB transforms
│   └── schemas/           # Modelos Pydantic
├── data/
│   ├── bronze/            # Dados brutos (JSON)
│   ├── silver/            # Dados processados
│   ├── gold/              # Star Schema/Parquet
│   └── cache/             # Cache de deduplicação
├── tests/                 # Testes automatizados
├── config.yaml            # Configurações centralizadas
└── pyproject.toml         # Dependências Python
```

---

## 🔄 Pipeline de Execução

```mermaid
flowchart LR
    A[Bronze] --> B[Silver]
    B --> C[QualityGate]
    C --> D[Gold]
    D --> E[Telegram]
    
    A -- "APIs: Gupy, Greenhouse" --> A
    B -- "LLM: Gemini" --> B
    C -- "Filtros: Remoto, Brasil" --> C
    D -- "DuckDB + Parquet" --> D
```

### Comandos do Pipeline

```bash
# Pipeline completo
python -m src.pipeline run

# Etapas isoladas
python -m src.pipeline bronze --query "Data Engineer" --max-jobs 50
python -m src.pipeline silver
python -m src.pipeline gold
python -m src.pipeline notify

# Exportar dados
python -m src.pipeline export
```

---

## 🔌 GitHub Actions

### Workflows Disponíveis

| Workflow | Trigger | Descrição |
|----------|---------|-----------|
| `scrape.yaml` | Cron (3h) / Manual | Pipeline completo de coleta |
| `ci.yaml` | Push/PR | Testes, lint, type-check |

### Executar Manualmente

1. Vá em **Actions** no GitHub
2. Selecione **Job Scraping Pipeline**
3. Clique em **Run workflow**
4. Configure parâmetros opcionais (query, max_jobs, dry_run)

### Secrets Necessários

| Secret | Descrição | Onde Obter |
|--------|-----------|------------|
| `GOOGLE_API_KEY` | API Gemini | [Google AI Studio](https://aistudio.google.com/apikey) |
| `TELEGRAM_BOT_TOKEN` | Token do bot | [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_CHAT_ID` | ID do grupo | `python get_group_id.py` |
| `PROXY_URL` | Proxy residencial | SmartProxy, BrightData, etc. |

---

## 📊 Fontes de Dados

### APIs Funcionais

| Fonte | Tipo | Status | Vagas/exec |
|-------|------|--------|------------|
| **Gupy API** | API v1 | ✅ Funcionando | ~10-20 |
| **Greenhouse API** | API pública | ✅ Funcionando | ~100-150 |
| Lever API | API pública | ❌ Quebrado | 0 |
| SmartRecruiters | API pública | ⚠️ Sem vagas BR | 0 |

### Endpoints de API

**Gupy (v1):**
```python
url = "https://portal.api.gupy.io/api/v1/jobs"
params = {"jobName": "Data Engineer", "limit": 50, "isRemoteWork": "true"}
```

**Greenhouse:**
```python
url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs"
# token = slug da empresa (ex: "quintoandar", "gympass")
```

---

## 🛡️ QualityGate - Regras de Filtragem

### ✅ Padrões REMOTOS (válidos)
- `100% remoto`, `fully remote`, `full remote`
- `remote first`, `trabalho remoto`, `home office`
- `anywhere in brazil`, `work from anywhere`

### ❌ Padrões REJEITADOS (inválidos)
- `híbrido`, `hybrid`, `presencial`, `on-site`
- `dias no escritório`, `days in office`
- `residir em`, `must live in`, `requires relocation`

### Pontuação Mínima
- Score >= 50 para notificação
- Ver `config.yaml` para detalhes de pontuação

---

## ⚙️ Configuração

### Variáveis de Ambiente (.env)

```bash
# LLM (obrigatório)
GOOGLE_API_KEY=sua_chave_gemini

# Telegram (obrigatório)
TELEGRAM_BOT_TOKEN=seu_token_bot
TELEGRAM_CHAT_ID=-1001234567890

# Proxy (recomendado)
PROXY_URL=http://user:pass@host:port

# Modelo LLM
LLM_MODEL=gemini-2.0-flash
```

### config.yaml

Arquivo centralizado com:
- Termos de busca por categoria
- Regras do QualityGate
- Agendamento
- Configurações de scraping
- Parâmetros de LLM
- Formato de notificações

---

## 🐛 Problemas Conhecidos

### 1. Links do Telegram podem dar erro
- **Causa:** Caracteres especiais na URL
- **Arquivo:** `src/notifications/telegram.py`
- **Status:** Em investigação

### 2. Greenhouse - Tokens desatualizados
- **Empresas afetadas:** Creditas, Hotmart, Loggi, Neoway, CI&T
- **Solução:** Pesquisar tokens corretos nas páginas de carreira

### 3. Lever API retorna 404
- **Causa:** Empresas migraram para outros ATS
- **Status:** Removido do pipeline

### 4. Gupy Browser Scraper - CAPTCHA
- **Causa:** Detecção de automação
- **Solução:** Usar API v1 em vez de browser

---

## 📝 Notas para o Agente

1. **Pipeline principal:** Use `src/pipeline.py` - orquestra todas as etapas
2. **QualityGate:** Toda vaga passa por `src/quality_gate.py` antes de notificar
3. **API Gupy:** Use `/api/v1/jobs` com `jobName` e `isRemoteWork`
4. **Não usar browser scraping** para Gupy - causa CAPTCHA
5. **Encoding:** Use `encoding='utf-8'` ao ler/escrever arquivos
6. **GitHub Actions:** Ver `.github/workflows/` para automação
7. **Secrets:** Nunca commitar tokens - usar GitHub Secrets

---

## 🔄 Histórico de Alterações

| Data | Alteração |
|------|-----------|
| 2026-01-24 | v2.0 - Adicionado contexto de GitHub Actions e CI/CD |
| 2026-01-16 | v1.0 - Criação inicial do documento |
| 2026-01-16 | Corrigida API Gupy (v3→v1) |
| 2026-01-16 | Checkpoint: Pipeline funcional |

---

## 🚀 Próximos Passos

- [ ] Implementar cache de deduplicação entre execuções
- [ ] Corrigir tokens Greenhouse desatualizados
- [ ] Adicionar mais fontes de dados (Indeed, Glassdoor)
- [ ] Dashboard de métricas (Streamlit)
- [ ] Alertas de falha via email
