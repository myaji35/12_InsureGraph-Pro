"""
삼성화재 PDF 버튼 클릭 디버깅
"""
import asyncio
from app.services.playwright_crawler import PlaywrightCrawler


async def debug_pdf_click():
    """PDF 버튼 클릭 시 동작 확인"""
    crawler = PlaywrightCrawler(headless=False, timeout=30000)

    try:
        await crawler.initialize()
        page = crawler.page

        # 페이지 로드
        print("Loading page...")
        await page.goto("https://www.samsungfire.com/vh/page/VH.HPIF0103.do", wait_until="networkidle")
        await asyncio.sleep(3)

        # Step1: 자동차보험 클릭
        print("\nClicking 자동차보험...")
        auto_insurance = await page.query_selector("#depth1 li a:has-text('자동차보험')")
        if auto_insurance:
            await auto_insurance.click()
            await asyncio.sleep(1.5)

        # Step2: 개인용 클릭
        print("Clicking 개인용...")
        individual = await page.query_selector("#product_gubun > li > a:has-text('개인용')")
        if individual:
            await individual.click()
            await asyncio.sleep(1.5)

        # Step3: 첫 번째 상품 클릭
        print("Clicking first product...")
        first_product = await page.query_selector("#product_list li a")
        if first_product:
            product_name = await first_product.inner_text()
            print(f"Product: {product_name}")
            await first_product.click()
            await asyncio.sleep(1.5)

        # Step4: 첫 번째 판매기간 클릭
        print("Clicking first date...")
        first_date = await page.query_selector("#date_list li a")
        if first_date:
            date_text = await first_date.inner_text()
            print(f"Date: {date_text}")
            await first_date.click()
            await asyncio.sleep(2)

        # 보험약관 버튼 찾기
        print("\n=== Finding 보험약관 button ===")
        yakgwan_button = await page.query_selector("#pdfDiv2 button:has-text('보험약관')")

        if yakgwan_button:
            button_id = await yakgwan_button.get_attribute("id")
            print(f"Button ID: {button_id}")

            # 네트워크 요청 모니터링
            captured_requests = []

            def handle_request(request):
                url = request.url
                if 'pdf' in url.lower() or 'download' in url.lower():
                    print(f"[NETWORK REQUEST] {url}")
                    captured_requests.append(url)

            page.on("request", handle_request)

            # 팝업 감지
            print("\n=== Clicking 보험약관 button (watching for popup) ===")
            popup_opened = False
            popup_url = None

            try:
                async with page.expect_event("popup", timeout=5000) as popup_info:
                    await yakgwan_button.click()
                    popup = await popup_info.value
                    popup_url = popup.url
                    popup_opened = True
                    print(f"[POPUP OPENED] {popup_url}")
                    await asyncio.sleep(1)
                    await popup.close()
            except Exception as e:
                print(f"[NO POPUP] {e}")

            await asyncio.sleep(2)

            # 결과 출력
            print("\n=== Results ===")
            print(f"Popup opened: {popup_opened}")
            if popup_url:
                print(f"Popup URL: {popup_url}")
            print(f"Captured network requests: {len(captured_requests)}")
            for req in captured_requests:
                print(f"  - {req}")

            # 페이지 소스에서 PDF 관련 스크립트 찾기
            print("\n=== Checking page source for PDF scripts ===")
            page_content = await page.content()

            # fnPdfDownV 함수 찾기
            if "fnPdfDownV" in page_content:
                print("Found fnPdfDownV function!")
                import re
                matches = re.findall(r"function fnPdfDownV.*?\}", page_content, re.DOTALL)
                if matches:
                    print(f"Function definition:\n{matches[0][:500]}")

            # pdfCnt_2 관련 이벤트 리스너 찾기
            if button_id in page_content:
                print(f"\nFound {button_id} in page source")

        print("\n=== Keeping browser open for 20 seconds ===")
        await asyncio.sleep(20)

    finally:
        await crawler.close()


if __name__ == "__main__":
    asyncio.run(debug_pdf_click())
