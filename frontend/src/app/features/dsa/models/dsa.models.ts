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
/** Mirrors MAX_RUN_CASES / MAX_RUN_INPUT_BYTES in schemas.py. */
export const MAX_RUN_CASES = 6;
export const MAX_RUN_INPUT_BYTES = 64 * 1024;

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

/** Run executes exactly `inputs`; cases equal to an example are checked against its output. */
export interface RunRequest extends SubmitRequest {
  inputs: JsonValue[];
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

/** A submission's first failing test (a snapshot taken when it was judged). */
export interface FailedTest {
  input: JsonValue;
  expected: JsonValue;
  actual: JsonValue | null;
  error: string | null;
  /** False when the program stopped on this test before producing a result (see the message). */
  answered: boolean;
  is_sample: boolean;
}

export interface SubmissionDetail extends SubmissionSummary {
  problem_slug: string;
  code: string;
  failed_case: number | null;
  failed_test: FailedTest | null;
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

/** Parsed JSON text, or undefined when it isn't valid JSON. */
export function parseJson(text: string): JsonValue | undefined {
  try {
    return JSON.parse(text) as JsonValue;
  } catch {
    return undefined;
  }
}

/** One labelled part of a test input: a function parameter, or a design problem's `ops` / `args`. */
export interface InputField {
  name: string;
  type: string;
}

/** Used when a signature can't describe its inputs: the whole input is one JSON value. */
const RAW_INPUT_FIELD: InputField = { name: 'input', type: 'JSON' };

const DESIGN_FIELDS: InputField[] = [
  { name: 'ops', type: 'string[]' },
  { name: 'args', type: 'any[][]' },
];

/** The fields a test input is made of, in order. */
export function inputFields(signature: SignatureSpec | null): InputField[] {
  if (signature?.kind === 'class') return DESIGN_FIELDS;
  const params = signature?.['params'];
  if (!Array.isArray(params) || params.length === 0) return [RAW_INPUT_FIELD];
  return params.map((p) => {
    const { name, type } = p as { name: string; type: string };
    return { name, type };
  });
}

/** One value per field of `inputFields(signature)`, or null when `input` doesn't have that shape. */
export function splitInput(signature: SignatureSpec | null, input: JsonValue): JsonValue[] | null {
  if (signature?.kind === 'class') {
    const isOps = input !== null && typeof input === 'object' && !Array.isArray(input) && 'ops' in input && 'args' in input;
    return isOps ? [input['ops'], input['args']] : null;
  }
  const fields = inputFields(signature);
  if (fields[0] === RAW_INPUT_FIELD) return [input];
  return Array.isArray(input) && input.length === fields.length ? input : null;
}

/** Inverse of `splitInput`. */
export function joinInput(signature: SignatureSpec | null, values: JsonValue[]): JsonValue {
  if (signature?.kind === 'class') return { ops: values[0], args: values[1] };
  return inputFields(signature)[0] === RAW_INPUT_FIELD ? values[0] : values;
}
