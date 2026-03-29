/**
 * CRO/GEO Dashboard Data Template
 * 
 * Preencha este template com os dados reais da análise.
 * Use como base para o arquivo cro-data.ts do dashboard webdev.
 * 
 * Instruções:
 * 1. Substitua todos os valores [PLACEHOLDER] pelos dados reais
 * 2. Adicione/remova findings conforme necessário
 * 3. Mantenha a estrutura de tipos intacta
 */

// === SCORES ===
export const scores = {
  cro: 0,         // 0-100 — ver scoring-rubric.md seção 2
  ux: 0,          // 0-100 — ver scoring-rubric.md seção 3
  seo: 0,         // 0-100 — ver scoring-rubric.md seção 4
  performance: 0, // 0-100 — ver scoring-rubric.md seção 5
  security: 0,    // 0-100 — ver scoring-rubric.md seção 6
  geo: 0,         // 0-100 — ver scoring-rubric.md seção 7
};

// === SITE INFO ===
export const siteInfo = {
  name: "[NOME DO SITE]",
  url: "[URL]",
  auditDate: "[YYYY-MM-DD]",
  author: "[NOME DO AUTOR]",
};

// === FUNNEL ===
export type FunnelStep = {
  label: string;
  percentage: number;
  dropoff: string;
};

export const funnel: FunnelStep[] = [
  { label: "Visitante", percentage: 100, dropoff: "" },
  { label: "Interesse (scroll)", percentage: 0, dropoff: "[motivo da perda]" },
  { label: "Ver Preço", percentage: 0, dropoff: "[motivo da perda]" },
  { label: "Cadastro", percentage: 0, dropoff: "[motivo da perda]" },
  { label: "Pagamento", percentage: 0, dropoff: "[motivo da perda]" },
  { label: "Uso/Resultado", percentage: 0, dropoff: "" },
];

// === FINDINGS ===
export type Severity = "critical" | "high" | "medium" | "low";
export type Category = "CRO" | "UX" | "SEO" | "Performance" | "Segurança" | "GEO";

export type Finding = {
  id: number;
  title: string;
  severity: Severity;
  category: Category;
  page: string;
  description: string;
  recommendation: string;
  impact: string;
};

export const findings: Finding[] = [
  // Adicionar cada problema encontrado como um objeto Finding
  // Exemplo:
  // {
  //   id: 1,
  //   title: "CTA principal leva a 404",
  //   severity: "critical",
  //   category: "CRO",
  //   page: "Homepage",
  //   description: "O botão 'Ver Produtos' no hero leva a uma página 404.",
  //   recommendation: "Corrigir a rota /produtos ou redirecionar para a página correta.",
  //   impact: "Perda direta de conversões — visitantes interessados não conseguem avançar.",
  // },
];

// === PERFORMANCE METRICS ===
export const performanceMetrics = {
  ttfb: 0,          // em milissegundos
  totalLoad: 0,     // em segundos
  pageSize: 0,      // em KB
  httpCode: 200,
};

// === SECURITY HEADERS ===
export type SecurityHeader = {
  name: string;
  present: boolean;
  value: string;
  severity: Severity;
};

export const securityHeaders: SecurityHeader[] = [
  { name: "HSTS", present: false, value: "", severity: "high" },
  { name: "CSP", present: false, value: "", severity: "high" },
  { name: "X-Content-Type-Options", present: false, value: "", severity: "medium" },
  { name: "X-Frame-Options", present: false, value: "", severity: "medium" },
  { name: "Referrer-Policy", present: false, value: "", severity: "low" },
  { name: "Permissions-Policy", present: false, value: "", severity: "low" },
  { name: "X-XSS-Protection", present: false, value: "", severity: "low" },
];

// === GEO DATA ===
export type GeoMetric = {
  name: string;
  score: number;
  maxScore: number;
};

export const geoMetrics: GeoMetric[] = [
  { name: "Visibilidade IA", score: 0, maxScore: 100 },
  { name: "Citações", score: 0, maxScore: 100 },
  { name: "Posição", score: 0, maxScore: 100 },
  { name: "Risco Reputacional", score: 0, maxScore: 100 },
  { name: "Autoridade", score: 0, maxScore: 100 },
  { name: "Schema", score: 0, maxScore: 100 },
  { name: "Fontes", score: 0, maxScore: 100 },
  { name: "Conteúdo Citável", score: 0, maxScore: 100 },
  { name: "Presença Diretórios", score: 0, maxScore: 100 },
];

export type AICrawler = {
  name: string;
  company: string;
  blocked: boolean;
};

export const aiCrawlers: AICrawler[] = [
  { name: "GPTBot", company: "OpenAI", blocked: false },
  { name: "Google-Extended", company: "Google", blocked: false },
  { name: "ChatGPT-User", company: "OpenAI", blocked: false },
  { name: "Bingbot", company: "Microsoft", blocked: false },
  { name: "ClaudeBot", company: "Anthropic", blocked: false },
  { name: "PerplexityBot", company: "Perplexity", blocked: false },
  { name: "Amazonbot", company: "Amazon", blocked: false },
  { name: "Applebot-Extended", company: "Apple", blocked: false },
  { name: "CCBot", company: "Common Crawl", blocked: false },
  { name: "Bytespider", company: "ByteDance", blocked: false },
  { name: "Cohere-ai", company: "Cohere", blocked: false },
  { name: "FacebookBot", company: "Meta", blocked: false },
];

// === TOP ACTIONS ===
export type TopAction = {
  rank: number;
  title: string;
  impact: string;
  effort: string;
  category: Category;
};

export const topActions: TopAction[] = [
  // Adicionar as 3-5 ações de maior impacto
  // Exemplo:
  // {
  //   rank: 1,
  //   title: "Liberar robots.txt para crawlers de IA",
  //   impact: "Score GEO de 28 → 70+",
  //   effort: "5 minutos",
  //   category: "GEO",
  // },
];
