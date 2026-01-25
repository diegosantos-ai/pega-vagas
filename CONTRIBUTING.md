# Contribuindo para o Pega-Vagas

Obrigado por considerar contribuir com o Pega-Vagas! 🎉

## 🚀 Setup de Desenvolvimento

### 1. Clone o repositório

```bash
git clone https://github.com/diegosantos-ai/pega-vagas.git
cd pega-vagas
```

### 2. Crie um ambiente virtual

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -e ".[dev]"
```

### 4. Configure as variáveis de ambiente

```bash
cp .env.example .env
# Edite .env com suas chaves (opcional para desenvolvimento)
```

---

## 📝 Padrões de Código

Usamos [Ruff](https://docs.astral.sh/ruff/) para linting e formatação.

### Verificar código

```bash
# Lint
ruff check src/ tests/

# Formatar
ruff format src/ tests/
```

### Configuração do Ruff

O projeto está configurado com as seguintes regras (ver `pyproject.toml`):

- **line-length**: 100 caracteres
- **target-version**: Python 3.11
- **select**: E, F, I, UP, B

---

## 🧪 Testes

Execute os testes antes de enviar um PR:

```bash
# Rodar todos os testes
pytest tests/ -v

# Com coverage
pytest tests/ --cov=src --cov-report=html

# Rodar teste específico
pytest tests/test_schemas.py -v
```

---

## 🔄 Workflow de Contribuição

### 1. Crie uma branch

```bash
git checkout -b feature/minha-feature
# ou
git checkout -b fix/meu-bug-fix
```

### 2. Faça suas alterações

- Escreva código limpo e documentado
- Adicione/atualize testes quando necessário
- Siga os padrões de código do projeto

### 3. Verifique a qualidade

```bash
# Lint
ruff check src/ tests/

# Testes
pytest tests/ -v
```

### 4. Commit com mensagem clara

```bash
git add .
git commit -m "feat: adiciona suporte para nova plataforma X"
```

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - Nova funcionalidade
- `fix:` - Correção de bug
- `docs:` - Documentação
- `refactor:` - Refatoração
- `test:` - Adição/modificação de testes
- `chore:` - Tarefas de manutenção

### 5. Push e abra um PR

```bash
git push origin feature/minha-feature
```

Abra um Pull Request no GitHub com:

- Descrição clara das mudanças
- Link para issue relacionada (se houver)
- Screenshots (se for mudança visual)

---

## 📁 Estrutura do Projeto

```
pega-vagas/
├── src/
│   ├── pipeline.py        # Pipeline principal (orquestrador)
│   ├── quality_gate.py    # Filtros de qualidade
│   ├── notifications/     # Telegram notifier
│   ├── ingestion/         # Scrapers de API
│   ├── config/            # Empresas e configurações
│   ├── processing/        # Extração com LLM
│   ├── analytics/         # Transformações DuckDB
│   └── schemas/           # Modelos Pydantic
├── tests/                 # Testes automatizados
├── .github/workflows/     # GitHub Actions
└── data/                  # Dados (não versionados)
```

---

## 🐛 Reportando Bugs

Use o [GitHub Issues](https://github.com/diegosantos-ai/pega-vagas/issues) para reportar bugs.

Inclua:

1. Descrição do problema
2. Passos para reproduzir
3. Comportamento esperado vs. atual
4. Logs de erro (se aplicável)
5. Versão do Python e SO

---

## 💡 Sugestões de Melhoria

Ideias para contribuir:

- [ ] Adicionar novas fontes de dados (Indeed, Glassdoor)
- [ ] Melhorar o QualityGate com mais regras
- [ ] Dashboard de métricas (Streamlit)
- [ ] Suporte a mais idiomas
- [ ] Melhorar cobertura de testes

---

## 📞 Dúvidas?

Abra uma [Discussion](https://github.com/diegosantos-ai/pega-vagas/discussions) no GitHub.

---

Obrigado por contribuir! 🚀
