# Pega Vagas - Contexto para Agentes IA

Este documento define regras e contexto para sessões futuras de desenvolvimento.

---

## 🎯 Objetivo do Projeto

Coletar vagas de **Data Engineering** de empresas relevantes para o mercado brasileiro, com foco em oportunidades **100% remotas** para profissionais baseados no **Brasil**.

**Títulos de vagas monitorados:**
- Data Engineer / Engenheiro de Dados
- Analista de Dados / Data Analyst
- Cientista de Dados / Data Scientist

---


## 📁 Arquitetura Atual (Checkpoint 2026-01-16)

### Pipeline Principal: `src/pipeline.py`

Pipeline orquestrado em etapas:
1. **Bronze**: Coleta vagas de APIs (Gupy, Greenhouse, etc)
2. **Silver**: Processa e estrutura dados via LLM
3. **QualityGate**: Filtra vagas não-remotas, links quebrados, irrelevantes (src/quality_gate.py)
4. **Gold**: Carrega dados em DuckDB/Parquet
5. **Notifica** via Telegram (apenas vagas aprovadas)

```bash
# Pipeline completo
python -m src.pipeline run

# Etapas isoladas
python -m src.pipeline bronze --query "Data Engineer"
python -m src.pipeline silver
python -m src.pipeline gold
python -m src.pipeline notify
```

### Fontes de Dados Funcionais

| Fonte | Tipo | Status | Vagas/exec |
|-------|------|--------|------------|
| **Gupy API** | API v1 | ✅ Funcionando | ~10 |
| **Greenhouse API** | API pública | ✅ Funcionando | ~125 |
| Lever API | API pública | ❌ Quebrado (404) | 0 |
| SmartRecruiters | API pública | ⚠️ Sem vagas | 0 |

### APIs Descobertas

**Gupy (FUNCIONA):**
```python
# API v1 - endpoint correto
url = "https://portal.api.gupy.io/api/v1/jobs"
params = {
    "jobName": "Data Engineer",  # Termo de busca
    "limit": 50,
    "isRemoteWork": "true"  # Filtro de remoto
}
# Retorna JSON com data[]
```

**Gupy (NÃO FUNCIONA - deprecada):**
```python
# API v3 - NÃO USAR, retorna 404
url = "https://portal.api.gupy.io/api/job-search/v3/jobs"  # QUEBRADA
```

**Greenhouse:**
```python
url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs"
# Token = slug da empresa (ex: "quintoandar", "gympass")
```


### Estrutura de Diretórios

```
pega-vagas/
├── src/
│   ├── pipeline.py           # Pipeline principal (USE ESTE)
│   ├── quality_gate.py       # QualityGate: filtro obrigatório
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

---

## 📍 Definição: Modalidade REMOTA

### ✅ O que é considerado REMOTO (válido):
- **100% Home Office** - trabalho totalmente remoto
- **Remote First** - empresa prioriza remoto
- **Anywhere in Brazil** - qualquer lugar do Brasil
- **Full Remote** / **Fully Remote**

### ❌ O que NÃO é considerado REMOTO (inválido):
- **Híbrido** - exige presença X dias por semana/mês
- **Remote with occasional office visits** - não é 100% remoto
- **Presencial com home office eventual** - não é remoto
- **Flex** - geralmente significa híbrido

### Regex de Filtragem (implementado em simple_pipeline.py):
```python
REMOTE_NEGATIVE = [
    r"\bh[íi]brido\b",
    r"\bhybrid\b",
    r"\bpresencial\b",
    r"\bon[\s-]?site\b",
    r"\b\d+\s*(dias?|days?)\s*(por\s*)?(semana|week|m[êe]s|month)",
]
```

---

## 🇧🇷 Definição: Empresa com Operação no BRASIL

### ✅ Empresas validadas (em `companies.py`):
Todas as empresas listadas em `src/config/companies.py` já foram validadas como tendo operação no Brasil.

### Empresas por ATS:

**GUPY (20 empresas):**
BTG Pactual, C6 Bank, Banco Inter, PicPay, PagBank, Neon, Will Bank, iFood, Globo, TOTVS, RD Station, Magazine Luiza, Ambev, Localiza, Suzano, B3, Stefanini, Semantix, BHS

**GREENHOUSE (12 empresas - 7 funcionando):**
- ✅ Funcionando: QuintoAndar, Gympass (Wellhub), Wildlife, ThoughtWorks, VTEX, Loft, Cloudwalk
- ❌ Token errado: Creditas, Hotmart, Loggi, Neoway, CI&T

**LEVER (5 empresas - todas quebradas):**
Nubank, Stone, PagSeguro, Movile, Olist - **Migraram de ATS**

---

## 🔧 Configuração

### Variáveis de Ambiente (.env):
```bash
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=-1003574574884  # Grupo/canal de destino
```

### Dependências principais:
```
httpx          # Requisições HTTP async
structlog      # Logging estruturado
python-dotenv  # Carregar .env
playwright     # Browser automation (backup)
tenacity       # Retry logic
```

---

## 🐛 Problemas Conhecidos

### 1. Links do Telegram podem dar erro
**Sintoma:** Link clicável não abre a vaga
**Causa provável:** Caracteres especiais na URL (=, ?) ou encoding
**Investigação:** Testar com HTML vs Markdown no Telegram
**Arquivo:** `src/notifications/telegram.py` - método `_format_job_message()`

### 2. Greenhouse - 5 empresas com token errado
**Empresas:** Creditas, Hotmart, Loggi, Neoway, CI&T
**Causa:** Tokens em `companies.py` estão desatualizados
**Solução:** Pesquisar tokens corretos nas páginas de carreira

### 3. Lever API retorna 404
**Causa:** Empresas migraram para outros ATS
**Solução:** Remover ou atualizar essas empresas

### 4. Gupy Browser Scraper - CAPTCHA
**Causa:** Gupy detecta automação e mostra CAPTCHA
**Solução:** Usar API v1 em vez de browser scraping

---

## 📊 Métricas de Execução (2026-01-16)

```
Total coletadas: 134
- Gupy: 9
- Greenhouse: 125

Após deduplicação: 133
Válidas (remoto+Brasil+data): 5
Enviadas ao Telegram: 5

Descartadas:
- Não remoto (híbrido): 30
- Título errado: 90
- Outros países: 0
- Antigas: 0
```

---

## 🔄 Histórico de Alterações

| Data | Alteração |
|------|-----------|
| 2026-01-16 | Criação inicial do documento |
| 2026-01-16 | Corrigida API Gupy (v3→v1) |
| 2026-01-16 | Checkpoint: Pipeline funcional com 5 vagas enviadas |
| 2026-01-16 | Identificado problema de links no Telegram (em investigação) |

---

## 📝 Notas para o Agente


1. **Pipeline principal:** Use `src/pipeline.py` - orquestra todas as etapas
2. **QualityGate:** Toda vaga passa por `src/quality_gate.py` antes de ser notificada
3. **API Gupy:** Use `/api/v1/jobs` com `jobName` e `isRemoteWork`
4. **Não usar browser scraping** para Gupy - causa CAPTCHA
5. **Sempre testar** com `--dry-run` antes de enviar ao Telegram (se implementar)
6. **Encoding:** Use `encoding='utf-8'` ao ler/escrever arquivos no Windows
7. **Caracteres especiais:** Evitar → e outros Unicode em logs (problema CP1252)

---

## 🚀 Próximos Passos

1. [ ] **Resolver links do Telegram** - investigar se é Markdown vs HTML
2. [ ] **Corrigir tokens Greenhouse** - Creditas, Hotmart, Loggi, Neoway, CI&T
3. [ ] **Expandir busca Gupy** - adicionar mais termos de busca
4. [ ] **Agendar execução** - Task Scheduler ou cron
5. [ ] **Monitoramento** - alertas se pipeline falhar
6. [ ] **Aprimorar QualityGate** - ajustar score, regras e logging
