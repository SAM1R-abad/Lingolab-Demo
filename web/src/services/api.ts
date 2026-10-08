import type {
  AdminQuestion,
  AdminQuestionPayload,
  AdminUser,
  AuthResponse,
  CEFRLevel,
  Paginated,
  PlacementSession,
  ProfileUpdatePayload,
  SessionResult,
  Skill,
  StartSessionResponse,
  SubmitAnswerResponse,
  User,
  WritingSubmission,
  WritingSubmissionListItem,
  WritingSubmissionPayload,
  WritingTask,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("lingolab_token");
}

async function request<T>(
  path: string,
  options: { method?: string; body?: unknown; auth?: boolean } = {}
): Promise<T> {
  const { method = "GET", body, auth = true } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Token ${token}`;
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  let data: unknown = null;
  try {
    data = await res.json();
  } catch {
    // No JSON body (e.g. 204) - that's fine.
  }

  if (!res.ok) {
    let message = `Request failed with status ${res.status}`;
    if (data && typeof data === "object") {
      const record = data as Record<string, unknown>;
      if (typeof record.detail === "string") {
        message = record.detail;
      } else {
        message = JSON.stringify(data);
      }
    }
    throw new ApiError(res.status, message, data);
  }

  return data as T;
}

// The `users/` and `questions/` admin list endpoints are paginated on the
// backend (they can grow unbounded with real data). Existing admin screens
// were built against a plain array, so we walk every page here and return
// the flat list - callers don't need to change. If these lists grow large
// enough that "fetch everything up front" stops being a good idea, this is
// the place to switch to real page-by-page UI instead.
async function requestAllPages<T>(path: string): Promise<T[]> {
  const results: T[] = [];
  let next: string | null = path;
  while (next) {
    const page: Paginated<T> = await request<Paginated<T>>(next);
    results.push(...page.results);
    next = page.next ? new URL(page.next).pathname + new URL(page.next).search : null;
  }
  return results;
}

export const api = {
  // --- Auth -----------------------------------------------------------
  signup: (payload: {
    username: string;
    email: string;
    password: string;
    password2: string;
  }) => request<AuthResponse>("/api/v1/auth/signup/", { method: "POST", body: payload, auth: false }),

  login: (payload: { username: string; password: string }) =>
    request<AuthResponse>("/api/v1/auth/login/", { method: "POST", body: payload, auth: false }),

  guest: () => request<AuthResponse>("/api/v1/auth/guest/", { method: "POST", auth: false }),

  me: () => request<User>("/api/v1/auth/me/"),

  updateProfile: (payload: ProfileUpdatePayload) =>
    request<User>("/api/v1/auth/me/", { method: "PATCH", body: payload }),

  deleteAccount: () => request<null>("/api/v1/auth/me/", { method: "DELETE" }),

  // --- Admin: users ------------------------------------------------------
  // Note: /api/v1/auth/users/ is paginated server-side; this walks every
  // page and returns the flat list.
  adminUsers: () => requestAllPages<AdminUser>("/api/v1/auth/users/"),

  adminUpdateUser: (id: number, payload: Partial<Pick<AdminUser, "role" | "is_active">>) =>
    request<AdminUser>(`/api/v1/auth/users/${id}/`, { method: "PATCH", body: payload }),

  adminDeleteUser: (id: number) => request<null>(`/api/v1/auth/users/${id}/`, { method: "DELETE" }),

  // --- Admin: question bank -----------------------------------------------
  // Note: /api/v1/assessment/questions/ is paginated server-side (the
  // combined bank is ~500 questions and growing); this walks every page
  // and returns the flat list, same as before pagination was added.
  adminQuestions: (filters?: { skill?: Skill; level?: CEFRLevel }) => {
    const params = new URLSearchParams();
    if (filters?.skill) params.set("skill", filters.skill);
    if (filters?.level) params.set("level", filters.level);
    const qs = params.toString();
    return requestAllPages<AdminQuestion>(`/api/v1/assessment/questions/${qs ? `?${qs}` : ""}`);
  },

  adminCreateQuestion: (payload: AdminQuestionPayload) =>
    request<AdminQuestion>("/api/v1/assessment/questions/", { method: "POST", body: payload }),

  adminUpdateQuestion: (id: number, payload: Partial<AdminQuestionPayload>) =>
    request<AdminQuestion>(`/api/v1/assessment/questions/${id}/`, { method: "PATCH", body: payload }),

  adminDeleteQuestion: (id: number) =>
    request<null>(`/api/v1/assessment/questions/${id}/`, { method: "DELETE" }),

  // --- Assessment -------------------------------------------------------
  levels: () => request<Record<CEFRLevel, string>>("/api/v1/assessment/levels/"),

  sessions: () => request<PlacementSession[]>("/api/v1/assessment/sessions/"),

  startSession: (skill: Skill) =>
    request<StartSessionResponse>("/api/v1/assessment/start/", {
      method: "POST",
      body: { skill },
    }),

  sessionStatus: (sessionId: number) =>
    request<StartSessionResponse>(`/api/v1/assessment/${sessionId}/`),

  submitAnswer: (sessionId: number, questionId: number, answer: string) =>
    request<SubmitAnswerResponse>(`/api/v1/assessment/${sessionId}/answer/`, {
      method: "POST",
      body: { question_id: questionId, answer },
    }),

  sessionResult: (sessionId: number) =>
    request<SessionResult>(`/api/v1/assessment/${sessionId}/result/`),

  // --- Writing Assessment -------------------------------------------------
  writingTasks: () => request<WritingTask[]>("/api/v1/writing/tasks/"),

  writingTask: (taskId: number) => request<WritingTask>(`/api/v1/writing/tasks/${taskId}/`),

  writingSubmissions: () =>
    request<WritingSubmissionListItem[]>("/api/v1/writing/submissions/"),

  submitWriting: (payload: WritingSubmissionPayload) =>
    request<WritingSubmission>("/api/v1/writing/submissions/", {
      method: "POST",
      body: payload,
    }),

  writingSubmission: (submissionId: number) =>
    request<WritingSubmission>(`/api/v1/writing/submissions/${submissionId}/`),
};
