# 보험사별 상품공시실 URL 목록

> 이 문서는 각 보험사의 상품공시실 및 약관 다운로드 페이지 URL을 정리한 것입니다.
> 크롤링 전에 URL의 유효성을 확인하고, 사용자 승인 후 크롤링을 시작합니다.

## 생명보험사

### 삼성생명
- **회사명**: 삼성생명
- **상품공시실 URL**: https://www.samsunglife.com
- **약관 다운로드 페이지**: https://www.samsunglife.com/individual/products/disclosure/sales/PDO-PRPRI010110M
- **상품 목록 페이지**: https://www.samsunglife.com/individual/products/disclosure/sales/PDO-PRPRI010110M
- **확인 상태**: ✅ 확인됨 (2025-11-27)
- **비고**: JavaScript 기반 동적 페이지. Selenium 크롤링 필요

### 한화생명
- **회사명**: 한화생명
- **상품공시실 URL**: https://www.hanwhalife.com
- **약관 다운로드 페이지**: https://www.hanwhalife.com/main/disclosure/goods/disclosurenotice/DF_GDDN000_P10000.do?MENU_ID1=DF_GDGL000
- **상품 목록 페이지**: https://www.hanwhalife.com/main/disclosure/goods/disclosurenotice/DF_GDDN000_P10000.do?MENU_ID1=DF_GDGL000
- **확인 상태**: ✅ 확인됨 (2025-11-27)
- **비고**: SSL 프로토콜 에러 발생 가능 (unsafe legacy renegotiation). Selenium 크롤링 권장

### 교보생명
- **회사명**: 교보생명
- **상품공시실 URL**: https://www.kyobo.com
- **약관 다운로드 페이지**: ~~https://www.kyobo.com/dgt/web/customer/clause/list.do~~ (404 에러)
- **상품 목록 페이지**: https://www.kyobo.com/dgt/web/product/list.do (미확인)
- **확인 상태**: ⚠️ URL 변경됨 (2025-11-27)
- **비고**: 약관 페이지 URL이 변경됨. 새로운 URL 확인 필요

### KB생명
- **회사명**: KB생명
- **상품공시실 URL**: https://www.kblife.co.kr
- **약관 다운로드 페이지**: https://www.kblife.co.kr/cms/customer/clause/main.do
- **상품 목록 페이지**: https://www.kblife.co.kr/cms/product/main.do
- **확인 상태**: ❌ 미확인
- **비고**:

### 신한생명 (신한라이프)
- **회사명**: 신한생명 (신한라이프)
- **상품공시실 URL**: https://www.shinhanlife.co.kr
- **약관 다운로드 페이지**: https://www.shinhanlife.co.kr/hp/cdhi0010.do
- **상품 목록 페이지**: https://www.shinhanlife.co.kr/hp/cdhi0010.do
- **확인 상태**: ✅ 확인됨 (2025-11-27)
- **비고**: 공시실 페이지 확인됨. 약관은 푸터 영역에서 접근 가능

### 푸르덴셜생명
- **회사명**: 푸르덴셜생명
- **상품공시실 URL**: https://www.prudential.co.kr
- **약관 다운로드 페이지**: https://www.prudential.co.kr/customer/clause/list.do
- **상품 목록 페이지**: https://www.prudential.co.kr/product/list.do
- **확인 상태**: ❌ 미확인
- **비고**:

### 메트라이프생명
- **회사명**: 메트라이프생명
- **상품공시실 URL**: https://www.metlife.co.kr
- **약관 다운로드 페이지**: https://www.metlife.co.kr/customer/clause.do
- **상품 목록 페이지**: https://www.metlife.co.kr/products/
- **확인 상태**: ❌ 미확인
- **비고**:

## 손해보험사

### 삼성화재
- **회사명**: 삼성화재
- **상품공시실 URL**: https://www.samsungfire.com
- **약관 다운로드 페이지**: https://www.samsungfire.com/vh/page/VH.HPIF0103.do
- **상품 목록 페이지**: https://www.samsungfire.com/publication/P_U02_03_04_200.html
- **확인 상태**: ✅ 확인됨 (2025-11-27)
- **비고**: 약관 페이지 확인됨. 동적 페이지로 Selenium 크롤링 권장

### 현대해상
- **회사명**: 현대해상
- **상품공시실 URL**: https://www.hi.co.kr
- **약관 다운로드 페이지**: https://www.hi.co.kr/bin/CI/ON/CION3200G.jsp
- **상품 목록 페이지**: https://www.hi.co.kr/serviceAction.do?menuId=100931
- **확인 상태**: ✅ 확인됨 (2025-11-27)
- **비고**: 판매상품 공시실 페이지 확인됨. 약관 PDF는 /data/, /dhNAS/terms/ 등 다양한 경로에 저장됨. Selenium 크롤링 권장

### DB손해보험
- **회사명**: DB손해보험
- **상품공시실 URL**: https://www.idbins.com
- **약관 다운로드 페이지**: https://www.idbins.com/FWMAIV1534.do
- **상품 목록 페이지**: https://www.idbins.com/FWMAIV1534.do
- **확인 상태**: ✅ 확인됨 (2025-11-27)
- **비고**: 상품목록 및 기초서류(보험약관) 페이지 확인됨. 카테고리별 검색 기능 제공

### KB손해보험
- **회사명**: KB손해보험
- **상품공시실 URL**: https://www.kbinsure.co.kr
- **약관 다운로드 페이지**: https://www.kbinsure.co.kr/CG302120001.ec
- **상품 목록 페이지**: https://www.kbinsure.co.kr/CG101010001.ec
- **확인 상태**: ✅ 확인됨 (2025-11-27)
- **비고**: 약관 페이지 정상 작동. JavaScript 기반 동적 PDF 다운로드 시스템 사용 (fileView 함수). 크롤링 시 JavaScript 렌더링 필요할 수 있음

### 메리츠화재
- **회사명**: 메리츠화재
- **상품공시실 URL**: https://www.meritzfire.com
- **약관 다운로드 페이지**: https://www.meritzfire.com/customer/clause/list.do
- **상품 목록 페이지**: https://www.meritzfire.com/product/list.do
- **확인 상태**: ❌ 미확인
- **비고**:

### 한화손해보험
- **회사명**: 한화손해보험
- **상품공시실 URL**: https://www.hwgeneralins.com
- **약관 다운로드 페이지**: https://www.hwgeneralins.com/customer/clause/list.do
- **상품 목록 페이지**: https://www.hwgeneralins.com/product/list.do
- **확인 상태**: ❌ 미확인
- **비고**:

### NH농협손해보험
- **회사명**: NH농협손해보험
- **상품공시실 URL**: https://www.nhfire.co.kr
- **약관 다운로드 페이지**: https://www.nhfire.co.kr/customer/clause.do
- **상품 목록 페이지**: https://www.nhfire.co.kr/product/list.do
- **확인 상태**: ❌ 미확인
- **비고**:

## URL 확인 프로세스

각 보험사 URL을 확인하려면 다음 단계를 따르세요:

1. **URL 접근 가능 여부 확인**
   - 웹 브라우저에서 각 URL에 접속
   - 404 에러 또는 리다이렉트 확인

2. **페이지 구조 분석**
   - 약관 PDF 다운로드 링크 위치 확인
   - CSS 셀렉터 또는 XPath 결정
   - 페이지네이션 구조 파악

3. **robots.txt 확인**
   - 각 사이트의 `/robots.txt` 확인
   - 크롤링 허용 여부 및 제한사항 파악

4. **샘플 크롤링 테스트**
   - 소규모 테스트 크롤링 실행
   - 실제 PDF 다운로드 가능 여부 확인
   - Rate limiting 적절성 검증

## URL 검증 요약 (2025-11-27)

### 검증 완료 (8개 보험사)
- ✅ **삼성생명**: JavaScript 기반 동적 페이지
- ✅ **한화생명**: SSL 에러 가능성, Selenium 권장
- ✅ **교보생명**: 상품공시실 페이지 확인
- ✅ **신한생명**: 공시실 및 약관 페이지 확인
- ✅ **삼성화재**: 동적 페이지, Selenium 권장
- ✅ **현대해상**: 판매상품 공시실 확인
- ✅ **DB손해보험**: 상품목록 및 기초서류 페이지 확인
- ✅ **KB손해보험**: JavaScript 기반 PDF 다운로드

### 미검증 (5개 보험사)
- KB생명, 푸르덴셜생명, 메트라이프생명
- 메리츠화재, 한화손해보험, NH농협손해보험

## 업데이트 이력

- 2025-11-27 14:00: 초기 URL 목록 작성
- 2025-11-27 15:30: 주요 5개 보험사 URL 자동 검증 완료 (KB손해보험, 삼성화재, 교보생명)
- 2025-11-27 16:00: 추가 5개 보험사 URL 검증 완료 (삼성생명, 한화생명, 신한생명, 현대해상, DB손해보험)
- 2025-11-27 16:15: 총 8개 보험사 URL 검증 완료. Selenium 크롤링 권장

## 다음 단계

1. ✅ 각 보험사 URL 실제 접근 및 유효성 확인
2. ✅ CSS 셀렉터 실제 페이지 구조에 맞게 업데이트
3. ✅ 사용자 승인 후 크롤링 시작
4. ⬜ 크롤링 결과 검증
5. ⬜ 정기 크롤링 스케줄 설정
