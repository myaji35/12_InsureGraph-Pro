"""
브라우저 기반 크롤러

Selenium을 사용하여 JavaScript 렌더링이 필요하거나 봇 차단이 있는 웹사이트를 크롤링합니다.
"""
import time
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from loguru import logger


class BrowserCrawler:
    """
    Selenium 기반 브라우저 크롤러

    JavaScript 기반 동적 페이지나 봇 차단이 있는 웹사이트를 크롤링합니다.
    """

    def __init__(self, headless: bool = True, timeout: int = 30):
        """
        Args:
            headless: 헤드리스 모드 사용 여부
            timeout: 페이지 로딩 타임아웃 (초)
        """
        self.headless = headless
        self.timeout = timeout
        self.driver: Optional[webdriver.Chrome] = None

    def _init_driver(self):
        """Chrome WebDriver 초기화"""
        try:
            chrome_options = Options()

            if self.headless:
                chrome_options.add_argument("--headless=new")

            # 봇 감지 우회를 위한 옵션
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # 일반적인 브라우저처럼 보이도록 User-Agent 설정
            chrome_options.add_argument(
                "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )

            # 성능 최적화 옵션
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")

            # SSL 인증서 오류 무시 (한화생명 SSL 에러 대응)
            chrome_options.add_argument("--ignore-certificate-errors")
            chrome_options.add_argument("--ignore-ssl-errors")

            # WebDriver 생성
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            # 암시적 대기 설정
            self.driver.implicitly_wait(10)

            # WebDriver 감지 우회 스크립트 실행
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            logger.info("Chrome WebDriver 초기화 완료")

        except Exception as e:
            logger.error(f"WebDriver 초기화 실패: {e}")
            raise

    def __enter__(self):
        """컨텍스트 매니저 진입"""
        self._init_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.close()

    def close(self):
        """브라우저 종료"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Chrome WebDriver 종료 완료")
            except Exception as e:
                logger.warning(f"WebDriver 종료 중 오류: {e}")

    def test_url_access(self, url: str) -> Dict[str, any]:
        """
        URL 접근 테스트

        Args:
            url: 테스트할 URL

        Returns:
            테스트 결과 딕셔너리
        """
        result = {
            "success": False,
            "url": url,
            "status_code": None,
            "page_title": None,
            "content_length": 0,
            "load_time": 0,
            "error": None,
            "screenshots": [],
        }

        if not self.driver:
            self._init_driver()

        try:
            start_time = time.time()

            # 페이지 로드
            logger.info(f"페이지 로드 시작: {url}")
            self.driver.get(url)

            # 페이지 로드 대기 (document.readyState == 'complete')
            WebDriverWait(self.driver, self.timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )

            load_time = time.time() - start_time

            # 페이지 정보 수집
            result["success"] = True
            result["page_title"] = self.driver.title
            result["content_length"] = len(self.driver.page_source)
            result["load_time"] = round(load_time, 2)
            result["current_url"] = self.driver.current_url

            logger.info(f"페이지 로드 성공: {url} (소요시간: {load_time:.2f}초)")

        except TimeoutException as e:
            result["error"] = f"페이지 로드 타임아웃 ({self.timeout}초 초과)"
            logger.error(f"페이지 로드 타임아웃: {url}")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"페이지 접근 실패: {url} - {e}")

        return result

    def find_pdf_links(
        self,
        url: str,
        selectors: Optional[List[str]] = None,
        wait_for_selector: Optional[str] = None,
        wait_time: int = 5
    ) -> List[Dict[str, str]]:
        """
        페이지에서 PDF 링크 찾기

        Args:
            url: 크롤링할 URL
            selectors: PDF 링크를 찾을 CSS 셀렉터 리스트
            wait_for_selector: 페이지 로드 후 대기할 셀렉터
            wait_time: 대기 시간 (초)

        Returns:
            PDF 링크 정보 리스트
        """
        if not self.driver:
            self._init_driver()

        pdf_links = []

        try:
            # 페이지 로드
            self.driver.get(url)

            # 특정 셀렉터 대기
            if wait_for_selector:
                try:
                    WebDriverWait(self.driver, wait_time).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_selector))
                    )
                except TimeoutException:
                    logger.warning(f"셀렉터 대기 타임아웃: {wait_for_selector}")

            # 동적 콘텐츠 로딩 대기
            time.sleep(wait_time)

            # 기본 셀렉터
            if selectors is None:
                selectors = [
                    "a[href$='.pdf']",
                    "a[href*='.pdf']",
                    "a[href*='download']",
                    "a:contains('약관')",
                    "a:contains('PDF')",
                ]

            # PDF 링크 찾기
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    for elem in elements:
                        try:
                            href = elem.get_attribute("href")
                            text = elem.text.strip()

                            if href and (".pdf" in href.lower() or "download" in href.lower()):
                                pdf_links.append({
                                    "url": href,
                                    "text": text,
                                    "title": elem.get_attribute("title") or "",
                                })
                        except Exception as e:
                            logger.debug(f"링크 추출 실패: {e}")
                            continue

                except NoSuchElementException:
                    continue

            logger.info(f"{len(pdf_links)}개의 PDF 링크 발견: {url}")

        except Exception as e:
            logger.error(f"PDF 링크 찾기 실패: {url} - {e}")

        return pdf_links

    def get_page_content(self, url: str, wait_time: int = 5) -> str:
        """
        페이지 HTML 콘텐츠 가져오기

        Args:
            url: 가져올 URL
            wait_time: 동적 콘텐츠 로딩 대기 시간 (초)

        Returns:
            페이지 HTML 소스
        """
        if not self.driver:
            self._init_driver()

        try:
            self.driver.get(url)
            time.sleep(wait_time)
            return self.driver.page_source

        except Exception as e:
            logger.error(f"페이지 콘텐츠 가져오기 실패: {url} - {e}")
            return ""

    def take_screenshot(self, filepath: str) -> bool:
        """
        현재 페이지 스크린샷 저장

        Args:
            filepath: 저장할 파일 경로

        Returns:
            성공 여부
        """
        if not self.driver:
            logger.error("WebDriver가 초기화되지 않았습니다")
            return False

        try:
            self.driver.save_screenshot(filepath)
            logger.info(f"스크린샷 저장 완료: {filepath}")
            return True

        except Exception as e:
            logger.error(f"스크린샷 저장 실패: {e}")
            return False


def test_crawler():
    """크롤러 테스트"""
    test_urls = [
        "https://www.kbinsure.co.kr/CG302120001.ec",
        "https://www.samsungfire.com/vh/page/VH.HPIF0103.do",
        "https://www.idbins.com/FWMAIV1534.do",
    ]

    with BrowserCrawler(headless=True) as crawler:
        for url in test_urls:
            print(f"\n테스트 중: {url}")
            result = crawler.test_url_access(url)
            print(f"결과: {result}")

            if result["success"]:
                pdf_links = crawler.find_pdf_links(url)
                print(f"발견된 PDF 링크: {len(pdf_links)}개")
                for link in pdf_links[:5]:  # 처음 5개만 출력
                    print(f"  - {link['text']}: {link['url']}")


if __name__ == "__main__":
    test_crawler()
