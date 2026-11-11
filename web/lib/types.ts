export type Role = { name: string; label: string; description: string };

export type Source = {
  n: number;
  title: string;
  url: string;
  heading: string;
  access_group: string;
  snippet: string;
  score: number | null;
};

export type Outcome = {
  refused: boolean;
  uncited: boolean;
  cited: number[];
  usage: { token_source: "provider" | "estimated" };
  cost_usd: { total: number | null };
  timings_ms: { total?: number; first_token?: number };
};

export type Exchange = {
  id: number;
  question: string;
  role: Role;
  status: "searching" | "writing" | "done" | "failed";
  text: string;
  sources: Source[];
  outcome?: Outcome;
  failure?: string;
};

export type StreamEvent =
  | { event: "sources"; data: Source[] }
  | { event: "delta"; data: string }
  | { event: "done"; data: Outcome }
  | { event: "error"; data: { message: string } };
