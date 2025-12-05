"""
삼성화재 PDF 버튼 구조 디버깅
"""
import asyncio
from app.services.playwright_crawler import PlaywrightCrawler


async def debug_pdf_buttons():
    """PDF 버튼 구조 확인"""
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

        # PDF 영역 확인
        print("\n=== Checking PDF area ===")

        # 1. pdfDiv2의 HTML 구조 확인
        pdf_div = await page.query_selector("#pdfDiv2")
        if pdf_div:
            html = await pdf_div.inner_html()
            print(f"PDF Div HTML:\n{html[:1000]}")
        else:
            print("ERROR: #pdfDiv2 not found!")

        # 2. 버튼 찾기 시도
        print("\n=== Looking for buttons ===")
        buttons = await page.query_selector_all("#pdfDiv2 button")
        print(f"Total buttons: {len(buttons)}")

        for i, button in enumerate(buttons[:5]):
            text = await button.inner_text()
            onclick = await button.get_attribute("onclick")
            disabled = await button.get_attribute("disabled")
            print(f"  Button {i+1}: '{text}' | onclick={onclick} | disabled={disabled}")

        # 3. 링크 찾기 시도
        print("\n=== Looking for links ===")
        links = await page.query_selector_all("#pdfDiv2 a")
        print(f"Total links: {len(links)}")

        for i, link in enumerate(links[:5]):
            text = await link.inner_text()
            href = await link.get_attribute("href")
            onclick = await link.get_attribute("onclick")
            print(f"  Link {i+1}: '{text}' | href={href} | onclick={onclick}")

        # 4. 보험약관 버튼/링크 찾기
        print("\n=== Looking for 보험약관 ===")
        yakgwan_elements = await page.query_selector_all("#pdfDiv2 :text('보험약관')")
        print(f"Elements with '보험약관': {len(yakgwan_elements)}")

        for i, elem in enumerate(yakgwan_elements):
            tag = await elem.evaluate("el => el.tagName")
            text = await elem.inner_text()
            onclick = await elem.get_attribute("onclick")
            href = await elem.get_attribute("href")
            disabled = await elem.get_attribute("disabled")
            print(f"  Element {i+1}:")
            print(f"    Tag: {tag}")
            print(f"    Text: '{text}'")
            print(f"    onclick: {onclick}")
            print(f"    href: {href}")
            print(f"    disabled: {disabled}")

        print("\n=== Pausing for 30 seconds for manual inspection ===")
        await asyncio.sleep(30)

    finally:
        await crawler.close()


if __name__ == "__main__":
    asyncio.run(debug_pdf_buttons())
