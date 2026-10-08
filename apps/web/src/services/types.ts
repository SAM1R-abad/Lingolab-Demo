// Matches DRF's PageNumberPagination envelope, used by list endpoints that
// paginate (currently: admin users, admin question bank).
export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export type Role = "student" | "teacher" | "admin";

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: Role;
  is_guest: boolean;
}

export interface AdminUser extends User {
  is_active: boolean;
  date_joined: string;
}

export interface ProfileUpdatePayload {
  first_name?: string;
  last_name?: string;
  email?: string;
}

export interface AuthResponse {
  user: User;
  token: string;
}

export type Skill = "vocabulary" | "grammar" | "reading";

export type CEFRLevel = "A1" | "A2" | "B1" | "B2" | "C1" | "C2";

export type SessionStatus = "in_progress" | "completed";

export interface Question {
  id: number;
  level: CEFRLevel;
  question_type: string;
  prompt: string;
  options: string[];
  tag: string;
}

/** Full question record as seen by admins (includes the answer key). */
export interface AdminQuestion extends Question {
  external_id: string;
  skill: Skill;
  correct_answer: string;
  created_at: string;
  updated_at: string;
}

export interface AdminQuestionPayload {
  external_id: string;
  skill: Skill;
  level: CEFRLevel;
  question_type: string;
  prompt: string;
  options: string[];
  correct_answer: string;
  tag?: string;
}

export interface SessionQuestion {
  id: number;
  order: number;
  level: CEFRLevel;
  question: Question;
  selected_answer: string;
  is_correct: boolean | null;
  answered_at: string | null;
}

export interface PlacementSession {
  id: number;
  skill: Skill;
  status: SessionStatus;
  current_level: CEFRLevel;
  passed_levels: CEFRLevel[];
  result_level: string;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface LevelBreakdownEntry {
  level: CEFRLevel;
  total_questions: number;
  correct_answers: number;
  score_percent: number;
  passed: boolean;
}

export interface SessionResult extends PlacementSession {
  level_breakdown: LevelBreakdownEntry[];
}

export interface StartSessionResponse {
  session: PlacementSession;
  questions: SessionQuestion[];
}

export interface SubmitAnswerResponse {
  session: PlacementSession;
  questions?: SessionQuestion[];
  result?: SessionResult;
}

// --- Writing Assessment -----------------------------------------------

export interface WritingTask {
  id: number;
  key: string;
  title: string;
  prompt: string;
  target_level: CEFRLevel | null;
  min_word_count: number;
  svg_url: string;
}

export type WritingSubmissionStatus = "pending" | "processing" | "completed" | "failed";

export type TopicRelevance = "relevant" | "partially_relevant" | "weakly_relevant";

export interface SpellingError {
  word: string;
  suggestion: string;
  error_type: string;
  start_offset: number;
  end_offset: number;
}

export interface GrammarError {
  fragment: string;
  suggestion: string;
  short_description: string;
  rule_id: string;
  category: string;
  start_offset: number;
  end_offset: number;
}

export interface TopicRelevanceDetails {
  matched_core_count?: number;
  total_core_count?: number;
  matched_keywords?: string[];
  bonus_matches?: string[];
}

export interface WritingResult {
  overall_score: number;
  overall_cefr_level: CEFRLevel;
  confidence: "low" | "medium" | "high";
  rationale: string;
  word_count: number;
  sentence_count: number;
  vocabulary_distribution: Record<string, number>;
  dominant_vocabulary_level: CEFRLevel | null;
  lexical_complexity_level: CEFRLevel | null;
  grammar_accuracy_level: CEFRLevel | null;
  grammar_complexity_level: CEFRLevel | null;
  topic_relevance: TopicRelevance | null;
  topic_relevance_details: TopicRelevanceDetails;
  strengths: string[];
  weaknesses: string[];
  feedback: string;
  limitations: string;
}

export interface WritingSubmission {
  id: number;
  task: WritingTask;
  submitted_text: string;
  status: WritingSubmissionStatus;
  error_message: string;
  created_at: string;
  completed_at: string | null;
  result: WritingResult | null;
  spelling_errors: SpellingError[];
  grammar_errors: GrammarError[];
}

/** Lightweight row used by the submission history / Progress list. */
export interface WritingSubmissionListItem {
  id: number;
  task_title: string;
  status: WritingSubmissionStatus;
  created_at: string;
  completed_at: string | null;
  overall_cefr_level: CEFRLevel | null;
  overall_score: number | null;
}

export interface WritingSubmissionPayload {
  task_id: number;
  submitted_text: string;
}
