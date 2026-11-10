# FitPlan Android 배포

## 현황
- 현재 공개 정식 최신 버전: 1.9.5 (fitplan/latest.json)
- 1.9.8은 1.9.7의 서명키를 고정한 후속 버전으로 제작됨 (아직 GitHub 미게시)
- 1.9.8은 1.9.7 시험판을 업데이트할 수 있지만, 1.9.5 정식 앱 위에는 설치되지 않습니다.
- 1.9.5 운동 기록: 기존 앱에서 설정 > 기록 백업·복원 > 전체 데이터 백업 보기로 외부 백업 후, 새 앱에서 복원해야 합니다. 성공 확인 전 기존 앱 삭제 금지.

## GitHub Actions 자동 배포 초기 설정
- 자동 배포 워크플로: .github/workflows/fitplan-release.yml
- 버전: fitplan/version.json (version, version_code)
- 앱 소스: fitplan/app/ 폴더 또는 최초 fitplan/source.zip 압축파일 (ZIP 루트에는 build_apk.py, assets/ 등)
- 소스 ZIP 또는 소스파일을 변경하면 Actions에서 빌드, 서명, 릴리스 생성, latest.json 갱신

## Actions Secrets 두 개 등록 (필수)
Settings > Secrets and variables > Actions > New repository secret
1. FITPLAN_SIGNING_KEY_PEM_B64: 1.9.7/1.9.8 서명 개인키 PEM의 base64 값
2. FITPLAN_SIGNING_CERT_DER_B64: 동일 인증서 DER의 base64 값

인증서 SHA-256: 2de78f098f47c444b4ef054be6dfbcbab49a374a3a30937ead5d9d73f5d6e99c

**절대 공개 GitHub Code/Issues/Releases에 개인키 또는 Secrets 파일을 업로드하지 마세요.**

## 안전 유의사항
- 1.9.5는 새로운 서명으로 덮어쓰지 못하므로 먼저 데이터 이관이 필요합니다.
- 1.9.8 배포 검증 전에는 fitplan/latest.json에 기록된 정식 1.9.5를 변경하지 않습니다.
- 이후 버전에는 패키지명 com.fitplan.autocv196 및 동일 서명, 증가하는 versionCode를 유지합니다.
- 기존 FieldCamera 릴리스는 변경하지 않습니다.
