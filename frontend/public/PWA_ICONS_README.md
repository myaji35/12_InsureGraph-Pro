# PWA Icons

PWA를 위해 다음 아이콘 파일이 필요합니다:

## Required Icons

1. **icon-192x192.png** (192x192 픽셀)
   - 홈 화면 아이콘
   - PWA 설치 시 사용되는 메인 아이콘

2. **icon-512x512.png** (512x512 픽셀)
   - 스플래시 스크린용 큰 아이콘
   - 고해상도 디스플레이 지원

## Icon Design Guidelines

- **배경**: 투명 배경 또는 #0ea5e9 (primary 색상)
- **디자인**: InsureGraph Pro 로고 또는 "IG" 이니셜
- **스타일**: 모던하고 전문적인 느낌
- **색상**: Primary (#0ea5e9), Dark (#1e40af), White

## Screenshots (Optional)

- **screenshot-mobile.png** (540x720)
- **screenshot-desktop.png** (1280x720)

## Temporary Solution

현재는 `/logo.png`를 사용하지만, 프로덕션 배포 전에 적절한 PWA 아이콘을 만들어야 합니다.

## Tools for Creating Icons

- **Favicon Generator**: https://realfavicongenerator.net/
- **PWA Asset Generator**: https://github.com/elegantapp/pwa-asset-generator
- **Figma/Sketch**: 디자인 툴에서 직접 export

## Installation

```bash
# PWA Asset Generator 사용 예시
npx pwa-asset-generator logo.svg public --icon-only
```
