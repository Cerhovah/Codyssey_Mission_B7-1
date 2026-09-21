import { login, resetDemoHistory } from "./api.js";

const TOKEN_KEY = "codyssey.preview.token.v1";
const DEMO_TOKEN = "preview-demo-session";

const elements = {
  startButton: document.querySelector("#open-login-button"),
  logoutButton: document.querySelector("#logout-button"),
  resetButton: document.querySelector("#preview-reset-button"),
  notice: document.querySelector("#preview-notice"),
  connectionStatus: document.querySelector("#connection-status"),
  connectionStatusLabel: document.querySelector("#connection-status-label"),
  modeBadge: document.querySelector("#ai-mode-badge"),
  questionInput: document.querySelector("#question-input"),
};

export function getAccessToken() {
  try {
    return sessionStorage.getItem(TOKEN_KEY) === DEMO_TOKEN ? DEMO_TOKEN : null;
  } catch (_error) {
    return null;
  }
}

function announceAuthChange(authenticated) {
  window.dispatchEvent(new CustomEvent("auth:changed", { detail: { authenticated } }));
}

function renderSession() {
  const authenticated = Boolean(getAccessToken());
  elements.startButton.hidden = authenticated;
  elements.logoutButton.hidden = !authenticated;
}

function setNotice(message) {
  elements.notice.textContent = message;
}

export function clearSession() {
  try {
    sessionStorage.removeItem(TOKEN_KEY);
  } catch (_error) {
    // 저장 공간이 차단된 환경에서도 화면 상태를 갱신합니다.
  }
  resetDemoHistory();
  renderSession();
  announceAuthChange(false);
}

export function openLoginModal(notice = "") {
  clearSession();
  setNotice(notice || "데모로 다시 시작해 주세요. 질문은 이 탭에만 저장됩니다.");
  elements.startButton.focus();
}

async function startDemo() {
  const result = await login({ username: "demo", password: "demo" });
  try {
    sessionStorage.setItem(TOKEN_KEY, result.accessToken);
  } catch (_error) {
    setNotice("브라우저 저장 공간이 차단되어 데모를 시작할 수 없습니다.");
    return;
  }
  setNotice("실제 AI·서버 미연결. 질문은 이 탭에만 저장됩니다. 개인정보 입력 금지.");
  renderSession();
  announceAuthChange(true);
  elements.questionInput.focus();
}

function resetDemo() {
  clearSession();
  setNotice("이 탭의 시연 기록을 지웠습니다. 데모로 다시 시작해 주세요.");
  elements.startButton.focus();
}

function initializeDemoAuth() {
  elements.startButton.textContent = "데모로 시작";
  elements.logoutButton.textContent = "데모 종료";
  elements.modeBadge.textContent = "UI DEMO";
  elements.modeBadge.hidden = false;
  elements.connectionStatus.dataset.state = "demo";
  elements.connectionStatus.title = "데모 화면 · 서버 미연결";
  elements.connectionStatusLabel.textContent = "데모 화면 · 서버 미연결";
  elements.startButton.addEventListener("click", () => { void startDemo(); });
  elements.logoutButton.addEventListener("click", clearSession);
  elements.resetButton.addEventListener("click", resetDemo);
  renderSession();
}

initializeDemoAuth();
