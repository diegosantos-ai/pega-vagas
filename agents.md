# Pega Vagas - Contexto para Agentes IA

Este documento define regras e contexto para sessões futuras de desenvolvimento.

---

## 🎯 Objetivo do Projeto

Coletar vagas de **Data Engineering** de empresas relevantes para o mercado brasileiro, com foco em oportunidades **100% remotas** para profissionais baseados no **Brasil**.

---

## 📍 Definição: Modalidade REMOTA

### ✅ O que é considerado REMOTO (válido):
- **100% Home Office** - trabalho totalmente remoto, sem exigência de presença física
- **Remote First** - empresa prioriza remoto, escritório é opcional
- **Anywhere in Brazil** - pode trabalhar de qualquer lugar do Brasil
- **Full Remote** / **Fully Remote** - termos em inglês equivalentes

### ❌ O que NÃO é considerado REMOTO (inválido):
- **Híbrido** - exige presença X dias por semana/mês
- **Remote with occasional office visits** - não é 100% remoto
- **Presencial com home office eventual** - não é remoto
- **Remote (must be near office)** - exige proximidade física
- **Flex** - geralmente significa híbrido

### ⚠️ Casos que precisam análise:
- "Remote (Brazil)" ✅ - ok, especifica o país
- "Remote (Spain)" ❌ - remoto, mas para outro país
- "Remote - São Paulo based" ⚠️ - pode exigir presença eventual
- "Remote with quarterly meetups" ✅ - aceitável se meetups forem opcionais

### Regex para detecção de REMOTO:
```python
REMOTE_POSITIVE = [
    r"\b100%?\s*remoto\b",
    r"\bfully\s*remote\b",
    r"\bfull\s*remote\b",
    r"\bremote\s*first\b",
    r"\btrabalho\s*remoto\b",
    r"\bhome\s*office\b",
    r"\banywhere\b",
    r"\bremoto\b(?!.*\b(h[íi]brido|presencial|escrit[óo]rio)\b)",
]

REMOTE_NEGATIVE = [
    r"\bh[íi]brido\b",
    r"\bhybrid\b",
    r"\bpresencial\b",
    r"\bon[\s-]?site\b",
    r"\boffice\s*based\b",
    r"\b\d+\s*(dias?|days?)\s*(no\s*)?(escrit[óo]rio|office)\b",
]
```

---

## 🇧🇷 Definição: Empresa com Operação no BRASIL

### ✅ O que é considerado EMPRESA BRASIL (válido):
- Empresa com **CNPJ brasileiro** (matriz ou filial)
- Contratação via **CLT** ou **PJ brasileiro**
- Processo seletivo conduzido por **RH no Brasil** (mesmo que matriz seja gringa)
- Pagamento em **BRL** (Reais)
- Empresa multinacional com **escritório funcional no Brasil**

### ❌ O que NÃO é considerado (inválido):
- Empresa 100% estrangeira contratando como **contractor internacional**
- Pagamento apenas em **USD/EUR** via Deel, Remote.com, etc.
- Processo seletivo 100% em inglês sem menção ao Brasil
- Vaga listada para outro país (Espanha, Portugal, EUA, etc.)

### Como identificar na vaga:
1. **Localização explícita**: "Brazil", "Brasil", "São Paulo", "Remote - Brazil"
2. **Idioma**: Vaga em português geralmente é para Brasil
3. **Moeda**: Salário em BRL indica Brasil
4. **ATS da empresa**: Se empresa está na nossa lista, já validamos

### Empresas na lista `companies.py`:
Todas as empresas configuradas em `src/config/companies.py` já foram validadas como tendo operação no Brasil. Vagas dessas empresas são automaticamente consideradas "Brasil válido".

### Empresas internacionais com Brasil:
| Empresa | Status Brasil |
|---------|---------------|
| Nubank | ✅ Matriz BR |
| Stone | ✅ Matriz BR |
| iFood | ✅ Matriz BR |
| Wildlife | ✅ Matriz BR |
| ThoughtWorks | ✅ Escritório BR |
| CI&T | ✅ Matriz BR |
| Stripe | ⚠️ Verificar se vaga é p/ BR |
| Vercel | ⚠️ Verificar se vaga é p/ BR |
| Figma | ⚠️ Verificar se vaga é p/ BR |

---

## 🔍 Regras de Filtragem

### Na Ingestão (Bronze):
```python
# Gupy: usar filtro nativo
params["workplaceType"] = "remote"

# SmartRecruiters: já filtra por país
params["country"] = "br"

# Greenhouse/Lever: filtrar no pós-processamento
```

### Na Transformação (Silver):
```python
def is_valid_job(job: dict) -> bool:
    """Valida se vaga atende critérios de remoto + Brasil."""
    
    # 1. Deve ser 100% remoto
    if job.get("modelo_trabalho") != "Remoto":
        return False
    
    # 2. Deve ser para Brasil
    localidade = job.get("localidade", {})
    pais = localidade.get("pais", "Brasil") if isinstance(localidade, dict) else "Brasil"
    
    if pais.lower() not in ["brasil", "brazil", "br"]:
        return False
    
    # 3. Verificar se localização não indica outro país
    location_text = str(localidade).lower()
    invalid_countries = ["spain", "espanha", "portugal", "usa", "united states", "uk", "germany"]
    if any(country in location_text for country in invalid_countries):
        return False
    
    return True
```

### Na Notificação:
- Aplicar `is_valid_job()` antes de enviar
- Logar vagas descartadas para análise

---

## 📊 Métricas de Qualidade

Após implementar filtros, espera-se:
- **0%** de vagas presenciais notificadas
- **0%** de vagas de outros países notificadas
- **100%** de vagas notificadas são remotas para Brasil

---

## 🔄 Atualizações

| Data | Alteração |
|------|-----------|
| 2026-01-16 | Criação inicial do documento |

---

## 📝 Notas para o Agente

1. **Sempre verificar** se vaga é remota E para Brasil antes de processar/notificar
2. **Em caso de dúvida**, descartar a vaga (melhor perder uma válida do que notificar inválida)
3. **Empresas da lista** `companies.py` são pré-validadas para Brasil
4. **Vagas em português** têm maior probabilidade de serem para Brasil
5. **Filtrar na fonte** sempre que a API permitir (mais eficiente)
