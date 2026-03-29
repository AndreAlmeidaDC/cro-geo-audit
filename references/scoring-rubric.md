# Scoring Rubric — CRO/GEO Audit

## Table of Contents
1. Visão Geral do Sistema de Pontuação
2. Score CRO (Conversion Rate Optimization)
3. Score UX (User Experience)
4. Score SEO (Search Engine Optimization)
5. Score Performance
6. Score Segurança
7. Score GEO (Generative Engine Optimization)
8. Score Geral

---

## 1. Visão Geral do Sistema de Pontuação

Cada categoria é avaliada de 0 a 100 pontos. O score geral é a média ponderada das 6 categorias.

| Categoria | Peso | Descrição |
|-----------|------|-----------|
| CRO | 25% | Capacidade de converter visitantes em clientes |
| UX | 20% | Experiência do usuário, fluxos e usabilidade |
| SEO | 20% | Otimização para mecanismos de busca tradicionais |
| Performance | 15% | Velocidade de carregamento e métricas técnicas |
| Segurança | 10% | Headers de segurança, SSL, boas práticas |
| GEO | 10% | Visibilidade em motores de busca generativos (IA) |

**Classificação por faixa:**

| Faixa | Classificação | Cor sugerida |
|-------|--------------|-------------|
| 0-25 | Crítico | Vermelho |
| 26-50 | Insuficiente | Laranja |
| 51-70 | Regular | Amarelo |
| 71-85 | Bom | Verde claro |
| 86-100 | Excelente | Verde |

---

## 2. Score CRO (Conversion Rate Optimization)

| Critério | Pontos | Como avaliar |
|----------|--------|-------------|
| Proposta de valor clara no hero | 0-15 | 15 = benefício + número concreto; 8 = genérico; 0 = ausente |
| CTA principal above the fold | 0-10 | 10 = visível e com texto de ação; 5 = presente mas fraco; 0 = ausente |
| Preço visível antes do cadastro | 0-15 | 15 = preço claro na landing; 8 = na página de produtos; 0 = só após cadastro |
| Prova social com resultados | 0-15 | 15 = depoimentos reais com valores; 8 = números genéricos; 0 = ausente |
| Garantia explícita | 0-10 | 10 = garantia clara; 5 = política de reembolso escondida; 0 = ausente |
| Funil sem fricção | 0-15 | 15 = checkout < 3 etapas; 8 = 4-5 etapas; 0 = > 5 etapas ou quebrado |
| Links funcionais (sem 404) | 0-10 | 10 = todos ok; 5 = 1-2 quebrados; 0 = > 2 quebrados |
| Ancoragem de preço | 0-10 | 10 = mostra valor recuperável vs custo; 5 = desconto visível; 0 = preço seco |

---

## 3. Score UX (User Experience)

| Critério | Pontos | Como avaliar |
|----------|--------|-------------|
| Navegação clara e consistente | 0-15 | 15 = menu intuitivo, breadcrumbs; 8 = ok mas confuso; 0 = sem navegação |
| Formulários simples | 0-15 | 15 = < 3 campos + login social; 8 = 4-5 campos; 0 = > 5 campos |
| Feedback visual (loading, sucesso, erro) | 0-10 | 10 = feedback em todas ações; 5 = parcial; 0 = ausente |
| Responsividade mobile | 0-15 | 15 = perfeito; 8 = funcional com problemas; 0 = quebrado |
| Consistência visual | 0-10 | 10 = design system coerente; 5 = parcialmente; 0 = inconsistente |
| Fluxo de recuperação (esqueci senha) | 0-10 | 10 = funcional; 5 = existe mas com problemas; 0 = ausente |
| Linguagem adequada ao público | 0-15 | 15 = linguagem do público-alvo; 8 = mista; 0 = jargão técnico |
| Acessibilidade básica (contraste, alt) | 0-10 | 10 = WCAG AA; 5 = parcial; 0 = sem acessibilidade |

---

## 4. Score SEO (Search Engine Optimization)

| Critério | Pontos | Como avaliar |
|----------|--------|-------------|
| Title tags otimizados (30-65 chars) | 0-15 | Executar `seo_meta_check.py` |
| Meta descriptions (120-160 chars) | 0-15 | Executar `seo_meta_check.py` |
| Open Graph completo | 0-10 | Executar `seo_meta_check.py` |
| Schema JSON-LD presente | 0-15 | Executar `seo_meta_check.py` |
| Hierarquia de headings (1x H1) | 0-10 | Executar `seo_meta_check.py` |
| Sitemap.xml funcional | 0-10 | Executar `technical_audit.py` |
| Alt text em imagens | 0-10 | Executar `seo_meta_check.py` |
| Canonical tags | 0-5 | Executar `seo_meta_check.py` |
| Blog com conteúdo indexável | 0-10 | Navegação manual |

---

## 5. Score Performance

| Critério | Pontos | Como avaliar |
|----------|--------|-------------|
| TTFB < 200ms | 0-25 | 25 = < 200ms; 15 = 200-500ms; 5 = 500ms-1s; 0 = > 1s |
| Tempo total < 2s | 0-25 | 25 = < 2s; 15 = 2-4s; 5 = 4-6s; 0 = > 6s |
| Tamanho da página < 2MB | 0-15 | 15 = < 2MB; 8 = 2-5MB; 0 = > 5MB |
| Cache headers presentes | 0-15 | 15 = cache-control com max-age; 8 = parcial; 0 = ausente |
| Compressão (gzip/brotli) | 0-10 | 10 = presente; 0 = ausente |
| HTTP/2 ou HTTP/3 | 0-10 | 10 = sim; 0 = HTTP/1.1 |

---

## 6. Score Segurança

| Critério | Pontos | Como avaliar |
|----------|--------|-------------|
| SSL válido | 0-20 | Executar `technical_audit.py` |
| HSTS | 0-15 | Executar `technical_audit.py` |
| CSP (Content Security Policy) | 0-15 | Executar `technical_audit.py` |
| X-Content-Type-Options | 0-10 | Executar `technical_audit.py` |
| X-Frame-Options | 0-10 | Executar `technical_audit.py` |
| Referrer-Policy | 0-10 | Executar `technical_audit.py` |
| Permissions-Policy | 0-10 | Executar `technical_audit.py` |
| X-XSS-Protection | 0-10 | Executar `technical_audit.py` |

---

## 7. Score GEO (Generative Engine Optimization)

O score GEO é calculado **automaticamente** pelo script `geo_audit.py`. O script retorna um `percentage` (0-100) que deve ser usado diretamente como o score GEO.

### Sub-categorias calculadas pelo geo_audit.py:

| Sub-categoria | Pontos Máx | Como é calculado automaticamente |
|---------------|-----------|----------------------------------|
| AI Crawler Accessibility | 25 | Análise do robots.txt: 25 pts base, -5 por crawler crítico `blocked`, -2 por secundário `blocked`. Crawlers `allowed_restricted` (Allow: / com Disallow de subpastas privadas) NÃO são penalizados |
| Structured Data Quality | 20 | Análise de JSON-LD: +4 se tem JSON-LD, +4 Organization, +3 Product, +3 FAQ, +2 Breadcrumb, +2 WebSite, +2 Article |
| Content Citability | 20 | Análise de conteúdo: +4 FAQ, +3 estatísticas, +3 citações, +3 listas, +2 tabelas, +3 headings, +2 profundidade |
| Meta & OG Completeness | 15 | Análise de meta tags: +3 title, +3 description, +2 og:title, +2 og:description, +3 og:image, +2 og:type |
| Content Architecture | 10 | Análise estrutural: +3 se 1x H1, +2 se 3+ H2, +2 se 5+ links internos, +1 se links externos, +2 se 300+ palavras |
| External Authority | 10 | Presença no Google: +5 se tem presença, +1 a +5 baseado no volume de resultados |

**Total máximo**: 100 pontos.

### Classificação GEO:

| Faixa | Nota | Veredicto |
|-------|------|-----------|
| 80-100 | A | Excelente visibilidade em IA |
| 60-79 | B | Boa visibilidade, com espaço para melhorias |
| 40-59 | C | Visibilidade moderada, precisa de atenção |
| 20-39 | D | Visibilidade fraca, ações urgentes necessárias |
| 0-19 | F | Praticamente invisível para IAs |

### Complemento manual (browser):

Além do score automático, a verificação manual via browser (Fase 4 do workflow) pode ajustar o score em até ±10 pontos:

| Critério manual | Ajuste |
|----------------|--------|
| Marca aparece em 3+ IAs | +5 |
| Marca aparece em 1-2 IAs | +2 |
| Marca não aparece em nenhuma IA | -5 |
| Presente em 3+ diretórios verificados | +5 |
| Backlinks de .gov.br ou .edu.br | +3 |
| Menções em mídia de autoridade | +2 |

---

## 8. Score Geral

O score geral é calculado como média ponderada:

```
Score Geral = (CRO × 0.25) + (UX × 0.20) + (SEO × 0.20) + (Performance × 0.15) + (Segurança × 0.10) + (GEO × 0.10)
```

Arredondar para inteiro. Classificar conforme tabela de faixas na seção 1.
