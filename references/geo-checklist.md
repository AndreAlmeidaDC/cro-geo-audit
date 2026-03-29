# GEO (Generative Engine Optimization) Checklist

## Visão Geral

Esta checklist é usada em conjunto com o script `geo_audit.py` que realiza a análise GEO de forma **100% autônoma**. O script cobre automaticamente as seções 1-4 abaixo. As seções 5-7 requerem verificação manual via browser.

## Table of Contents
1. Acessibilidade para Crawlers de IA (automatizado)
2. Schema.org e Dados Estruturados (automatizado)
3. Conteúdo Citável (automatizado)
4. Presença em Diretórios (checklist gerado automaticamente)
5. Verificação de Visibilidade em IA (manual via browser)
6. Autoridade e Backlinks (manual via browser)
7. Monitoramento Contínuo

---

## 1. Acessibilidade para Crawlers de IA (Automatizado pelo geo_audit.py)

O script `geo_audit.py` verifica automaticamente o `robots.txt` para os seguintes 12 crawlers:

| Bot | Empresa | Prioridade | Pontos se bloqueado |
|-----|---------|------------|---------------------|
| GPTBot | OpenAI (ChatGPT) | Crítica | -5 pts |
| ChatGPT-User | OpenAI (browsing) | Crítica | -5 pts |
| Google-Extended | Google (Gemini) | Crítica | -5 pts |
| Googlebot | Google Search + AI Overviews | Crítica | -5 pts |
| Bingbot | Microsoft (Copilot) | Crítica | -5 pts |
| anthropic-ai | Anthropic (Claude) | Secundária | -2 pts |
| ClaudeBot | Claude Web | Secundária | -2 pts |
| PerplexityBot | Perplexity AI | Secundária | -2 pts |
| Bytespider | ByteDance / TikTok AI | Secundária | -2 pts |
| CCBot | Common Crawl (dados de treino) | Secundária | -2 pts |
| FacebookBot | Meta AI | Secundária | -2 pts |
| cohere-ai | Cohere | Secundária | -2 pts |

**Pontuação máxima**: 25 pontos (todos liberados = 25, cada bloqueio deduz conforme tabela acima, mínimo 0).

**Classificação de status:**
- **`allowed`**: Sem regras de bloqueio, ou `Allow: /` explícito sem restrições
- **`allowed_restricted`**: `Allow: /` presente, mas com `Disallow` em caminhos específicos (ex: `/dashboard`, `/admin`) — comportamento correto e esperado, NÃO penalizado
- **`blocked`**: `Disallow: /` sem um `Allow: /` correspondente — penalizado conforme tabela

**Ação crítica**: Se qualquer crawler de prioridade Crítica estiver bloqueado (`blocked`), isso é classificado como recomendação de prioridade "critical" no relatório. Crawlers `allowed_restricted` NÃO geram alertas.

---

## 2. Schema.org e Dados Estruturados (Automatizado pelo geo_audit.py)

O script extrai automaticamente todos os blocos JSON-LD da homepage e das 10 páginas internas mais importantes, verificando:

| Tipo de Schema | Pontos | Quando é esperado |
|----------------|--------|-------------------|
| Organization | +4 | Sempre (homepage) |
| WebSite | +2 | Sempre (homepage) |
| Product / SoftwareApplication | +3 | Página de produtos/preços |
| FAQPage | +3 | Se houver FAQ (altamente valorizado por IAs) |
| Article / BlogPosting | +2 | Páginas de blog |
| BreadcrumbList | +2 | Navegação interna |
| HowTo | +2 | Tutoriais / guias |
| LocalBusiness | +2 | Se tiver presença física |

**Pontuação máxima**: 20 pontos.

**Verificação adicional manual**: Validar os JSON-LD no Google Rich Results Test (https://search.google.com/test/rich-results).

---

## 3. Conteúdo Citável (Automatizado pelo geo_audit.py)

O script analisa automaticamente o conteúdo HTML para avaliar a "citabilidade" — a probabilidade de uma IA generativa citar o site como fonte. Métricas avaliadas:

| Critério | Pontos | O que o script verifica |
|----------|--------|------------------------|
| Conteúdo FAQ presente | +4 | Detecta padrões "perguntas frequentes", "FAQ" no texto |
| Estatísticas com números | +3 | Conta ocorrências de padrões numéricos (X%, R$ X, etc.) |
| Citações e fontes | +3 | Detecta "segundo", "de acordo com", "fonte:" no texto |
| Listas estruturadas | +3 | Conta elementos `<ul>`, `<ol>` na página |
| Tabelas com dados | +2 | Conta elementos `<table>` na página |
| Hierarquia de headings clara | +3 | Verifica se há exatamente 1x H1 e 2+ H2 |
| Profundidade do conteúdo | +2 | > 1500 palavras = "deep" (+2), > 500 = "moderate" (+1), < 500 = "thin" (0) |

**Pontuação máxima**: 20 pontos.

**Para que IAs generativas citem o site, o conteúdo precisa ser:**

- **Estruturado**: Usar headings claros (H2/H3), listas, tabelas com dados
- **Autoritativo**: Incluir dados originais, pesquisas, estatísticas com fonte
- **Atualizado**: Datas de publicação e atualização visíveis
- **Específico**: Responder perguntas diretas que usuários fariam a uma IA (ex: "quanto custa a tarifa de água em SP?")
- **Indexável**: Conteúdo em HTML (não em imagens, PDFs embeddados ou JavaScript-only)

---

## 4. Presença em Diretórios (Checklist gerado pelo geo_audit.py)

O script gera automaticamente URLs de verificação para 10 diretórios. Use o browser para verificar presença real:

| Diretório | Tipo | Prioridade | Impacto em GEO |
|-----------|------|------------|----------------|
| Google Business Profile | Busca local | Alta | Citado diretamente pelo Gemini |
| Product Hunt | Lançamento de produto | Alta | Citado por ChatGPT e Perplexity |
| G2 | Review de software B2B | Alta | Citado por todas as IAs |
| Capterra | Review de software | Alta | Citado por Copilot e Perplexity |
| Crunchbase | Perfil de startup | Média | Citado por ChatGPT |
| LinkedIn Company | Perfil corporativo | Média | Citado por Copilot |
| GitHub | Repositórios | Média | Citado por ChatGPT (se open-source) |
| Wikipedia | Enciclopédia | Alta | Citado por todas as IAs (se elegível) |
| Reclame Aqui | Reputação BR | Alta | Citado por Gemini e ChatGPT para buscas BR |
| Trustpilot | Reputação global | Média | Citado por Perplexity |

---

## 5. Verificação de Visibilidade em IA (Manual via Browser)

O script `geo_audit.py` gera 15 prompts de teste em português. Testar os 5 mais relevantes em cada engine:

**Engines para testar:**
1. ChatGPT (chat.openai.com)
2. Gemini (gemini.google.com)
3. Perplexity (perplexity.ai)
4. Copilot (copilot.microsoft.com)

**Para cada prompt, registrar:**
- A marca aparece? (sim/não)
- É citada com link?
- Posição na resposta (1o parágrafo, meio, final, ausente)
- Sentimento (positivo, neutro, negativo)
- Concorrentes mencionados junto

**Exemplos de prompts gerados pelo script:**
- "O que é [Marca]?"
- "Quais são as melhores ferramentas para [categoria] no Brasil?"
- "Como [resolver problema que o produto resolve]?"
- "Existe algum serviço que [proposta de valor]?"
- "Comparação de serviços de [categoria]"

---

## 6. Autoridade e Backlinks (Manual via Browser)

Fatores que aumentam a probabilidade de citação por IA:

- **Backlinks de domínios .gov.br e .edu.br** têm peso desproporcional
- **Menções em mídia** (Folha, Exame, TechCrunch) são indexadas por todas as IAs
- **Artigos acadêmicos ou técnicos** citando a empresa aumentam autoridade
- **Guest posts** em blogs de autoridade do setor

Verificar via busca: `"nome da marca" site:gov.br OR site:edu.br OR site:folha.uol.com.br`

---

## 7. Monitoramento Contínuo

Após implementar as correções, monitorar evolução:

| Ação | Frequência | Como |
|------|-----------|------|
| Reexecutar `geo_audit.py` | Mensal | Comparar scores mês a mês |
| Testar prompts em IAs | Quinzenal | Verificar se a marca começou a aparecer |
| Verificar robots.txt | Após cada deploy | Garantir que crawlers não foram re-bloqueados |
| Monitorar Schema | Após cada alteração | Validar no Rich Results Test |

**Ferramentas externas opcionais (para complementar, não substituir a análise autônoma):**

| Ferramenta | O que mede | URL |
|------------|-----------|-----|
| NAIA | Score GEO completo | naia.today |
| Otterly.ai | Monitoramento de citações em IA | otterly.ai |
| HubSpot AI Search Grader | Visibilidade em buscas IA | hubspot.com/ai-search-grader |

Frequência recomendada: mensal para score GEO, semanal para monitoramento de citações.
