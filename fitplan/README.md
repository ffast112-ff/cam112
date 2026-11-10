# FitPlan Android 자동 업데이트

현재 정식 최신 버전: 1.9.5

## 자동 배포 준비 상태

- GitHub Actions 워크플로: .github/workflows/fitplan-release.yml (등록됨)
- 소스가 반영되면 APK 빌드, 서명, FitPlan 전용 릴리스 게시, latest.json 갱신을 시도합니다.
- FieldCamera 릴리스와 파일은 수정하지 않습니다.

## 자동 배포를 활성화하기 전에 필요한 것

1. 기존 1.9.5에 사용된 원본 서명 개인키. APK로부터 개인키를 복구할 수 없습니다.
2. GitHub Actions Secrets: FITPLAN_SIGNING_KEY_PEM_B64 및 FITPLAN_SIGNING_CERT_DER_B64
3. fitplan/app/ 아래의 빌드 가능한 전체 앱 소스 및 fitplan/version.json

1.9.5 인증서 SHA-256: 841d4b5ce5eeaf428652494c6214db536a883f1fdb0c588413c5b1e76722a346

원본 서명키가 없거나 다른 키라면 자동 배포 작업은 실패하도록 차단했습니다. 기존 1.9.5는 삭제하지 마세요.

서명키를 찾을 수 없다면 데이터 백업/복원 여부를 확인한 후 새로운 서명으로 한 차례 이관해야 합니다.
