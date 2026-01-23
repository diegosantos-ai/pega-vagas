# Implementação v2 - Reestruturação do Pega-Vagas

**Data:** 23 de janeiro de 2026  
**Objetivo:** Configurar automação para buscar vagas de Data Engineer, Automação e IA, com envio via Telegram a cada 3 horas

## 📋 Resumo das Mudanças

Esta versão implementa melhorias significativas no pipeline de busca de vagas, focando em:

1. **Sistema de Scoring Flexível** - Substituição do QualityGate binário por um sistema de pontuação
2. **Configuração Centralizada** - Arquivo YAML para gerenciar termos de busca e regras
3. **Agendamento a Cada 3 Horas** - Workflow do GitHub Actions atualizado
4. **Notificações Melhoradas** - Resumo de vagas com formatação corrigida
5. **Suporte Expandido** - Data Engineer, Automação, IA e Análise de Dados

---

## 🔧 Componentes Implementados

### 1. QualityGate v2 (`src/quality_gate_v2.py`)

**Melhorias:**
- Sistema de scoring (0-100) em vez de aprovação/rejeição binária
- Regra de ouro: **REMOTO é obrigatório** (nunca passa vagas híbridas/presenciais)
- Score mínimo configurável (padrão: 50)
- Pontuação por stack tecnológico
- Bônus de senioridade e penalidades para junior/estágio

**Fluxo de Validação:**
```
1. Verifica se é 100% remoto (REJEITA se híbrido/presencial)
2. Verifica localização (Brasil ou totalmente remoto)
3. Calcula score de relevância:
   - Título (40 pontos) + Stack (até 50 pontos)
   - Bônus de senioridade (+10 a +15)
   - Penalidades para junior (-10 a -20)
4. Aprova se score >= min_score_threshold
```

**Exemplo de Uso:**
```python
from src.quality_gate_v2 import QualityGateV2

gate = QualityGateV2(min_score_threshold=50)

job_data = {
    "title": "Senior Data Engineer",
    "description": "100% remoto. Stack: Python, Spark, Airflow, AWS. Brasil.",
    "url": "https://example.com/job",
}

result = gate.evaluate(job_data)
print(f"Válida: {result.is_valid}, Score: {result.score}")
# Output: Válida: True, Score: 95
```

---

### 2. Configuração Centralizada (`config.yaml`)

**Arquivo YAML** com todas as regras e parâmetros:

```yaml
search_terms:
  data_engineer: ["Data Engineer", "Engenheiro de Dados", ...]
  automation: ["Automation Engineer", "Engenheiro de Automação", ...]
  ai_ml: ["AI Engineer", "Machine Learning Engineer", ...]
  data_analyst: ["Data Analyst", "Analista de Dados", ...]
  data_scientist: ["Data Scientist", "Cientista de Dados", ...]

quality_gate:
  min_score_threshold: 50
  strict_remote: true
  remote_positive_patterns: [...]
  remote_negative_patterns: [...]
  tech_stack_points: {...}

schedule:
  frequency_hours: 3
  timezone: "America/Sao_Paulo"

telegram:
  message_format: "detailed"
  send_summary_only: true
  max_jobs_per_message: 5
```

**Vantagens:**
- Sem necessidade de editar código Python para ajustar regras
- Fácil adicionar novos termos de busca
- Centralizado e versionável no Git

---

### 3. Config Loader (`src/config/config_loader.py`)

**Singleton** que carrega e fornece acesso tipado à configuração:

```python
from src.config.config_loader import config

# Acesso simples
min_score = config.get_min_score_threshold()  # 50
frequency = config.get_frequency_hours()      # 3
terms = config.get_search_terms()             # Lista de 23 termos
```

---

### 4. Notificador Telegram v2 (`src/notifications/telegram_v2.py`)

**Melhorias:**
- Formatação corrigida de URLs (encoding UTF-8)
- Suporte a resumo de múltiplas vagas
- Indicador visual de score (🔥 para score >= 80, ⭐ para >= 60)
- Melhor tratamento de erros
- Deduplicação de vagas

**Exemplo de Mensagem:**
```
🔥 Senior Data Engineer
🏢 Tech Company
📍 Brasil
🏠 Remoto
🛠️ Python, Spark, AWS
📈 Relevância: 85/100

[🔗 Ver vaga completa](https://example.com/job)
```

---

### 5. Workflow GitHub Actions Atualizado (`.github/workflows/scrape.yaml`)

**Mudanças:**
- Agendamento: `0 0,3,6,9,12,15,18,21 * * *` (a cada 3 horas em UTC)
- Múltiplos termos de busca em cada execução
- Suporte a modo dry-run
- Melhor resumo de execução

**Cronograma (BRT - UTC-3):**
```
UTC        BRT
00:00  →  21:00 (dia anterior)
03:00  →  00:00
06:00  →  03:00
09:00  →  06:00
12:00  →  09:00
15:00  →  12:00
18:00  →  15:00
21:00  →  18:00
```

---

## 📊 Termos de Busca Expandidos

| Categoria | Termos |
|-----------|--------|
| **Data Engineer** | Data Engineer, Engenheiro de Dados, Analytics Engineer, Data Platform, Data Architect |
| **Automação** | Automation Engineer, Engenheiro de Automação, RPA Developer |
| **IA/ML** | AI Engineer, Machine Learning Engineer, ML Engineer |
| **Análise de Dados** | Data Analyst, Analista de Dados, Business Intelligence |
| **Ciência de Dados** | Data Scientist, Cientista de Dados |

**Total:** 23 termos de busca

---

## 🎯 Filtros de Qualidade

### Regra de Ouro: REMOTO é Obrigatório

**Padrões que REJEITAM (nunca passam):**
- "híbrido", "hybrid"
- "presencial", "on-site"
- "office based"
- "dias no escritório"
- "must live in"
- "requires relocation"

**Padrões que APROVAM (positivos):**
- "100% remoto", "fully remote"
- "remote first", "trabalho remoto"
- "home office", "anywhere in brazil"
- "work from anywhere"

### Score Mínimo: 50/100

Vagas precisam de score >= 50 para serem notificadas.

**Pontuação:**
- Título match com role alvo: +40
- Stack tecnológico: até +50
- Senioridade (Senior/Lead/Staff): +10 a +15
- Penalidade Junior/Estágio: -10 a -20

---

## 🚀 Como Usar

### 1. Configuração Inicial

```bash
# Clonar repositório
git clone https://github.com/diegosantos-ai/pega-vagas.git
cd pega-vagas

# Copiar .env (já fornecido)
cp .env .env.local

# Instalar dependências
pip install -e ".[dev]"
```

### 2. Testar Localmente

```bash
# Testar QualityGate
python src/quality_gate_v2.py

# Testar ConfigLoader
python -c "from src.config.config_loader import config; print(config.get_search_terms())"

# Testar Notificador
python -c "
import asyncio
from src.notifications.telegram_v2 import TelegramNotifierV2
notifier = TelegramNotifierV2()
asyncio.run(notifier.test_connection())
"
```

### 3. Executar Pipeline Manualmente

```bash
# Bronze (scraping)
python -m src.pipeline bronze --query "Data Engineer" --max-jobs 50

# Silver (LLM processing)
python -m src.pipeline silver

# Gold (DuckDB transforms)
python -m src.pipeline gold

# Notify (Telegram)
python -m src.pipeline notify
```

### 4. Agendamento Automático

O GitHub Actions executará automaticamente a cada 3 horas. Para executar manualmente:

1. Vá para: https://github.com/diegosantos-ai/pega-vagas/actions
2. Clique em "Job Scraping Pipeline - Every 3 Hours"
3. Clique em "Run workflow"

---

## 📈 Métricas Esperadas

Com as mudanças implementadas:

| Métrica | Antes | Depois | Melhoria |
|---------|-------|--------|----------|
| **Vagas coletadas/exec** | ~135 | ~140 | +4% |
| **Vagas aprovadas** | ~5 | ~20-30 | +400-500% |
| **Falsos positivos** | Alto | Baixo | Scoring |
| **Frequência** | 1x/dia | 8x/dia | +700% |
| **Termos monitorados** | 3 | 23 | +667% |

---

## 🔍 Troubleshooting

### Problema: Poucas vagas sendo notificadas

**Solução:**
1. Reduzir `min_score_threshold` em `config.yaml` (ex: 40)
2. Adicionar mais termos de busca
3. Verificar logs: `data/logs/pega-vagas.log`

### Problema: Muitas vagas irrelevantes

**Solução:**
1. Aumentar `min_score_threshold` (ex: 60)
2. Ajustar `tech_stack_points` em `config.yaml`
3. Usar `strict_remote: true` para rejeitar qualquer menção de híbrido

### Problema: Links não funcionam no Telegram

**Solução:**
- Já corrigido em `telegram_v2.py` com sanitização de URLs
- Usar `parse_mode: "Markdown"` para links

---

## 📝 Próximos Passos

1. **Monitoramento:** Adicionar alertas se pipeline falhar
2. **Cache:** Implementar cache de vagas para evitar duplicatas
3. **Analytics:** Dashboard com estatísticas de vagas
4. **Integração:** Adicionar suporte a LinkedIn e outras plataformas
5. **ML:** Usar histórico de cliques para melhorar scoring

---

## 📚 Arquivos Modificados/Criados

| Arquivo | Status | Descrição |
|---------|--------|-----------|
| `src/quality_gate_v2.py` | ✨ Novo | Sistema de scoring refatorado |
| `src/config/config_loader.py` | ✨ Novo | Carregador de configuração |
| `src/notifications/telegram_v2.py` | ✨ Novo | Notificador melhorado |
| `config.yaml` | ✨ Novo | Configuração centralizada |
| `.github/workflows/scrape.yaml` | 🔄 Atualizado | Agendamento a cada 3 horas |
| `.env` | 📋 Fornecido | Credenciais (Telegram, Gemini) |

---

## ✅ Checklist de Implementação

- [x] QualityGate v2 com sistema de scoring
- [x] Configuração centralizada em YAML
- [x] ConfigLoader singleton
- [x] Notificador Telegram v2 com resumo
- [x] Agendamento a cada 3 horas
- [x] Termos de busca expandidos (23 termos)
- [x] Testes unitários dos componentes
- [x] Documentação completa
- [ ] Deploy em produção (GitHub Actions)
- [ ] Monitoramento e alertas

---

## 🤝 Suporte

Para dúvidas ou problemas, consulte:
- `agents.md` - Contexto técnico do projeto
- `README.md` - Documentação geral
- Logs em `data/logs/pega-vagas.log`

**Desenvolvido com ❤️ para a recolocação profissional de Diego Santos**
