export type Line = { speaker: string; en: string; spoken?: string; spoken_from_en?: string };

export type Shot = {
  id: string;
  reason: string;
  description: string;
  place?: string;
  duration_s: number;
  characters?: string[];
  image_prompt?: string;
  seed?: number;
  motion_prompt?: string;
  vertical?: { mode: "crop" | "fit"; focus?: number };
  clip_s?: number;
  lines: Line[];
};

export type Storyboard = {
  schema_version: 1;
  title: string;
  logline?: string;
  narration_language: string;
  translation_notes?: string;
  style?: string;
  motion_style?: string;
  video_engine?: "wan" | "grok";
  music?: { caption: string; seeds: number[]; chosen_seed?: number; why_chosen?: string };
  end_card?: { title?: string; made_by?: string };
  characters?: Record<string, { description: string; seed?: number }>;
  voices?: Record<string, { voice: string; style?: string }>;
  shots: Shot[];
};

export type ShotOutputs = { keyframe: string | null; clip: string | null; lines: (string | null)[] };

export type Outputs = {
  references: Record<string, string | null>;
  shots: Record<string, ShotOutputs>;
  music: { seed: number; url: string | null }[];
  films: Record<"16x9" | "9x16", string | null>;
};

export type StageName = "script" | "narration" | "keyframes" | "shots" | "music" | "film";

export type StageEstimate = { to_make: number; cached: number; est_usd: number; needs_keys: string[]; waiting_for: string[] };

export type Estimate = { stages: Partial<Record<StageName, StageEstimate>>; problems: string[] };

export type RunSummary = {
  id: string;
  stages: StageName[];
  quality: "draft" | "final";
  status: "queued" | "running" | "done" | "failed" | "cancelled";
  stage_status: Partial<Record<StageName, "started" | "done" | "failed">>;
};

export type RunEvent =
  | { type: "log"; line: string }
  | { type: "stage"; stage: StageName; status: "started" | "done" | "failed"; seconds?: number; error?: string }
  | { type: "status"; status: RunSummary["status"] };

export type CostSummary = { calls: number; ok: number; failed: number; billed: number; list: number; total_min: number };

export type Costs = { total: CostSummary; by_stage: Record<string, CostSummary> };
