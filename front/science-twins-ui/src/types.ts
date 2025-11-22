export type MatchType = "textual" | "conceptual" | "mixed";

export interface OverlapFragment {
  query_fragment: string;
  match_fragment: string;
  score?: number;
}

export interface AnalyzeMatch {
  id: string;
  title: string;
  field: string;
  similarity: number;
  type: MatchType;
  url?: string;
  explanation: string;
  overlap_fragments?: OverlapFragment[];
  conceptual_links?: string[];
}

export interface AnalyzeQueryInfo {
  normalized_title?: string;
  field?: string;
  summary?: string;
}

export interface PlagiarismResponse {
  type: "plagiarism" | "no_plagiarism";
  url?: string;
  title?: string;
  reason?: string;
}

export interface DoppelgangerPaper {
  id: number;
  title: string;
  url: string;
  domain: string;
  reason: string;
  place?: number; // only present in top_3.papers
}

export interface DoppelgangerTop3 {
  papers: DoppelgangerPaper[];
  justification: string;
}

export interface DoppelgangerResult {
  type: "doppelganger";
  count: number;
  all_doppelgangers_with_reasons: DoppelgangerPaper[];
  top_3: DoppelgangerTop3;
}

export type AnalyzeResponse =
  | { mode: "plagiarism"; result: PlagiarismResponse }
  | { mode: "doppelganger"; result: DoppelgangerResult };

