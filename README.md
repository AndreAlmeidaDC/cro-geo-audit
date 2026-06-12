# CRO + GEO Audit Toolkit

**Auditoria autônoma de Conversion Rate Optimization (CRO) e Generative Engine Optimization (GEO) para qualquer website.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Agent Skill](https://img.shields.io/badge/Agent-Skill-purple.svg)](SKILL.md)

---

## O que é

Este toolkit realiza uma análise completa e **100% autônoma** de qualquer website, cobrindo duas dimensões críticas para negócios digitais:

- **CRO (Conversion Rate Optimization)** — Identifica problemas que impedem visitantes de se tornarem clientes: UX, copy, CTAs, funil, prova social, performance e segurança.
- **GEO (Generative Engine Optimization)** — Avalia a visibilidade do site em motores de busca generativos como ChatGPT, Gemini, Perplexity e Copilot.

A análise GEO é totalmente independente — não depende de ferramentas externas como NAIA, Otterly ou HubSpot AI Grader. Todos os dados são coletados e pontuados pelos scripts incluídos.

---

## Estrutura do Repositório

```
cro-geo-audit/
├── README.md                              # Este arquivo
├── SKILL.md                               # Instruções para uso como Agent Skill
├── LICENSE                                # Licença MIT
├── docs/
│   └── ARCHITECTURE.md                    # Arquitetura técnica detalhada
├── scripts/
│   ├── technical_audit.py                 # Auditoria técnica (performance, headers, SSL)
│   ├── seo_meta_check.py                  # Análise de SEO e meta tags
│   └── geo_audit.py                       # Análise GEO autônoma completa
├── references/
│   ├── cro-checklist.md                   # Checklist CRO para navegação manual
│   ├── geo-checklist.md                   # Checklist GEO com critérios de avaliação
│   └── scoring-rubric.md                  # Rubrica de pontuação (CRO, UX, SEO, Perf, Seg, GEO)
└── templates/
    ├── report-template.md                 # Template do relatório final em Markdown
    └── dashboard-data-template.ts         # Template de dados para dashboard interativo
```

---

## Scripts

### 1. `technical_audit.py` — Auditoria Técnica

Coleta dados de performance, headers HTTP, segurança, robots.txt, sitemap e SSL.

```bash
python scripts/technical_audit.py https://exemplo.com.br > resultado_tecnico.json
```

**O que analisa:**

| Categoria | Métricas |
|-----------|----------|
| Performance | DNS, TCP, SSL, TTFB, tempo total de resposta |
| Headers HTTP | Cache-Control, Content-Type, Server, compressão |
| Segurança | HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy |
| robots.txt | Conteúdo, regras de bloqueio para bots de IA |
| sitemap.xml | Existência, contagem de URLs |
| SSL | Validade do certificado, emissor, expiração |

---

### 2. `seo_meta_check.py` — Análise de SEO e Meta Tags

Extrai e avalia meta tags, Open Graph, Schema.org e estrutura de headings de múltiplas páginas.

```bash
python scripts/seo_meta_check.py \
  https://exemplo.com.br \
  https://exemplo.com.br/produtos \
  https://exemplo.com.br/blog \
  > resultado_seo.json
```

**O que analisa por página:**

| Critério | Avaliação |
|----------|-----------|
| Title tag | Comprimento (30-65 chars ideal), presença de keywords |
| Meta description | Comprimento (120-160 chars ideal), qualidade |
| Canonical URL | Presença e consistência |
| Open Graph | og:title, og:description, og:image, og:type |
| Twitter Card | Tipo e completude |
| Heading hierarchy | Contagem de H1 (deve ser 1), estrutura H2-H4 |
| Schema.org JSON-LD | Tipos presentes, completude |
| Imagens sem alt | Contagem e URLs |
| Links internos/externos | Contagem e proporção |

---

### 3. `geo_audit.py` — Análise GEO Autônoma

Este é o script principal. Realiza uma análise completa de Generative Engine Optimization sem dependência de ferramentas externas.

```bash
python scripts/geo_audit.py \
  https://exemplo.com.br \
  --brand "Nome da Marca" \
  --competitors "concorrente1,concorrente2" \
  > resultado_geo.json
```

**Análises realizadas:**

#### A. Acessibilidade para Crawlers de IA (25 pontos)

Verifica o `robots.txt` para 12 crawlers de IA e classifica cada um em 3 estados:

| Status | Significado | Penalidade |
|--------|-------------|------------|
| `allowed` | Sem restrições | Nenhuma |
| `allowed_restricted` | Allow: / com Disallow em subpastas privadas (ex: /dashboard) | Nenhuma |
| `blocked` | Disallow: / sem Allow correspondente | -5 pts (crítico) ou -2 pts (secundário) |

**Crawlers verificados:** GPTBot, ChatGPT-User, Google-Extended, Googlebot, Bingbot, anthropic-ai, ClaudeBot, PerplexityBot, Bytespider, CCBot, FacebookBot, cohere-ai.

#### B. Qualidade de Dados Estruturados (20 pontos)

Extrai e avalia blocos JSON-LD, verificando presença de Schema types: Organization, WebSite, Product/SoftwareApplication, FAQPage, Article, BreadcrumbList, HowTo, LocalBusiness.

#### C. Citabilidade do Conteúdo (20 pontos)

Analisa fatores que aumentam a probabilidade de citação por IAs generativas: conteúdo FAQ, estatísticas numéricas, citações com fonte, listas estruturadas, tabelas, hierarquia de headings, e profundidade do conteúdo.

#### D. Descoberta e Análise Multi-Página

Descobre páginas internas usando 4 métodos:
1. Links `href` tradicionais do HTML
2. Caminhos JavaScript-embedded (SPAs e plataformas no-code)
3. Descoberta via `sitemap.xml`
4. Probing de páginas comuns (/about, /faq, /pricing, /como-funciona, etc.)

Analisa até 10 páginas adicionais para Schema, citabilidade e qualidade de conteúdo.

#### E. Presença no Google (10 pontos)

Verifica a presença da marca nos resultados de busca do Google.

#### F. Meta Tags e Open Graph (15 pontos)

Avalia completude de title, description, og:title, og:description, og:image, og:type.

#### G. Arquitetura de Conteúdo (10 pontos)

Avalia hierarquia de headings (H1 único, H2+), links internos/externos, e volume de conteúdo.

#### H. Score GEO Final

Calcula um score de 0-100 com nota (A-F) e veredicto:

| Faixa | Nota | Veredicto |
|-------|------|-----------|
| 80-100 | A | Excelente visibilidade em IA |
| 60-79 | B | Boa visibilidade, com espaço para melhorias |
| 40-59 | C | Visibilidade moderada, precisa de atenção |
| 20-39 | D | Visibilidade fraca, ações urgentes necessárias |
| 0-19 | F | Praticamente invisível para IAs |

#### I. Recomendações Priorizadas

Gera recomendações específicas e acionáveis, cada uma com: prioridade (critical/high/medium/low), categoria, título, descrição, impacto, esforço e ação concreta.

#### J. Prompts de Teste de Visibilidade

Gera 15 prompts em português para testar manualmente a visibilidade da marca em ChatGPT, Gemini, Perplexity e Copilot.

---

## Exemplo de Saída

Exemplo de execução no site revisaconta.com.br:

```json
{
  "summary": {
    "overall_score": 71,
    "grade": "B",
    "verdict": "Boa visibilidade, com espaço para melhorias",
    "pages_discovered": 20,
    "pages_analyzed": 11,
    "total_recommendations": 5,
    "critical_issues": 0,
    "high_issues": 1,
    "medium_issues": 3,
    "low_issues": 1
  }
}
```

---

## Requisitos

- **Python 3.8+**
- Acesso à internet para buscar as páginas do site alvo

Três dos quatro scripts usam exclusivamente a biblioteca padrão do Python (`urllib`, `ssl`, `json`, `re`, `html.parser`). O `seo_meta_check.py` requer `requests` e `beautifulsoup4`:

```bash
pip install -r requirements.txt
```

Se as dependências não estiverem disponíveis, o script falha com um erro JSON estruturado e a skill aplica o fallback documentado no SKILL.md (inspeção das páginas via ferramenta HTTP da plataforma).

---

## Uso como Agent Skill (multiplataforma)

Este repositório segue o formato Agent Skill (um `SKILL.md` com instruções e arquivos de apoio) e roda em qualquer plataforma de agentes que leia esse formato. A skill detecta as capacidades do ambiente na Fase 0 e adapta as fases dependentes de browser e de conversão de PDF com fallbacks documentados (veja `references/environment-adapters.md`).

**Claude (claude.ai / Claude Code):**
1. Faça download do repositório
2. Adicione a pasta como skill (em claude.ai: Settings > Capabilities > Skills; no Claude Code: pasta de skills do projeto)
3. O Claude detecta a skill pelo `SKILL.md`

**Manus:**
1. Faça download do repositório
2. Coloque em `/home/ubuntu/skills/cro-geo-audit/`
3. O Manus detecta a skill pelo `SKILL.md`

**Outras plataformas:**
Qualquer agente com execução de Python e acesso HTTP consegue rodar o fluxo completo. Sem browser interativo, as Fases 4 e 5 operam nos modos de fallback descritos no `SKILL.md`.

Consulte o arquivo [SKILL.md](SKILL.md) para o workflow completo de 8 fases da auditoria.

---

## Documentação

| Documento | Descrição |
|-----------|-----------|
| [SKILL.md](SKILL.md) | Workflow completo de auditoria em 7 fases |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Arquitetura técnica e decisões de design |
| [references/cro-checklist.md](references/cro-checklist.md) | Checklist CRO para avaliação manual de páginas |
| [references/geo-checklist.md](references/geo-checklist.md) | Checklist GEO com critérios e pontuação |
| [references/scoring-rubric.md](references/scoring-rubric.md) | Rubrica de pontuação detalhada para todas as categorias |
| [templates/report-template.md](templates/report-template.md) | Template para o relatório final |
| [templates/dashboard-data-template.ts](templates/dashboard-data-template.ts) | Template TypeScript para dashboard interativo |

---

## Contribuindo

Contribuições são bem-vindas. Para contribuir:

1. Fork o repositório
2. Crie uma branch (`git checkout -b feature/minha-melhoria`)
3. Commit suas alterações (`git commit -m 'Adiciona minha melhoria'`)
4. Push para a branch (`git push origin feature/minha-melhoria`)
5. Abra um Pull Request

---

## Licença

Este projeto está licenciado sob a [MIT License](LICENSE).

---

## Verificação de versão com consentimento

Esta skill foi padronizada para operar como uma skill atualizável com consentimento humano. No início de um uso relevante, quando houver internet e ferramentas Git ou HTTP disponíveis, o agente deve consultar o repositório de origem, ler o `README.md` e o `CHANGELOG.md` quando existirem, comparar a cópia local com a versão upstream e resumir as novidades encontradas.

Essa checagem não autoriza autoatualização silenciosa. A regra é: **verificar, explicar e perguntar**. O agente deve informar o que mudou, dizer se a mudança impacta a tarefa atual e pedir autorização explícita antes de atualizar qualquer arquivo local da skill. O protocolo completo está em [`references/version-check.md`](references/version-check.md).

## Autor

**André Almeida** — Cofundador da [RevisaConta](https://revisaconta.com.br) e [+Seguro](https://maisseguro.com.br). Curador e orquestrador de agentes de IA.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Andre_Almeida-blue?logo=linkedin)](https://www.linkedin.com/in/andrealmeida/)
