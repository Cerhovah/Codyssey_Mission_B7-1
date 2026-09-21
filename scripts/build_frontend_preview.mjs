import { cp, lstat, mkdir, readFile, readdir, rm, writeFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const sourceRoot = join(repositoryRoot, "static");
const previewRoot = join(repositoryRoot, "preview");
const outputRoot = join(repositoryRoot, "preview-dist");

if (outputRoot !== join(repositoryRoot, "preview-dist")) {
  throw new Error("시연 출력 경로가 예상과 다릅니다.");
}

try {
  const output = await lstat(outputRoot);
  if (output.isSymbolicLink()) {
    throw new Error("시연 출력 경로가 심볼릭 링크입니다.");
  }
  await rm(outputRoot, { recursive: true });
} catch (error) {
  if (error?.code !== "ENOENT") {
    throw error;
  }
}

await mkdir(outputRoot, { recursive: true });
await cp(sourceRoot, join(outputRoot, "static"), { recursive: true });
await rm(join(outputRoot, "static", "index.html"));

const sourceHtml = await readFile(join(sourceRoot, "index.html"), "utf8");
if (!sourceHtml.includes("<body>") || !sourceHtml.includes("</head>")) {
  throw new Error("시연 HTML의 구조를 확인해 주세요.");
}

const banner = [
  '<div class="preview-banner" role="note">',
  '<span><strong>UI 데모</strong> <span id="preview-notice">실제 AI·서버 미연결. 질문은 이 탭에만 저장됩니다. 개인정보 입력 금지.</span></span>',
  '<button id="preview-reset-button" type="button">시연 초기화</button>',
  "</div>",
].join("");

const authModalPattern = /\s*<section\b(?=[^>]*\bid="auth-modal")[\s\S]*?<\/section>/i;
if (!authModalPattern.test(sourceHtml)) {
  throw new Error("시연 페이지에서 제거할 인증 입력 폼을 찾을 수 없습니다.");
}
const sidebarPattern = /<aside\b(?=[^>]*\bid="sidebar")[^>]*>/i;
if (!sidebarPattern.test(sourceHtml)) {
  throw new Error("시연 페이지에서 사이드바를 찾을 수 없습니다.");
}

let html = sourceHtml
  .replace(authModalPattern, '<section id="auth-modal" hidden></section>')
  .replace(sidebarPattern, (aside) => `${aside}\n        <span class="preview-sidebar-label">UI 데모 · 서버 미연결</span>`)
  .replaceAll('="/static/', '="./static/')
  .replace("</head>", [
    '  <meta http-equiv="Content-Security-Policy" content="default-src \'self\'; connect-src \'none\'; img-src \'self\' data:; style-src \'self\'; script-src \'self\'; base-uri \'none\'; form-action \'none\'">',
    '  <link rel="stylesheet" href="./preview-demo.css">',
    "  </head>",
  ].join("\n"))
  .replace("<body>", `<body>\n    ${banner}`)
  .replace("<title>AI Assistant</title>", "<title>AI Assistant · UI 시연</title>");

await writeFile(join(outputRoot, "index.html"), html, "utf8");
await cp(join(previewRoot, "demo-api.js"), join(outputRoot, "static", "js", "api.js"));
await cp(join(previewRoot, "demo-auth.js"), join(outputRoot, "static", "js", "auth.js"));
await cp(join(previewRoot, "demo.css"), join(outputRoot, "preview-demo.css"));
await writeFile(join(outputRoot, ".nojekyll"), "", "utf8");

for (const folder of ["js", "css"]) {
  const assetFolder = join(outputRoot, "static", folder);
  for (const fileName of await readdir(assetFolder)) {
    const asset = await readFile(join(assetFolder, fileName), "utf8");
    if (/\bfetch\s*\(|["'(]\/static\//.test(asset)) {
      throw new Error(`시연 자산에 외부 요청 또는 절대 경로가 남았습니다: ${folder}/${fileName}`);
    }
  }
}

console.log("preview-dist/ 생성 완료: 정적 UI 시연 전용, 외부 API 호출 없음");
