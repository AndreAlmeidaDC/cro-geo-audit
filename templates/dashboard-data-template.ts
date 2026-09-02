export type EvidenceStatus = "observed" | "measured" | "inferred" | "not_measured";
export type Confidence = "high" | "medium" | "low";
export type Priority = "P0" | "P1" | "P2" | "experiment" | "monitor";

export interface EvidenceItem {
  id: string;
  category: "cro" | "ux" | "search" | "ai-discovery" | "performance" | "accessibility" | "security" | "privacy";
  status: EvidenceStatus;
  source: string;
  confidence: Confidence;
  scope: string;
  evidence: string;
  consequence: string;
  priority: Priority;
  recommendation: string;
  verification: string;
}

export interface MeasurementSource {
  name: string;
  status: EvidenceStatus;
  period?: string;
  scope?: string;
  note: string;
}

export interface AuditDashboardData {
  site: string;
  auditedAt: string;
  methodology: string[];
  coverageGaps: string[];
  measurements: MeasurementSource[];
  findings: EvidenceItem[];
}

// Deliberately no overall score or grade. Visualize evidence coverage,
// open priorities and measurement sources instead of pseudo-precision.
