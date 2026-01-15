# 🎯 Pega-Vagas

Pipeline de Engenharia de Dados para coleta e análise de vagas de tecnologia no Brasil.

## 📋 Visão Geral

Este projeto implementa um pipeline completo de dados seguindo a arquitetura **Medallion** (Bronze/Silver/Gold):

```
Web Scraping → HTML Bruto → Extração LLM → Star Schema → Análises
  (Camoufox)     (Bronze)      (Silver)      (Gold)       (BI)
```

## 🚀 Quick Start

```bash
# 1. Clone e instale
git clone https://github.com/seu-usuario/pega-vagas.git
cd pega-vagas
pip install -e ".[dev]"

# 2. Instale o navegador
playwright install firefox

# 3. Configure
cp .env.example .env
# Edite .env com suas chaves de API

# 4. Execute
python -m src.pipeline run
```

## 🛠️ Tecnologias

| Componente | Tecnologia | Descrição |
|------------|------------|-----------|
| Scraping | Camoufox + Playwright | Navegador anti-detecção |
| Extração | Gemini Flash / GPT-4o-mini | Estruturação semântica |
| Validação | Pydantic | Type-safe schemas |
| Processamento | DuckDB | OLAP local de alta performance |
| Storage | Parquet | Formato colunar comprimido |
| Orquestração | GitHub Actions | Execução diária serverless |

## 📊 Arquitetura Medallion

### 🥉 Bronze (Raw)
- HTML bruto das páginas
- Metadados de coleta
- Formato: JSON Lines

### 🥈 Silver (Cleansed)  
- Dados estruturados via LLM
- Validados por schema Pydantic
- Formato: Parquet

### 🥇 Gold (Curated)
- Star Schema dimensional
- Views analíticas pré-calculadas
- Formato: DuckDB + Parquet

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
│   ├── ingestion/      # Camada Bronze (scraping)
│   ├── processing/     # Camada Silver (LLM)
│   ├── analytics/      # Camada Gold (DuckDB)
│   └── schemas/        # Modelos Pydantic
├── data/
│   ├── bronze/         # HTML bruto
│   ├── silver/         # Dados limpos
│   └── gold/           # Star Schema
├── .github/workflows/  # Orquestração
└── tests/              # Testes automatizados
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
