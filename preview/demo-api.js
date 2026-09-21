const DEMO_TOKEN = "preview-demo-session";
const DEMO_USER = "demo";
const DEMO_PASSWORD = "demo";
const HISTORY_KEY = "codyssey.preview.history.v1";
let fallbackHistory = [];

export class ApiError extends Error {
  constructor(message, { status = 0, code = "API_ERROR" } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

function assertActive(signal) {
  if (signal?.aborted) {
    throw new DOMException("요청이 취소되었습니다.", "AbortError");
  }
}

function assertDemoSession(token, signal) {
  assertActive(signal);
  if (token !== DEMO_TOKEN) {
    throw new ApiError("데모 계정으로 다시 로그인해 주세요.", { status: 401 });
  }
}

function demoAnswer(question) {
  const normalized = question.trim();
  if (/안녕|반가/.test(normalized)) {
    return "데모 응답 · 안녕하세요! 이 화면에서는 대화의 흐름과 모바일 사용성을 체험할 수 있어요. 실제 AI 답변은 연결되지 않습니다.";
  }
  if (/계획|정리|순서/.test(normalized)) {
    return "데모 응답 · 먼저 목표를 한 문장으로 적고, 필요한 단계를 작은 일로 나눠 보세요. 가장 먼저 할 일 하나를 정하면 시작하기 쉬워집니다. 실제 AI 답변은 연결되지 않습니다.";
  }
  return "데모 응답 · 질문을 받았습니다. 이 페이지는 채팅 UI 시연용이며 실제 AI와 서버, 데이터베이스에 연결되지 않습니다.";
}

function readHistory() {
  try {
    const parsed = JSON.parse(sessionStorage.getItem(HISTORY_KEY) || "[]");
    return Array.isArray(parsed) ? parsed : [];
  } catch (_error) {
    return [...fallbackHistory];
  }
}

function writeHistory(history) {
  fallbackHistory = [...history];
  try {
    sessionStorage.setItem(HISTORY_KEY, JSON.stringify(history));
  } catch (_error) {
    // 저장 공간을 사용할 수 없어도 현재 탭의 시연은 계속합니다.
  }
}

export function resetDemoHistory() {
  fallbackHistory = [];
  try {
    sessionStorage.removeItem(HISTORY_KEY);
  } catch (_error) {
    // 저장 공간이 차단된 환경에서도 메모리 기록은 지웁니다.
  }
}

export async function health(signal) {
  assertActive(signal);
  return { data: { status: "ok" }, status: 200, aiMode: "mock" };
}

export async function login(credentials, signal) {
  assertActive(signal);
  if (credentials.username !== DEMO_USER || credentials.password !== DEMO_PASSWORD) {
    throw new ApiError("시연 계정은 demo / demo입니다. 실제 비밀번호를 입력하지 마세요.", {
      status: 401,
    });
  }
  return { accessToken: DEMO_TOKEN, tokenType: "bearer", aiMode: "mock" };
}

export async function register(_credentials, signal) {
  assertActive(signal);
  throw new ApiError("공개 시연에서는 회원가입을 제공하지 않습니다. demo / demo로 로그인해 주세요.", {
    status: 400,
  });
}

export async function sendChat(question, token, signal) {
  assertDemoSession(token, signal);
  if (typeof question !== "string" || !question.trim()) {
    throw new ApiError("질문을 입력해 주세요.", { status: 400 });
  }
  if (Array.from(question).length > 500) {
    throw new ApiError("질문은 500자 이하로 입력해 주세요.", { status: 422 });
  }
  await Promise.resolve();
  assertDemoSession(token, signal);
  const answer = demoAnswer(question);
  const latencyMs = 0;
  const history = readHistory();
  history.push({
    id: history.length + 1,
    question,
    response: answer,
    latency_ms: latencyMs,
    created_at: new Date().toISOString(),
  });
  writeHistory(history);
  return { answer, latencyMs, aiMode: "mock" };
}

export async function getChatHistory(token, signal) {
  assertDemoSession(token, signal);
  return { chats: readHistory(), aiMode: "mock" };
}
