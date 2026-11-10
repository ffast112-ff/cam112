# FitPlan 업데이트 배포

이 디렉터리는 FitPlan Android 앱의 업데이트 메타데이터를 보관합니다.

배포 원칙:
- 기존 FieldCamera 릴리스와 파일을 변경하지 않습니다.
- 동일한 앱 서명 인증서로 생성한 APK만 새 버전으로 배포합니다.
- APK를 실제로 게시하고 링크 및 버전을 검증한 다음 `latest.json`을 갱신합니다.
- 사용자는 FitPlan 시작 시 `latest.json`을 조회하고 새 버전이 있으면 알림을 받습니다.
- APK 설치는 Android에서 사용자가 승인합니다.
