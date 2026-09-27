/** Mirrors backend/app/modules/dsa/schemas.py. */

export type DsaLanguage = 'python' | 'javascript' | 'cpp' | 'java';
export type Difficulty = 'easy' | 'medium' | 'hard';
export type ProblemStatus = 'draft' | 'published';
export type ProgressStatus = 'not_started' | 'attempted' | 'solved';
export type JobStatus = 'pending' | 'running' | 'done' | 'error';
export type CompareMode = 'exact' | 'unordered' | 'unordered_nested' | 'float_tolerance' | 'checker';
export type TestKind = 'example' | 'edge' | 'random' | 'manual';
export type BadgeTone = 'success' | 'warning' | 'danger' | 'info' | 'default';

/** JSON test data: arguments, expected outputs, actual outputs. */
export type JsonValue = string | number | boolean | null | JsonValue[] | { [key: string]: JsonValue };

export const LANGUAGE_LABELS: Record<DsaLanguage, string> = {
  python: 'Python 3',
  javascript: 'JavaScript',
  cpp: 'C++17',
  java: 'Java 17',
};

export const DIFFICULTY_LABELS: Record<Difficulty, string> = { easy: 'Easy', medium: 'Medium', hard: 'Hard' };
export const MAX_CUSTOM_INPUTS = 3;

export interface DsaMe {
  can_edit: boolean;
}

/** A user's private markdown note; `updated_at` is null when nothing has been written. */
export interface DsaNote {
  content: string;
  updated_at: string | null;
}

/** What a note is attached to. */
export type DsaNoteScope = 'patterns' | 'problems';

export interface PatternSummary {
  slug: string;
  number: number;
  name: string;
  description: string;
  week: number;
  total: number;
  solved: number;
  attempted: number;
}

export interface ProblemRow {
  slug: string;
  title: string;
  difficulty: Difficulty;
  tags: string[];
  is_variant: boolean;
  status: ProblemStatus;
  progress: ProgressStatus;
}

export interface PatternDetail extends PatternSummary {
  problems: ProblemRow[];
}

export interface SampleCase {
  input: JsonValue;
  expected: JsonValue;
  explanation: string | null;
}

export interface SignatureSpec {
  kind: 'function' | 'class';
  name: string;
  [key: string]: JsonValue;
}

export interface ProblemDetail {
  slug: string;
  title: string;
  difficulty: Difficulty;
  tags: string[];
  is_variant: boolean;
  status: ProblemStatus;
  pattern_slug: string;
  pattern_name: string;
  statement: string;
  constraints: string;
  signature: SignatureSpec | null;
  time_limit_ms: number;
  memory_limit_mb: number;
  samples: SampleCase[];
  starter_code: Partial<Record<DsaLanguage, string>>;
  languages: DsaLanguage[];
  progress: ProgressStatus;
}

export interface SubmitRequest {
  language: DsaLanguage;
  code: string;
}

export interface RunRequest extends SubmitRequest {
  custom_inputs: JsonValue[];
}

export interface JobAccepted {
  id: string;
  status: JobStatus;
}

export interface RunCaseResult {
  index: number;
  input: JsonValue;
  expected: JsonValue | null;
  actual: JsonValue | null;
  passed: boolean | null;
  ms: number | null;
  error: string | null;
  is_custom: boolean;
}

export interface RunResult {
  id: string;
  status: JobStatus;
  verdict: string | null;
  message: string | null;
  cases: RunCaseResult[];
  stdout: string;
  stderr: string;
}

export interface SubmissionSummary {
  id: string;
  language: DsaLanguage;
  status: JobStatus;
  verdict: string | null;
  passed: number;
  total: number;
  runtime_ms: number | null;
  memory_kb: number | null;
  created_at: string;
}

export interface SubmissionDetail extends SubmissionSummary {
  problem_slug: string;
  code: string;
  failed_case: number | null;
  message: string | null;
}

export interface SubmissionPage {
  items: SubmissionSummary[];
  total: number;
}

export interface AdminTestCase {
  id: string;
  position: number;
  input: JsonValue;
  expected: JsonValue;
  is_sample: boolean;
  kind: TestKind;
  explanation: string | null;
}

export interface AdminProblemDetail extends ProblemDetail {
  compare_mode: CompareMode;
  checker: string | null;
  edited_in_ui: boolean;
  tests: AdminTestCase[];
}

export interface ProblemUpdate {
  title?: string;
  difficulty?: Difficulty;
  tags?: string[];
  is_variant?: boolean;
  status?: ProblemStatus;
  statement?: string;
  constraints?: string;
  signature?: SignatureSpec | null;
  compare_mode?: CompareMode;
  checker?: string | null;
  time_limit_ms?: number;
  memory_limit_mb?: number;
}

export interface CaseWrite {
  input: JsonValue;
  expected: JsonValue;
  is_sample: boolean;
  explanation: string | null;
  position?: number;
}

export function isTerminal(status: JobStatus): boolean {
  return status === 'done' || status === 'error';
}

export function verdictTone(verdict: string | null): BadgeTone {
  switch (verdict) {
    case 'Accepted':
      return 'success';
    case 'Wrong Answer':
    case 'Runtime Error':
    case 'Compilation Error':
      return 'danger';
    case 'Time Limit Exceeded':
    case 'Memory Limit Exceeded':
      return 'warning';
    case null:
      return 'default';
    default:
      return 'info';
  }
}

export function difficultyTone(difficulty: Difficulty): BadgeTone {
  return difficulty === 'easy' ? 'success' : difficulty === 'medium' ? 'warning' : 'danger';
}

/** Compact one-line JSON for showing test data. */
export function formatJson(value: JsonValue | undefined): string {
  return value === undefined ? '' : JSON.stringify(value);
}
