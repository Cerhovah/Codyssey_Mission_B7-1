# EC2 배포 절차와 승인 경계

이 문서는 AWS EC2 `t2.micro`, Ubuntu 22.04 LTS, Nginx, systemd, 2GB swap이라는 팀 배포안을 실행 가능한 순서로 정리한 **승인 전 계획**입니다. 2026-09-16 현재 AWS 리소스 생성·보안 그룹 변경·DNS/TLS 설정·외부 공개·유료 AI 호출은 실행하지 않았습니다. 따라서 공개 URL과 외부 검증 결과는 없습니다.

## 1. 실행 전 확인과 승인

운영자는 아래 값을 실제 계정과 팀에서 확인한 뒤 기록합니다. 확인되지 않은 placeholder나 예시 키로 배포하지 않습니다.

- AWS 계정 생성 시점, 대상 리전, `t2.micro` 제공 여부, 예상 과금과 예산 알림
- Ubuntu 22.04 LTS AMI와 CPU 아키텍처, 디스크 여유 공간
- 평가 대상 Git 저장소·정확한 ref/SHA와 배포 책임자
- 앱 비root 계정, 설치 절대경로, 영속 DB 경로, 환경 파일 경로
- SSH를 허용할 팀원 공인 IP/CIDR 목록
- HTTP 80 임시 시연인지 HTTPS 443 공개 운영인지, DNS·인증서 책임자
- 실제 코디세이 URL·모델·키·호출 권한·요금/빈도 한도

“프리티어”라는 이름만으로 무료를 가정하지 않습니다. 비용 조건이나 위 값 중 하나라도 확인되지 않으면 인프라 변경을 멈추고 로컬 Mock 검증만 유지합니다.

## 2. 기준 경로와 네트워크

아래 값은 예시 운영안이며 실제 머신에 적용하기 전에 팀 승인이 필요합니다.

| 용도 | 예시 값 | 조건 |
|---|---|---|
| 앱 계정/그룹 | `ai-assistant` | 로그인 셸이 없는 비root 전용 계정 |
| 앱 checkout | `/srv/ai-assistant` | 코드와 `.venv`; root 소유, 앱은 읽기 중심 |
| 환경 파일 | `/etc/ai-assistant/ai-assistant.env` | root:앱 그룹 소유, mode 0640 |
| SQLite 디렉터리 | `/var/lib/ai-assistant` | 앱 계정 쓰기, 백업 대상 |
| 앱 로그 | `/srv/ai-assistant/logs/app.log` | 현재 코드의 고정 경로, 앱 계정 쓰기 |
| Uvicorn | `127.0.0.1:8000` | 외부 보안 그룹과 공인 인터페이스에 미노출 |
| Nginx | `0.0.0.0:80` | 승인된 임시 HTTP 또는 TLS 전환 전 단계 |

보안 그룹에서 22/tcp는 승인된 팀원 CIDR만, 8000/tcp는 어떤 외부 CIDR에도 열지 않습니다. 원계획의 80/tcp 전체 공개는 로그인/JWT가 평문 네트워크를 지나는 위험이 있습니다. 443/tcp와 TLS를 추가하는 변경은 팀·운영자 승인과 DNS가 확보된 뒤 적용합니다.

HTTP만 허용된 짧은 평가 시연을 선택한다면 재사용 비밀번호·개인정보·민감한 질문을 넣지 않는 폐기 계정을 사용하고, 공개 시작/종료 시각과 보안 그룹 회수 책임자를 정합니다. 이것을 일반 사용자 대상 보안 완료 상태로 표현하지 않습니다.

## 3. 앱과 환경 준비

다음 명령은 승인된 EC2 안에서 로그인한 비root 배포 운영자가 경로와 ref를 재확인한 뒤 실행하는 예시입니다. 이 저장소의 로컬 작업에서는 실행하지 않습니다.

```bash
sudo apt-get update
sudo apt-get install --yes python3-venv nginx git
sudo adduser --system --group --home /nonexistent --no-create-home ai-assistant
sudo install -d -o ai-assistant -g ai-assistant -m 0700 /var/lib/ai-assistant
sudo install -d -o root -g ai-assistant -m 0750 /etc/ai-assistant
```

승인된 저장소 URL은 사용자정보·토큰을 포함하지 않아야 합니다. 기존 `/srv/ai-assistant`가 있으면 아래 최초 설치 절차를 실행하지 말고 백업·업데이트 계획을 별도로 승인받습니다. 운영자가 임시 소유한 빈 디렉터리에 정확한 SHA를 checkout하고 의존성·테스트를 확인한 뒤, 마지막에 코드 전체를 root 소유로 고정하고 앱 계정에는 로그 디렉터리만 쓰게 합니다. `<APPROVED_REPOSITORY_URL>`과 `<APPROVED_SHA>`를 임의로 채우지 않습니다.

```bash
test "$(id -u)" -ne 0
DEPLOY_USER="$(id -un)"
sudo test ! -e /srv/ai-assistant
sudo install -d -o "$DEPLOY_USER" -g "$DEPLOY_USER" -m 0750 /srv/ai-assistant
git clone --no-checkout "<APPROVED_REPOSITORY_URL>" /srv/ai-assistant
git -C /srv/ai-assistant checkout --detach "<APPROVED_SHA>"
cd /srv/ai-assistant
git status --short --branch
git rev-parse HEAD
test "$(git rev-parse HEAD)" = "<APPROVED_SHA>"
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt -c constraints.txt
.venv/bin/python -m pip check
.venv/bin/python -m pytest -q
.venv/bin/python scripts/smoke_test.py
sudo chown -R root:ai-assistant /srv/ai-assistant
sudo install -d -o ai-assistant -g ai-assistant -m 0700 /srv/ai-assistant/logs
```

환경 파일은 `.env.example`을 값의 목록으로만 참고해 별도로 만듭니다. 실제 키를 Git checkout이나 shell history에 넣지 않습니다. 배포에서는 최소한 다음 값이 필요합니다.

```dotenv
SECRET_KEY=<32자 이상의 별도 생성값>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DATABASE_URL=sqlite:////var/lib/ai-assistant/chatbot.db
CODESSEY_API_KEY=<승인된 실제 키>
CODESSEY_API_BASE=<확인된 HTTPS base URL>
AI_MODEL_NAME=<확인된 모델>
AI_TIMEOUT_SECONDS=8.0
APP_ENV=production
AI_MODE=real
CONTEXT_TURNS=5
```

파일을 만든 뒤 소유권과 권한을 확인합니다.

```bash
sudo chown root:ai-assistant /etc/ai-assistant/ai-assistant.env
sudo chmod 0640 /etc/ai-assistant/ai-assistant.env
sudo -u ai-assistant test -r /etc/ai-assistant/ai-assistant.env
sudo -u ai-assistant test -w /var/lib/ai-assistant
```

## 4. 설정 렌더링과 설치

저장소 템플릿은 머신별 절대경로를 소스에 하드코딩하지 않습니다. 다음 명령은 `deploy/generated/`에 두 파일만 만들며 sudo, 설치, 서비스 재시작, 네트워크 호출을 하지 않습니다.

- `deploy/chatbot.service.template`: systemd 원본
- `deploy/nginx.conf.template`: Nginx 원본
- `deploy/render_config.py`: 검증된 값 치환과 로컬 결과 생성

```bash
.venv/bin/python deploy/render_config.py \
  --app-user ai-assistant \
  --app-group ai-assistant \
  --app-dir /srv/ai-assistant \
  --env-file /etc/ai-assistant/ai-assistant.env \
  --data-dir /var/lib/ai-assistant \
  --server-name _
```

생성 결과는 Git 제외 대상입니다. CLI 출력 위치는 `deploy/generated/`로 고정되고 symlink·비정규 대상을 거부합니다. 운영자는 diff와 절대경로를 검토한 후에만 시스템 위치로 복사합니다. 이미 생성된 파일을 바꾸려면 내용을 먼저 확인한 뒤 `--force`를 명시합니다.

```bash
sed -n '1,240p' deploy/generated/ai-assistant.service
sed -n '1,240p' deploy/generated/ai-assistant.nginx.conf
# 기존 동명 설정이나 이전 백업이 하나라도 있으면 덮지 말고 변경 계획을 별도 승인합니다.
sudo test ! -e /etc/systemd/system/ai-assistant.service
sudo test ! -e /etc/nginx/sites-available/ai-assistant
sudo test ! -e /etc/nginx/sites-enabled/ai-assistant
sudo test ! -e /etc/nginx/sites-enabled/default.disabled-ai-assistant
sudo install -o root -g root -m 0644 deploy/generated/ai-assistant.service /etc/systemd/system/ai-assistant.service
sudo install -o root -g root -m 0644 deploy/generated/ai-assistant.nginx.conf /etc/nginx/sites-available/ai-assistant
# 기본 site가 symlink이고 다른 서비스를 제공하지 않는다고 검토·승인한 경우에만 보존 이름으로 이동합니다.
sudo test ! -e /etc/nginx/sites-enabled/default || sudo test -L /etc/nginx/sites-enabled/default
sudo test ! -L /etc/nginx/sites-enabled/default || sudo mv /etc/nginx/sites-enabled/default /etc/nginx/sites-enabled/default.disabled-ai-assistant
sudo ln -s /etc/nginx/sites-available/ai-assistant /etc/nginx/sites-enabled/ai-assistant
sudo systemd-analyze verify /etc/systemd/system/ai-assistant.service
sudo nginx -t
```

템플릿은 단일 Uvicorn worker를 `127.0.0.1:8000`에만 바인딩합니다. Nginx의 send/read timeout 15초는 AI 제한 8초와 DB·응답 처리 여유보다 길지만, 실제 지연을 측정해 재검토해야 합니다. FastAPI가 `/`와 `/static/`을 함께 제공하므로 Nginx는 현재 모든 경로를 같은 upstream으로 전달합니다.

설정 검사가 성공하고 변경 승인이 유지될 때만 서비스를 반영합니다.

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ai-assistant.service
sudo systemctl reload nginx
systemctl --no-pager --full status ai-assistant.service
journalctl -u ai-assistant.service -n 100 --no-pager
```

## 5. 2GB swap 확인과 조건부 구성

Swap은 메모리 압박을 완화할 수 있지만 OOM을 완전히 예방하거나 성능을 보장하지 않습니다. 먼저 현재 swap과 루트 디스크 공간, 기존 fstab 항목을 확인합니다.

```bash
swapon --show --bytes
free -h
df -h /
grep -nE '^[^#].*[[:space:]]swap[[:space:]]' /etc/fstab || true
```

이미 승인된 2GB 이상 swap이 있으면 새 `/swapfile`을 만들거나 fstab을 추가하지 않습니다. 없고 디스크·운영 승인이 충분할 때만 다음을 한 단계씩 실행합니다.

```bash
# 기존 /swapfile fstab 행은 형식이 달라도 중복 추가하지 않고 운영자가 먼저 검토합니다.
if grep -qE '^[[:space:]]*/swapfile[[:space:]]+' /etc/fstab; then
  echo '기존 /swapfile fstab 항목을 검토하세요.' >&2
  exit 1
fi
sudo test ! -e /swapfile
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
printf '%s\n' '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
sudo findmnt --verify --tab-file /etc/fstab
swapon --show --bytes
free -h
```

`fallocate`를 지원하지 않는 파일시스템이면 임의로 반복하지 말고 운영자와 대체 생성 방법을 정합니다. 재부팅 승인을 받은 뒤에는 재부팅 후 `swapon --show --bytes`와 `free -h`를 다시 확인합니다.

## 6. 단계별 검증과 복구

외부 공개 전에는 인스턴스 내부에서 다음 순서로 확인합니다.

```bash
curl --fail --silent --show-error http://127.0.0.1:8000/api/health
curl --fail --silent --show-error http://127.0.0.1/api/health
ss -ltnp
sudo -u ai-assistant test -r /etc/ai-assistant/ai-assistant.env
sudo -u ai-assistant test -w /var/lib/ai-assistant
```

가입 → 로그인 → 채팅 두 턴 → 기록 조회를 승인된 비민감 계정으로 확인하고, DB와 운영 로그를 교차 확인합니다. 서비스 재시작 전후 같은 사용자의 기록이 남아 있어야 합니다. 실제 AI 권한이 없다면 production/real을 Mock 성공으로 바꾸지 않고 REAL_AI를 대기 상태로 둡니다.

외부 검증은 공개 승인 후 다른 네트워크에서 수행하며 URL·시각·HTTP/TLS 조건을 기록합니다. 아래 복구는 이 문서의 **최초 설치가 새로 만든 설정만** 제거하고, 보존 이름으로 옮긴 기본 site를 되돌립니다. 기존 설정이 있어 최초 설치를 중단한 경우에는 이 절차를 쓰지 않고 그 시스템의 변경 계획을 따릅니다. DB·환경 파일·앱 checkout은 삭제·초기화하지 않고 백업/복구 책임자에게 인계합니다.

```bash
sudo systemctl disable --now ai-assistant.service || true
sudo test ! -L /etc/nginx/sites-enabled/ai-assistant || sudo unlink /etc/nginx/sites-enabled/ai-assistant
if sudo test -L /etc/nginx/sites-enabled/default.disabled-ai-assistant; then
  if sudo test -e /etc/nginx/sites-enabled/default || sudo test -L /etc/nginx/sites-enabled/default; then
    echo 'default site 경로가 다시 사용 중이므로 자동 복원을 중단합니다.' >&2
    exit 1
  fi
  sudo mv /etc/nginx/sites-enabled/default.disabled-ai-assistant /etc/nginx/sites-enabled/default
fi
sudo rm -f /etc/nginx/sites-available/ai-assistant
sudo rm -f /etc/systemd/system/ai-assistant.service
sudo systemctl daemon-reload
sudo nginx -t
sudo systemctl reload nginx
```

## 7. 현재 미실행 항목

- AWS 계정·리전·AMI·인스턴스·요금 조건 확인
- EC2 생성, SSH 접속, 패키지 설치, 2GB swap 적용
- 보안 그룹 22/80/443 변경과 8000 비공개 확인
- DNS·TLS 인증서 구성 또는 HTTP 임시 시연 승인
- 실제 공급자 두 턴과 비용/빈도 관찰
- 다른 네트워크의 공개 URL 검증과 재시작 보존 확인

이 항목은 승인과 외부 상태가 필요하므로 `PUBLIC_URL=BLOCKED_EXTERNAL`, `REAL_AI=BLOCKED_EXTERNAL`을 유지합니다.
