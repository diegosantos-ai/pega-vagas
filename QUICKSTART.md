# Quick Start - Pega-Vagas v2

## ⚡ Setup em 5 Minutos

### 1. Clonar e Instalar

```bash
git clone https://github.com/diegosantos-ai/pega-vagas.git
cd pega-vagas
pip install -e ".[dev]"
```

### 2. Configurar Credenciais

Seu arquivo `.env` já está configurado com:
- ✅ `TELEGRAM_BOT_TOKEN` - Bot do Telegram
- ✅ `TELEGRAM_CHAT_ID` - ID do grupo/chat
- ✅ `GOOGLE_API_KEY` - Gemini API

### 3. Testar Conexão

```bash
# Testar Telegram
python -c "
import asyncio
from src.notifications.telegram_v2 import TelegramNotifierV2
notifier = TelegramNotifierV2()
asyncio.run(notifier.test_connection())
"
```

Se receber ✅, está tudo funcionando!

---

## 🎯 Usar o Pipeline

### Opção 1: Executar Localmente

```bash
# Buscar vagas
python -m src.pipeline bronze --query "Data Engineer" --max-jobs 50

# Processar com LLM
python -m src.pipeline silver

# Carregar em DuckDB
python -m src.pipeline gold

# Enviar notificações
python -m src.pipeline notify
```

### Opção 2: Executar Tudo de Uma Vez

```bash
python -m src.pipeline run
```

### Opção 3: Agendamento Automático (GitHub Actions)

O pipeline já está configurado para rodar **a cada 3 horas** automaticamente!

Você receberá notificações no Telegram com as vagas encontradas.

---

## 📊 Entender os Termos de Busca

O sistema busca por **23 termos** em 5 categorias:

```yaml
Data Engineer:
  - Data Engineer
  - Engenheiro de Dados
  - Analytics Engineer
  - Data Platform
  - Data Architect

Automação:
  - Automation Engineer
  - Engenheiro de Automação
  - RPA Developer

IA/ML:
  - AI Engineer
  - Machine Learning Engineer

Análise de Dados:
  - Data Analyst
  - Analista de Dados
  - Business Intelligence

Ciência de Dados:
  - Data Scientist
  - Cientista de Dados
```

---

## 🔥 Filtros Importantes

### ✅ O que SEMPRE passa:

- Vagas **100% remotas**
- Menção explícita de "remoto", "fully remote", "work from home"
- Localização no Brasil ou "anywhere"

### ❌ O que NUNCA passa:

- Vagas **híbridas** ou **presenciais**
- Menção de "híbrido", "on-site", "presencial"
- Exigência de relocation
- Score < 50

---

## 📈 Score de Relevância

Cada vaga recebe uma pontuação (0-100):

| Fator | Pontos |
|-------|--------|
| Título match (Data Engineer, etc) | +40 |
| Stack: Python, SQL, Spark, etc | até +50 |
| Senior/Lead/Staff | +10 a +15 |
| Junior/Estágio | -10 a -20 |

**Mínimo para notificar:** 50 pontos

---

## 🛠️ Customizar Configuração

Edite `config.yaml` para:

**Aumentar volume de vagas:**
```yaml
quality_gate:
  min_score_threshold: 40  # Era 50
```

**Adicionar novo termo:**
```yaml
search_terms:
  data_engineer:
    - "Data Engineer"
    - "Seu novo termo aqui"
```

**Mudar frequência:**
```yaml
schedule:
  frequency_hours: 2  # Era 3
```

---

## 📱 Receber Notificações

### No Telegram:

Você receberá mensagens como:

```
📊 Resumo de Vagas - 23/01 18:00

✨ Encontradas 5 vagas relevantes:

1. Tech Company
  • Senior Data Engineer 🔥
    Score: 85/100

2. Another Company
  • Automation Engineer ⭐
    Score: 72/100

_Clique nos links abaixo para ver detalhes de cada vaga_
```

Depois, cada vaga é enviada com detalhes completos.

---

## 🐛 Troubleshooting

### Problema: "Nenhuma vaga nova para notificar"

**Solução:**
1. Reduzir `min_score_threshold` em `config.yaml`
2. Verificar se as APIs estão respondendo
3. Checar logs: `data/logs/pega-vagas.log`

### Problema: "TELEGRAM_CHAT_ID não configurado"

**Solução:**
```bash
python -m src.notifications.telegram_v2
# Siga as instruções para descobrir seu chat_id
```

### Problema: Links não funcionam no Telegram

**Solução:**
Já está corrigido em `telegram_v2.py`. Se persistir, verifique a URL da vaga.

---

## 📚 Documentação Completa

- `IMPLEMENTACAO_V2.md` - Detalhes técnicos
- `config.yaml` - Configuração centralizada
- `agents.md` - Contexto do projeto
- `README.md` - Documentação geral

---

## ✨ Próximas Execuções

O pipeline rodará automaticamente em:

- **Hoje às 21:00 BRT** (00:00 UTC)
- **Amanhã às 00:00 BRT** (03:00 UTC)
- **Amanhã às 03:00 BRT** (06:00 UTC)
- ... e assim por diante, a cada 3 horas

Você receberá notificações no Telegram!

---

**Desenvolvido com ❤️ para Diego Santos**
