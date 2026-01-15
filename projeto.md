Arquitetura de Referência para Engenharia de Dados em Inteligência de Mercado: Um Estudo Aprofundado sobre Web Scraping, Processamento via LLMs e Modelagem Analítica no Contexto de Vagas de Tecnologia

1. Introdução: O Novo Paradigma da Inteligência de Mercado de Trabalho
A dinâmica do mercado de trabalho global, especialmente no setor de tecnologia, sofreu uma metamorfose acelerada na última década. A busca por talentos em áreas críticas como Engenharia de Dados, Ciência de Dados, Análise de Negócios e Inteligência Artificial deixou de ser uma função puramente operacional de Recursos Humanos para se tornar um imperativo estratégico de inteligência competitiva. As descrições de vagas (Job Descriptions - JDs) transcenderam sua função original de simples anúncios publicitários; hoje, elas constituem artefatos de dados ricos e complexos que, quando agregados e analisados corretamente, revelam a maturidade tecnológica de uma organização, suas intenções estratégicas de investimento e as tendências emergentes em stacks tecnológicos.1
No entanto, a extração sistemática e estruturada desses dados apresenta desafios de engenharia formidáveis. Diferentemente de mercados financeiros ou meteorológicos, onde APIs padronizadas são a norma, o ecossistema de dados de emprego é fragmentado, não estruturado e agressivamente protegido contra automação. Plataformas como LinkedIn, Glassdoor, Indeed e agregadores de nicho implementaram defesas sofisticadas baseadas em análise comportamental, verificação de integridade de navegador e desafios criptográficos (CAPTCHAs) para preservar a exclusividade de seus dados. Concomitantemente, a evolução das interfaces web para Single Page Applications (SPAs) baseadas em frameworks reativos (React, Vue, Angular) tornou obsoletas as abordagens tradicionais de web scraping baseadas em requisições HTTP estáticas e parsing de DOM simples.
Este relatório técnico propõe uma arquitetura de pipeline de Engenharia de Dados "ponta a ponta" desenhada especificamente para este cenário hostil e de alta complexidade. A proposta rejeita a arquitetura legada de ETL (Extract, Transform, Load) em favor de uma abordagem moderna de ELT (Extract, Load, Transform) integrada a conceitos de Lakehouse Local. A solução articula o uso de navegadores instrumentados para evasão de detecção (Camoufox/Playwright), a aplicação de Grandes Modelos de Linguagem (LLMs) para a normalização semântica de entidades não estruturadas (Extraction-as-Code) e o uso de motores OLAP embutidos (DuckDB) para processamento analítico de alta performance e baixo custo.3 O objetivo não é apenas coletar dados, mas transformar o caos de HTMLs dispersos em um modelo dimensional (Star Schema) capaz de responder perguntas complexas sobre salários, correlações de habilidades e distribuição geográfica de oportunidades.

2. Soberania de Dados, Ética e Conformidade Regulatória no Brasil
A construção de qualquer pipeline de dados que envolva a coleta de informações da web aberta deve ser precedida por uma análise rigorosa do arcabouço legal. No Brasil, a Lei Geral de Proteção de Dados (LGPD - Lei nº 13.709/2018) estabelece as regras do jogo, criando um ambiente regulatório que difere substancialmente dos Estados Unidos e da União Europeia em nuances importantes. A engenharia do pipeline deve ser, portanto, "Privacy by Design", incorporando as restrições legais diretamente na arquitetura técnica.5
2.1. A Natureza Jurídica dos Dados de Vagas e Perfis Públicos
Uma concepção equivocada comum na engenharia de dados é a de que "se está na internet, é público e pode ser coletado". A LGPD introduziu distinções críticas. O Artigo 7º, §4º, diferencia dados "tornados manifestamente públicos pelo titular" de dados meramente acessíveis. Embora uma vaga de emprego seja, por definição, um dado público (pois a empresa deseja divulgá-la), os dados pessoais associados a ela — como o nome do recrutador, perfis de funcionários que trabalham na equipe ou links para perfis pessoais — gozam de proteção legal.5
A base legal mais robusta para a operação de um scraper de inteligência de mercado no Brasil, na ausência de consentimento (que é inviável de obter em escala), é o Legítimo Interesse (Art. 7º, IX). No entanto, a aplicação desta base legal não é um cheque em branco. Ela exige que o controlador (a entidade que realiza o scraping) realize um Teste de Proporcionalidade (LIA - Legitimate Interest Assessment). Este teste deve demonstrar que a finalidade da coleta (análise estatística do mercado de trabalho) é legítima, que a metodologia empregada é estritamente necessária (não há outra fonte de dados disponível) e que os direitos fundamentais dos titulares não são violados.8
Para mitigar riscos, o pipeline deve implementar filtros de Minimização de Dados na etapa de ingestão (Bronze Layer). Isso significa configurar os seletores de extração e os prompts dos LLMs para ignorar ou anonimizar ativamente qualquer Identificação Pessoal (PII) que não seja estritamente necessária para a análise da vaga. Por exemplo, coletar "Empresa: TechCorp" é essencial; coletar "Recrutador: João Silva" é um risco desnecessário que deve ser evitado arquiteturalmente.9

2.2. Dados Sensíveis e o Risco de Discriminação Algorítmica
Um risco exacerbado no scraping de vagas de dados, muitas das quais incluem hoje cláusulas de ações afirmativas ou censos de diversidade, é a coleta inadvertida de Dados Pessoais Sensíveis (origem racial, convicção religiosa, filiação a sindicato, dados referentes à saúde ou à vida sexual). O Artigo 11 da LGPD veda o uso do Legítimo Interesse para o tratamento de dados sensíveis. Se o pipeline coletar, mesmo que acidentalmente, descrições de vagas que contenham listas de candidatos ou comentários sobre saúde ocupacional, a operação torna-se ilegal. A arquitetura deve incluir uma etapa de "Sanitização de Sensibilidade" onde modelos de NLP (Processamento de Linguagem Natural) classificam e descartam qualquer texto que sugira a presença de dados sensíveis antes que ele seja persistido na camada Silver.10
2.3. Termos de Uso (ToS), Robots.txt e a Zona Cinzenta do Scraping

A relação entre a lei e os Termos de Uso (ToS) das plataformas é complexa. Nos Estados Unidos, o caso hiQ Labs, Inc. v. LinkedIn Corp. estabeleceu um precedente importante de que a coleta automatizada de dados publicamente acessíveis não viola a Lei de Fraude e Abuso de Computadores (CFAA).11 No entanto, no Brasil, a violação de ToS pode ser interpretada como quebra contratual no âmbito civil, especialmente se o scraper realizar login na plataforma (autenticação), momento em que o usuário "aceita" explicitamente as regras que proíbem robôs.12
Portanto, a recomendação técnica e jurídica para este pipeline é operar exclusivamente na camada pública das plataformas, sem realizar autenticação (login). Isso reduz drasticamente o risco jurídico, pois elimina a adesão contratual direta às cláusulas anti-scraping. Além disso, o respeito ao arquivo robots.txt deve ser a configuração padrão, embora muitas plataformas de vagas usem este arquivo para bloquear indiscriminadamente todos os bots. A indústria de inteligência de dados opera frequentemente em uma zona de tolerância onde o respeito a taxas de requisição (rate limiting) éticas e a identificação clara do User-Agent (quando possível) são usados para diferenciar pesquisadores de atacantes maliciosos.12
3. Paradigmas Arquiteturais: Do ETL Legado ao Local Lakehouse
A arquitetura de dados tradicional, baseada em processos ETL pesados e Data Warehouses monolíticos, mostrou-se inadequada para a velocidade e a variedade dos dados da web moderna. A necessidade de schemas rígidos no momento da ingestão (Schema-on-Write) colide frontalmente com a volatilidade dos layouts HTML, que podem mudar semanalmente. Para este projeto, adotamos uma arquitetura de "Post-Modern Data Stack", caracterizada pela flexibilidade, desacoplamento de computação e armazenamento, e processamento local de alto desempenho.14
3.1. Arquitetura Medalhão (Medallion Architecture)
A organização lógica dos dados seguirá o padrão Medalhão, que estrutura o refinamento da informação em três estágios distintos, permitindo rastreabilidade e recuperação de falhas 3:
Camada Bronze (Raw): Esta é a zona de aterrissagem dos dados. O objetivo primordial aqui é a fidelidade e imutabilidade. Armazenamos o conteúdo bruto extraído (HTML completo ou JSON cru das APIs ocultas) juntamente com metadados técnicos (data da extração, URL de origem, código de status HTTP). A persistência deve ser feita em formatos que suportem evolução de schema e compressão, como Parquet ou JSON Lines (JSONL) comprimido (zstd/snappy). A principal vantagem de armazenar o HTML bruto é a capacidade de "replay": se descobrirmos no futuro que precisamos extrair um novo campo que ignoramos hoje (ex: "benefícios de saúde"), podemos reprocessar o histórico da camada Bronze sem precisar realizar novo scraping, o que economiza custos de proxy e evita exposição ao bloqueio.3
Camada Silver (Cleansed/Enriched): Onde ocorre a transformação de dados não estruturados em estruturados. É nesta camada que aplicamos os LLMs para extrair entidades do HTML bruto. Os dados são limpos (remoção de duplicatas, normalização de strings, conversão de tipos de dados como datas e moedas) e validados contra um schema rigoroso. A tecnologia subjacente recomendada é o DuckDB, que permite realizar essas transformações usando SQL sobre arquivos Parquet de forma extremamente performática, sem a necessidade de carregar tudo em memória.
Camada Gold (Curated): A camada final de apresentação, modelada especificamente para consumo analítico. Aqui, os dados são desnormalizados ou estruturados em Star Schemas (Fato/Dimensão) para facilitar o uso em ferramentas de BI como Power BI, Metabase ou Streamlit. Agregações pré-calculadas (ex: média salarial por senioridade) também residem aqui.17
3.2. DuckDB: O Motor de Processamento OLAP Local
A escolha do DuckDB como coração do processamento é estratégica. Diferente de bancos de dados transacionais (OLTP) baseados em linha como o PostgreSQL, ou de frameworks distribuídos complexos como o Spark, o DuckDB é um banco de dados analítico (OLAP) embutido, vetorizado e colunar.
Processamento Vetorizado: O DuckDB processa dados em blocos de vetores, aproveitando as instruções SIMD (Single Instruction, Multiple Data) das CPUs modernas. Isso permite varrer milhões de linhas de vagas de emprego em milissegundos em um laptop padrão, eliminando a necessidade de clusters caros na nuvem para volumes de dados na escala de Gigabytes a Terabytes.3
Integração com Data Lake: O DuckDB atua como um motor de consulta sobre arquivos. Ele pode executar SQL diretamente sobre arquivos Parquet no S3 ou no disco local, sem necessidade de uma etapa de "Load" formal para um formato proprietário. Isso viabiliza o conceito de "Local Lakehouse", onde o Data Warehouse é apenas um conjunto de arquivos gerenciados por um motor leve.3
3.3. Armazenamento Híbrido: S3 e PostgreSQL
Embora o DuckDB e arquivos Parquet sejam excelentes para análise, a persistência transacional e a interface com aplicações web podem exigir um banco de dados OLTP. O PostgreSQL entra na arquitetura como o repositório de metadados de orquestração (controle de quais URLs já foram visitadas) e, opcionalmente, como a camada de serviço (Serving Layer) se houver necessidade de concorrência de múltiplos usuários acessando os dados finais. O armazenamento de objetos (AWS S3 ou compatíveis como MinIO) serve como a espinha dorsal de durabilidade, garantindo que os dados brutos e processados estejam seguros e acessíveis independentemente da computação.16
4. Engenharia de Ingestão: Superando a Guerra Anti-Bot
A etapa de ingestão (Web Scraping) é o componente mais frágil e crítico do pipeline. A simplicidade dos scripts requests + BeautifulSoup não é mais viável para alvos de alto valor como LinkedIn ou Glassdoor, que empregam defesas ativas. A engenharia de ingestão moderna exige uma simulação perfeita do ambiente de um navegador real.
4.1. Browser Automation: A Ascensão do Camoufox e Playwright
A comunidade de scraping migrou massivamente do Selenium para o Playwright devido à sua arquitetura moderna baseada em WebSockets (CDP - Chrome DevTools Protocol), que permite maior velocidade e confiabilidade.19 No entanto, o Playwright "vanilla" (padrão) vaza informações que revelam sua natureza automatizada (ex: a propriedade navigator.webdriver definida como true, inconsistências nas APIs de Canvas e WebGL).
Para combater isso, a ferramenta de escolha para 2025 é o Camoufox. O Camoufox não é apenas uma biblioteca; é uma versão customizada e compilada do navegador Firefox, projetada especificamente para evasão de detecção (anti-fingerprinting).20
Por que Firefox? A grande maioria dos bots utiliza Chromium (base do Chrome). Consequentemente, os sistemas anti-bot (como Cloudflare Turnstile, Datadome, Imperva) focam desproporcionalmente na detecção de assinaturas do Chromium. O Firefox possui uma "impressão digital" (fingerprint) diferente e, estatisticamente, apresenta uma taxa de sucesso maior em ambientes hostis por ser menos utilizado por scrapers amadores.20
Mecanismos de Evasão: O Camoufox implementa spoofing nativo de hardware. Ele altera dinamicamente a resposta do navegador a injeções de JavaScript que sondam a placa gráfica, a resolução da tela, as fontes instaladas e os drivers de áudio. Ele consegue passar em testes rigorosos de detecção de bot (como o CreepJS) onde o Playwright padrão falha.
A integração técnica é feita via Python, onde o Camoufox atua como um wrapper compatível com a API do Playwright, permitindo o uso de seletores e métodos de espera (await page.wait_for_selector) familiares aos engenheiros de dados, mas com o motor de renderização stealth do Firefox sob o capô.
4.2. A Necessidade Crítica de Proxies Residenciais
Nenhuma tecnologia de navegador consegue evitar o bloqueio se o endereço IP de origem estiver "queimado". Endereços IP de Data Centers (AWS, Google Cloud, DigitalOcean) são conhecidos e bloqueados preventivamente ou sujeitos a CAPTCHAs agressivos por plataformas de emprego.22
A solução mandatória é o uso de Proxies Residenciais. Estes são IPs atribuídos por Provedores de Acesso à Internet (ISPs) a residências reais (através de acordos de compartilhamento de banda). Para o servidor de destino, a requisição parece vir de um usuário doméstico comum da Vivo, Claro ou Comcast, tornando o bloqueio por faixa de IP quase impossível sem afetar usuários legítimos.23
Estratégia de Rotação: Para scraping de listagens (ex: resultados de busca "Data Engineer"), a rotação de IP a cada requisição é ideal para maximizar a velocidade. Para scraping de detalhes de uma vaga específica, onde pode ser necessário navegar por várias páginas dentro da mesma sessão, o uso de "Sticky Sessions" (manter o mesmo IP por X minutos) é necessário para evitar que a plataforma detecte uma mudança de localização impossível (ex: usuário acessa a home do Brasil e clica na vaga vindo da Alemanha 2 segundos depois).24
Análise de Custo-Benefício: Provedores como Bright Data e Oxylabs oferecem a infraestrutura mais robusta e pools de milhões de IPs, mas a custos elevados. Para projetos de menor escala, provedores "mid-range" como Smartproxy ou IPRoyal oferecem um equilíbrio aceitável, com taxas de sucesso acima de 98% a uma fração do custo.25
4.3. Resolução de Desafios e CAPTCHAs
Mesmo com Camoufox e proxies, CAPTCHAs (Completely Automated Public Turing test to tell Computers and Humans Apart) podem surgir. A estratégia de defesa em profundidade envolve:
Evasão: A melhor forma de lidar com CAPTCHA é não ativá-lo. O uso de comportamento humanizado (mouse jiggling, delays aleatórios entre cliques, rolagem suave da página) reduz o "score de bot" atribuído pela plataforma.
Resolução Automatizada: Quando a evasão falha, o pipeline deve ser capaz de resolver o desafio. Soluções modernas integram APIs de terceiros (como 2Captcha ou Anti-Captcha) ou, mais recentemente, usam LLMs multimodais (GPT-4 Vision) para identificar visualmente a solução do puzzle, embora isso introduza latência e custo. O Camoufox possui capacidades experimentais de auto-resolução de desafios do Cloudflare Turnstile, clicando nas caixas de verificação de forma programática e indetectável.
5. Extração Semântica e Normalização: A Revolução dos LLMs
A extração de dados estruturados a partir de HTML não estruturado sempre foi o "calcanhar de Aquiles" do web scraping. A manutenção de scripts baseados em seletores CSS ou XPath (//div[@class='job-description']/p) é exaustiva, pois qualquer alteração cosmética no site quebra o pipeline. A introdução de Grandes Modelos de Linguagem (LLMs) permitiu a transição para o paradigma de "Extraction-as-Code", onde a lógica de extração é semântica e resiliente.4
5.1. JSON Schema e Validação com Pydantic
O segredo para usar LLMs em engenharia de dados não é o prompt livre ("Resuma esta vaga"), mas a Geração de Saída Estruturada. Modelos modernos (Gemini 1.5 Pro, GPT-4o) podem ser coagidos a gerar saídas que aderem estritamente a um esquema JSON pré-definido.28
A biblioteca Pydantic em Python tornou-se o padrão da indústria para definir esses esquemas. Ela permite declarar a estrutura de dados desejada como classes Python, com tipagem forte e validação embutida.30
Exemplo de Definição de Schema para Vagas:

Python


from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class Salario(BaseModel):
    valor_minimo: Optional[float] = Field(description="Valor numérico do salário base mínimo mensal normalizado.")
    valor_maximo: Optional[float] = Field(description="Valor numérico do salário base máximo mensal normalizado.")
    moeda: Literal = Field(description="Código ISO da moeda.")

class Habilidade(BaseModel):
    nome: str = Field(description="Nome da tecnologia ou habilidade (ex: Python, SQL).")
    categoria: Literal
    obrigatoriedade: bool = Field(description="True se for requisito obrigatório, False se desejável.")

class VagaEmprego(BaseModel):
    titulo_normalizado: Literal
    senioridade: Literal
    descricao_resumida: str
    remoto: bool
    salario: Optional
    skills: List[Habilidade]


Esta abordagem garante que o dado extraído já nasça validado. Se o LLM alucinar e retornar uma string no campo valor_minimo, o Pydantic lançará um erro de validação, permitindo que o pipeline descarte o registro ou tente uma correção automática (Retry with Feedback).30
5.2. Prompt Engineering para Normalização e Inferência
O prompt enviado ao LLM deve ser projetado para realizar tarefas cognitivas complexas que Regex não consegue.
Normalização de Títulos: Uma vaga com título "Engenheiro de Dados II - Foco em Big Data" deve ser normalizada para Data Engineer e senioridade Pleno. O prompt deve conter instruções explícitas de classificação baseadas em palavras-chave e anos de experiência exigidos.27
Inferência de Salários: Vagas frequentemente apresentam salários em formatos variados ("100k/ano", "R$ 50/hora"). O LLM deve ser instruído a normalizar tudo para uma base comum (ex: mensal) e separar bônus de salário base.32 O uso de técnicas de Chain-of-Thought (pedir para o modelo explicar o raciocínio antes de gerar o JSON) aumenta significativamente a precisão em cálculos complexos.34
5.3. Estratégias de Redução de Custo
Processar milhares de vagas com LLMs pode ser custoso. Estratégias de otimização incluem:
Limpeza Prévia do HTML: Antes de enviar o texto para o LLM, o HTML deve ser limpo. Scripts Python (usando bibliotecas como trafilatura ou BeautifulSoup) devem remover scripts, estilos, menus de navegação, rodapés e comentários, mantendo apenas o texto do corpo da vaga. Isso reduz a contagem de tokens em até 70%.
Seleção de Modelo: Para tarefas de extração, modelos "Flash" ou "Mini" (Gemini 1.5 Flash, GPT-4o-mini) demonstraram desempenho comparável aos modelos maiores (GPT-4, Gemini Pro) a uma fração do custo e com latência muito menor.35
6. Modelagem de Dados e Persistência: A Camada Gold
A camada final do pipeline deve ser otimizada para responder a perguntas de negócio. A modelagem dimensional (Kimball) é a abordagem mais adequada para análise de tendências.36
6.1. Star Schema para Mercado de Trabalho
O modelo de dados central gira em torno da tabela fato de vagas, cercada por dimensões de contexto.
Tabela Fato (fact_vagas): Contém as métricas e as chaves estrangeiras. A granularidade é "uma vaga anunciada em uma data específica".
vaga_sk (Surrogate Key)
data_anuncio_sk (FK Tempo)
empresa_sk (FK Empresa)
localidade_sk (FK Local)
salario_mensal_min
salario_mensal_max
is_remoto (Degenerate Dimension)
Dimensão Habilidades (dim_skills e Bridge Table): Como uma vaga possui múltiplas habilidades (relação N:N), a modelagem clássica exige uma tabela de ponte (fact_vaga_skill). No entanto, bancos de dados modernos como DuckDB e PostgreSQL suportam tipos de dados semi-estruturados (Arrays, JSONB) de forma eficiente. Armazenar a lista de habilidades como um array `` dentro da tabela fato simplifica a carga e, graças às funções de UNNEST, permite análises de co-ocorrência ("Quais skills aparecem mais com Python?") com performance excepcional.37

Estratégia
Prós
Contras
Recomendação
Tabela de Ponte (Normalizada)
Padrão clássico, integridade referencial forte, compatível com qualquer ferramenta de BI.
Queries complexas (muitos JOINs), aumento do volume de linhas.
Ideal para ferramentas de BI legadas (Tableau, PowerBI antigo).
Array/JSON (Desnormalizada)
Carga simples, queries compactas, leitura rápida no DuckDB/BigQuery.
Requer suporte do banco de dados a funções de array, integridade referencial mais fraca.
Recomendada para DuckDB/MDS moderno. 37

6.2. DuckDB e Parquet: Performance e Compressão
A persistência física dos dados na camada Gold deve ser feita em formato Parquet. Este formato colunar oferece taxas de compressão superiores e permite que o motor de consulta leia apenas as colunas necessárias para uma análise (ex: ler apenas a coluna salario para calcular a média, ignorando a coluna descricao que é pesada). O DuckDB brilha neste cenário, atuando como uma interface SQL sobre esses arquivos, permitindo joins complexos e agregações em memória sem a latência de rede de um Data Warehouse na nuvem.3
7. Orquestração e DevOps: Automatizando o Ciclo de Vida
A operacionalização do pipeline transforma scripts isolados em um produto de dados confiável.
7.1. GitHub Actions como Orquestrador Leve
Para pipelines de extração de dados que rodam em batch (ex: uma vez por dia), o GitHub Actions oferece uma infraestrutura "Serverless" gratuita (até 2000 minutos/mês) e altamente integrada ao código.39
Um workflow típico .yaml realiza os seguintes passos:
Trigger: Cron schedule (0 8 * * *) para rodar toda manhã.
Checkout: Baixa o código do repositório.
Cache: Restaura dependências Python e binários do navegador Camoufox/Playwright de execuções anteriores para acelerar o boot.
Scraping (Bronze): Executa os scripts de coleta, salvando os resultados temporários.
Processamento (Silver/Gold): Executa o DuckDB para transformar e validar os dados.
Persistência: Faz upload dos arquivos Parquet resultantes para um bucket S3 (usando credenciais armazenadas em GitHub Secrets) ou commita pequenos datasets de volta ao repositório (Git Scraping) para versionamento de dados leves.40
7.2. Monitoramento e Tratamento de Falhas
A confiabilidade do pipeline depende de observabilidade.
Alertas: O pipeline deve ser configurado para enviar notificações (via Slack Webhook ou Email) em caso de falha na execução ou se a volumetria de dados coletados for anomalamente baixa (indicando possível mudança no layout do site ou bloqueio de bot).
Logs Estruturados: Em vez de print(), usar bibliotecas de logging que geram saídas JSON estruturadas, facilitando a análise posterior de erros de parsing ou timeouts de rede.
Backfilling: A arquitetura deve permitir a reexecução do pipeline para datas passadas, caso uma falha de proxy impeça a coleta de um dia específico. O particionamento dos dados no S3 (/date=2025-01-15/) facilita a substituição ou preenchimento de partições específicas.16
8. Conclusão
A construção de um pipeline de Engenharia de Dados para web scraping de vagas de tecnologia é um exercício de equilíbrio entre inovação técnica, rigor analítico e responsabilidade jurídica. A arquitetura proposta neste relatório — ancorada no poder de evasão do Camoufox, na inteligência semântica dos LLMs com validação Pydantic, e na eficiência de processamento do DuckDB — representa o estado da arte para 2025.
Esta abordagem supera as limitações dos scrapers legados, oferecendo resiliência contra mudanças de layout e bloqueios, ao mesmo tempo que adere a um modelo de dados robusto capaz de gerar insights de negócio profundos. Mais importante, ao incorporar princípios de Privacy by Design e conformidade com a LGPD desde a concepção, o pipeline mitiga riscos jurídicos, garantindo que a inteligência de mercado gerada seja um ativo estratégico seguro e sustentável para a organização.
Referências citadas
Datasets - Hugging Face, acessado em janeiro 15, 2026, https://huggingface.co/datasets?other=portuguese
lukebarousse/data_jobs · Datasets at Hugging Face, acessado em janeiro 15, 2026, https://huggingface.co/datasets/lukebarousse/data_jobs
DuckDB Medallion Architecture: A Complete Local Lakehouse ..., acessado em janeiro 15, 2026, https://medium.com/@datatomas/duckdb-medallion-architecture-a-complete-local-lakehouse-guide-0f1944b6bcdf
The guide to structured outputs and function calling with LLMs - Agenta.ai, acessado em janeiro 15, 2026, https://agenta.ai/blog/the-guide-to-structured-outputs-and-function-calling-with-llms
Brazil's New Data Protection Law: The LGPD - cyber/data/privacy insights, acessado em janeiro 15, 2026, https://cdp.cooley.com/brazils-new-data-protection-law-the-lgpd/
Data protection laws in Brazil, acessado em janeiro 15, 2026, https://www.dlapiperdataprotection.com/index.html?t=law&c=BR
Navigating technical, legal, and ethical hurdles to scraping LinkedIn data for academic researchNavegando pelas barreiras técnicas, legais e éticas na extração de dados do LinkedIn para pesquisas acadêmicas - ResearchGate, acessado em janeiro 15, 2026, https://www.researchgate.net/publication/388339011_Navigating_technical_legal_and_ethical_hurdles_to_scraping_LinkedIn_data_for_academic_researchNavegando_pelas_barreiras_tecnicas_legais_e_eticas_na_extracao_de_dados_do_LinkedIn_para_pesquisas_academi
Brazil's Guidance on Legitimate Interest - Securiti.ai, acessado em janeiro 15, 2026, https://securiti.ai/brazil-guidance-on-degitimate-interest/
LinkedIn Data Extraction 2025: Tools, Ethics & Best Practices - The Data Scientist, acessado em janeiro 15, 2026, https://thedatascientist.com/linkedin-data-extraction-2025-tools-ethics-best-practices/
Brazil Data Protection Law – Litigation in the Context of Employment - Littler Mendelson, acessado em janeiro 15, 2026, https://www.littler.com/news-analysis/asap/brazil-data-protection-law-litigation-context-employment
Federal Court Rules in Favor of LinkedIn's Breach of Contract Claim after Six Years of CFAA Data Scraping Litigation | Privacy World, acessado em janeiro 15, 2026, https://www.privacyworld.blog/2022/11/federal-court-rules-in-favor-of-linkedins-breach-of-contract-claim-after-six-years-of-cfaa-data-scraping-litigation/
Is Web Scraping Legal? Key Insights and Guidelines You Need to Know | ScrapingBee, acessado em janeiro 15, 2026, https://www.scrapingbee.com/blog/is-web-scraping-legal/
Data Protection in Brazil: Applying Text Mining in Court Documents - MDPI, acessado em janeiro 15, 2026, https://www.mdpi.com/2673-4591/87/1/57
Building a Postgres Data Warehouse using DuckDB, acessado em janeiro 15, 2026, https://blobs.duckdb.org/events/duckdb-amsterdam-meetup2/marco-slot-crunchy-data-building-a-postgres-data-warehouse-using-duckdb.pdf
Building an End-to-End Data Engineering Pipeline with DuckDB and Python, acessado em janeiro 15, 2026, https://dev.to/satyam_gupta/building-an-end-to-end-data-engineering-pipeline-with-duckdb-and-python-53g2
Large scale web scraping - storing data directly in postgres or use S3 as an intermediate step? : r/dataengineering - Reddit, acessado em janeiro 15, 2026, https://www.reddit.com/r/dataengineering/comments/132wwue/large_scale_web_scraping_storing_data_directly_in/
Analytics engineering for fact tables | Metabase Learn, acessado em janeiro 15, 2026, https://www.metabase.com/learn/grow-your-data-skills/data-fundamentals/fact-table
Dimensional modeling in Microsoft Fabric Warehouse: Fact tables, acessado em janeiro 15, 2026, https://learn.microsoft.com/en-us/fabric/data-warehouse/dimensional-modeling-fact-tables
7 Best Python Web Scraping Libraries for 2025 | ScrapingBee, acessado em janeiro 15, 2026, https://www.scrapingbee.com/blog/best-python-web-scraping-libraries/
How to Scrape With Camoufox to Bypass Antibot Technology | ScrapingBee, acessado em janeiro 15, 2026, https://www.scrapingbee.com/blog/how-to-scrape-with-camoufox-to-bypass-antibot-technology/
daijro/camoufox: Anti-detect browser - GitHub, acessado em janeiro 15, 2026, https://github.com/daijro/camoufox
The Best Residential Proxies for Web Scraping in 2025: A Deep Dive - Reddit, acessado em janeiro 15, 2026, https://www.reddit.com/r/PrivatePackets/comments/1jjeowm/the_best_residential_proxies_for_web_scraping_in/
10 Best Residential Proxy Providers in 2025: Full Comparison - Marsproxies.com, acessado em janeiro 15, 2026, https://marsproxies.com/blog/best-residential-proxy-providers/
Scraper's Honest Review: Top Proxy Providers in 2025 (Plus a Bonus Pick), acessado em janeiro 15, 2026, https://scrapecreators.com/blog/proxy-provider-comparison-2025
9 Best Residential Proxies in 2025 for Web Scraping and Data Collection - Scrapeless, acessado em janeiro 15, 2026, https://www.scrapeless.com/en/blog/best-residential-proxies
Top 5 Residential Proxy Providers for Web Scraping - Scrapfly, acessado em janeiro 15, 2026, https://scrapfly.io/blog/posts/top-5-residential-proxy-providers
Parsing Resumes with LLMs: A Guide to Structuring CVs for HR Automation - Datumo, acessado em janeiro 15, 2026, https://www.datumo.io/blog/parsing-resumes-with-llms-a-guide-to-structuring-cvs-for-hr-automation
Structured outputs | Gemini API - Google AI for Developers, acessado em janeiro 15, 2026, https://ai.google.dev/gemini-api/docs/structured-output
Every Way To Get Structured Output From LLMs | BAML Blog, acessado em janeiro 15, 2026, https://boundaryml.com/blog/structured-output-from-llms
How to Use Pydantic for LLMs: Schema, Validation & Prompts description, acessado em janeiro 15, 2026, https://pydantic.dev/articles/llm-intro
Pydantic: Simplifying Data Validation in Python, acessado em janeiro 15, 2026, https://realpython.com/python-pydantic/
JSON prompting for LLMs - IBM Developer, acessado em janeiro 15, 2026, https://developer.ibm.com/articles/json-prompting-llms/
Mastering JSON Prompting for LLMs - MachineLearningMastery.com, acessado em janeiro 15, 2026, https://machinelearningmastery.com/mastering-json-prompting-for-llms/
Prompt Engineer: Analyzing Skill Requirements in the AI Job Market - arXiv, acessado em janeiro 15, 2026, https://arxiv.org/html/2506.00058v1
Structured output | Generative AI on Vertex AI - Google Cloud Documentation, acessado em janeiro 15, 2026, https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/control-generated-output
Understand star schema and the importance for Power BI - Microsoft Learn, acessado em janeiro 15, 2026, https://learn.microsoft.com/en-us/power-bi/guidance/star-schema
Shredding Deeply Nested JSON, One Vector at a Time - DuckDB, acessado em janeiro 15, 2026, https://duckdb.org/2023/03/03/json
JSON Schema with DuckDB - Reddit, acessado em janeiro 15, 2026, https://www.reddit.com/r/DuckDB/comments/1jdbpl3/json_schema_with_duckdb/
swyxio/gh-action-data-scraping - GitHub, acessado em janeiro 15, 2026, https://github.com/swyxio/gh-action-data-scraping
How to Use GitHub Actions to Automate Data Scraping | by Tom Willcocks - Medium, acessado em janeiro 15, 2026, https://medium.com/data-analytics-at-nesta/how-to-use-github-actions-to-automate-data-scraping-299690cd8bdb
