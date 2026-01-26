# 🏆 Melhores Práticas - Pega-Vagas

> Este documento consolida os princípios de engenharia aplicados para tornar o projeto robusto, escalável e fácil de manter.

---

## 🧠 1. Filosofia: "Menos Regras, Mais Inteligência"

### O Problema "Regras Demais"
Tentar capturar todas as variações de texto com Regex ou pontuações complexas ("if junior -20 pontos") leva a fragilidade e manutenção constante.

### A Solução
Confie na camada **Silver (LLM)** para estruturar e classificar dados. A IA entende contexto ("remoto, mas presencial para festa" = Remoto). O regex não.

**Regra de Ouro:**
> O QualityGate deve ser um *Safety Check*, não uma recriação da inteligência que já existe no LLM.
>
> **Antes:** Regex negativo estrito + Regex positivo + Score + Penalidades
> **Agora:** Se LLM diz "Remoto" -> Aceita. (Regex apenas como fallback).

---

## 🛠️ 2. Engenharia de Software em Dados

### Configuração Centralizada (`src/config/settings.py`)
- **Nunca** use `os.getenv()` espalhado pelo código.
- Use **Pydantic Settings** para validação de tipo e obrigatoriedade no start da aplicação.
- Garante que a aplicação nem inicie se faltar uma chave de API crítica.

### Observabilidade Limitada (Logging)
- Logue **decisões de negócio** (ex: "Vaga X rejeitada por motivo Y").
- Evite logar ruído ("Iniciando loop...").
- Use logs estruturados (`structlog`) para facilitar ingestão futura em Datadog/CloudWatch.

### Tratamento de Falhas (Resiliência)
- **APIs externas falham.** Use bibliotecas de retry (`tenacity`) em chamadas de rede.
- **Links quebram.** Não bloqueie o pipeline inteiro porque um link retornou 404 (timeout curto ou flag opcional).

---

## 🧪 3. Qualidade e Testes (CI/CD)

### Pipeline Automatizado
- **Linting (Ruff):** Código mal formatado esconde bugs. O CI deve bloquear merges com erros de estilo.
- **Type Checking (Mypy):** Python é dinâmico, mas em Data Engineering a tipagem estrita evita erros de `NoneType` em produção.
- **Cache Inteligente:** Persista dados processados (`.seen_jobs.json`) entre execuções do GitHub Actions para evitar reprocessamento/spam.

---

## 🧹 4. Clean Code para Dados

- **Nomes Significativos:** `run_bronze()` é melhor que `scripts/step1.py`.
- **Extração de Lógica:** Se um `if` tem 3 linhas de condições, extraia para um método `_is_valid_job()`.
- **Arquivos Mortos:** Se não usa, apague. Arquivos `_v2.py` ou `test_old.py` só geram confusão para quem chega no projeto.

---

## 🚀 Resumo para Contribuições

1. **Simplifique:** Se for adicionar uma regra, pergunte-se: "O LLM já não sabe disso?"
2. **Valide:** Adicione ou rode testes existentes antes de commitar.
3. **Padronize:** Rode `ruff check` e `ruff format`.

---
