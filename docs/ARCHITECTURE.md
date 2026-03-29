# Arquitetura Técnica — CRO + GEO Audit Toolkit

## Visão Geral

O toolkit é composto por 3 scripts Python independentes que coletam dados de qualquer website e produzem relatórios JSON estruturados. Os scripts foram projetados para funcionar sem dependências externas, utilizando exclusivamente a biblioteca padrão do Python 3.8+.

---

## Princípios de Design

### 1. Zero Dependências Externas

Todos os scripts utilizam apenas módulos da biblioteca padrão do Python:

| Módulo | Uso |
|--------|-----|
| `urllib.request` / `urllib.error` / `urllib.parse` | Requisições HTTP e parsing de URLs |
| `ssl` | Verificação de certificados SSL |
| `socket` | Resolução DNS e conexões TCP |
| `json` | Serialização/deserialização de dados |
| `re` | Expressões regulares para parsing de conteúdo |
| `html.parser` | Parsing de HTML sem BeautifulSoup |
| `datetime` | Timestamps e cálculos de tempo |

Esta decisão garante que os scripts funcionem em qualquer ambiente Python 3.8+ sem instalação de pacotes, incluindo ambientes restritos como sandboxes de IA e servidores sem acesso a PyPI.

### 2. Saída JSON Estruturada

Todos os scripts produzem JSON para stdout, permitindo composição via pipes e integração com outras ferramentas. Logs de progresso são enviados para stderr para não contaminar a saída.

### 3. Análise Autônoma

O script `geo_audit.py` foi projetado para substituir ferramentas externas como NAIA, Otterly e HubSpot AI Grader. Toda a análise é feita localmente, sem APIs de terceiros.

---

## Arquitetura dos Scripts

### `technical_audit.py`

```
Input: URL do site
  │
  ├─ Resolução DNS (socket.getaddrinfo)
  ├─ Conexão TCP (socket.create_connection)
  ├─ Handshake SSL (ssl.wrap_socket)
  ├─ Requisição HTTP (urllib.request.urlopen)
  │   ├─ Headers de resposta
  │   ├─ Tempo de resposta (TTFB, total)
  │   └─ Tamanho da página
  ├─ Verificação de robots.txt
  ├─ Verificação de sitemap.xml
  └─ Verificação de certificado SSL
  │
Output: JSON com métricas técnicas
```

### `seo_meta_check.py`

```
Input: Lista de URLs
  │
  ├─ Para cada URL:
  │   ├─ Fetch HTML
  │   ├─ Parse com HTMLParser customizado
  │   │   ├─ Extrai <title>
  │   │   ├─ Extrai <meta> tags (name, property, content)
  │   │   ├─ Extrai JSON-LD (<script type="application/ld+json">)
  │   │   ├─ Conta headings (H1-H4)
  │   │   ├─ Conta imagens sem alt
  │   │   └─ Conta links internos/externos
  │   └─ Calcula score SEO por página
  │
Output: JSON com análise SEO por página
```

### `geo_audit.py`

```
Input: URL + brand (opcional) + competitors (opcional)
  │
  ├─ 1. Análise de robots.txt
  │   ├─ Fetch robots.txt
  │   ├─ Parse de regras por User-agent
  │   ├─ Verificação de 12 crawlers de IA
  │   └─ Classificação: allowed / allowed_restricted / blocked
  │
  ├─ 2. Análise de dados estruturados (homepage)
  │   ├─ Fetch HTML
  │   ├─ Parse com SchemaExtractor (HTMLParser)
  │   │   ├─ JSON-LD blocks
  │   │   ├─ Meta tags e Open Graph
  │   │   ├─ Citabilidade (FAQ, stats, citations, lists, tables)
  │   │   └─ Arquitetura de conteúdo (headings, links, word count)
  │   └─ Identificação de Schema types
  │
  ├─ 3. Descoberta e análise multi-página
  │   ├─ Método 1: Links href do HTML
  │   ├─ Método 2: Caminhos JavaScript-embedded
  │   ├─ Método 3: sitemap.xml (3 variantes)
  │   ├─ Método 4: Probing de páginas comuns
  │   ├─ Filtragem de não-conteúdo
  │   └─ Análise das top 10 páginas
  │
  ├─ 4. Presença no Google
  │   └─ Busca por "brand" OR site:domain
  │
  ├─ 5. Checklist de diretórios
  │   └─ URLs de verificação para 10 diretórios
  │
  ├─ 6. Prompts de teste de visibilidade em IA
  │   └─ 15 prompts em português
  │
  ├─ 7. Cálculo do score GEO
  │   ├─ AI Crawler Accessibility (25 pts)
  │   ├─ Structured Data Quality (20 pts)
  │   ├─ Content Citability (20 pts)
  │   ├─ Meta & OG Completeness (15 pts)
  │   ├─ Content Architecture (10 pts)
  │   └─ External Authority (10 pts)
  │
  ├─ 8. Geração de recomendações priorizadas
  │
  └─ 9. Sumário executivo
  │
Output: JSON completo com todas as análises e scores
```

---

## Decisões Técnicas

### Lógica de robots.txt (v2.0)

A versão original do parser classificava incorretamente crawlers como "blocked" quando tinham `Allow: /` mas também tinham `Disallow` para subpastas privadas (como `/dashboard`). A lógica foi corrigida para implementar a seguinte precedência:

1. Se existe uma regra específica para o User-agent do crawler, ela tem prioridade sobre regras wildcard (`*`)
2. `Disallow: /` sem `Allow: /` correspondente = **blocked**
3. `Allow: /` com `Disallow` de subpastas específicas = **allowed_restricted** (comportamento correto, não penalizado)
4. `Allow: /` sem restrições = **allowed**
5. Sem regras específicas → fallback para regras wildcard (`*`)
6. Sem regras wildcard → default **allowed**

### Descoberta Multi-Página (v2.0)

A versão original só buscava links `href` no HTML, o que falhava em sites SPA e plataformas no-code (Base44, Webflow, Wix) que renderizam conteúdo via JavaScript. A nova versão usa 4 métodos complementares:

1. **Links href tradicionais** — Funciona para sites estáticos e SSR
2. **Caminhos JavaScript-embedded** — Regex para extrair paths de strings JS
3. **sitemap.xml** — Tenta 3 variantes comuns (sitemap.xml, sitemap_index.xml, sitemap-0.xml) com suporte a sub-sitemaps
4. **Probing de páginas comuns** — Testa URLs padrão como /about, /faq, /pricing, /como-funciona

### SchemaExtractor (HTMLParser customizado)

Em vez de usar BeautifulSoup (dependência externa), o toolkit implementa um `HTMLParser` customizado que extrai simultaneamente:

- Blocos JSON-LD
- Meta tags e Open Graph
- Contagem de headings
- Contagem de listas e tabelas
- Links internos e externos
- Padrões de citabilidade (FAQ, estatísticas, citações)
- Contagem de palavras

Isso permite uma única passagem pelo HTML para coletar todos os dados necessários.

---

## Fluxo de Dados

```
                    ┌──────────────────┐
                    │   URL do Site    │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
    ┌─────────────┐ ┌──────────────┐ ┌──────────────┐
    │  technical   │ │  seo_meta    │ │  geo_audit   │
    │  _audit.py   │ │  _check.py   │ │  .py         │
    └──────┬──────┘ └──────┬───────┘ └──────┬───────┘
           │               │                │
           ▼               ▼                ▼
    ┌─────────────┐ ┌──────────────┐ ┌──────────────┐
    │  JSON:       │ │  JSON:        │ │  JSON:        │
    │  Performance │ │  SEO scores   │ │  GEO score    │
    │  Headers     │ │  Meta tags    │ │  Crawlers     │
    │  SSL         │ │  Schema       │ │  Schema       │
    │  Security    │ │  Headings     │ │  Citability   │
    └──────┬──────┘ └──────┬───────┘ │  Pages        │
           │               │         │  Directories  │
           │               │         │  Prompts      │
           │               │         │  Recs         │
           │               │         └──────┬───────┘
           │               │                │
           └───────────────┼────────────────┘
                           │
                           ▼
                 ┌──────────────────┐
                 │  Relatório Final │
                 │  (Markdown/PDF)  │
                 └──────────────────┘
```

---

## Limitações Conhecidas

1. **Sites com JavaScript-only rendering** — O fetch via `urllib` não executa JavaScript. Sites que renderizam 100% do conteúdo via JS (React SPA sem SSR) terão análise de conteúdo limitada. A descoberta multi-página mitiga parcialmente isso via sitemap e probing.

2. **Rate limiting do Google** — A verificação de presença no Google pode retornar 0 resultados se o IP estiver com rate limit. Isso afeta apenas a subcategoria "External Authority" (10 pontos).

3. **Plataformas no-code com routing customizado** — Algumas plataformas usam esquemas de routing não-padrão que podem não ser detectados pelos 4 métodos de descoberta.

4. **Conteúdo dinâmico** — Conteúdo carregado via AJAX/fetch após o carregamento inicial não é capturado pelo parser HTML.

---

## Changelog

### v2.0 (2026-03-29)
- Corrigida lógica de robots.txt para diferenciar `allowed`, `allowed_restricted` e `blocked`
- Adicionada descoberta multi-página com 4 métodos (href, JS paths, sitemap, probing)
- Adicionado logging de progresso para stderr
- Adicionada validação de tamanho mínimo de página (>200 bytes)
- Adicionado tracking de status HTTP por página descoberta

### v1.0 (2026-03-28)
- Release inicial com análise de robots.txt, Schema.org, citabilidade, presença no Google, diretórios, prompts de teste e scoring GEO
