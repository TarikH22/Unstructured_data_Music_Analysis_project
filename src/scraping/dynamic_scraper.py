import json
import os
import time
from datetime import datetime

import requests

from scraping.robots_utils import DEFAULT_USER_AGENT, get_headers, is_allowed_by_robots
from utils.logger import logger


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
RAW_SCRAPED_DIR = os.path.join(ROOT_DIR, "data", "raw", "scraped")
REQUEST_DELAY_SECONDS = 1.5


def _metadata(source, extraction_type, file_name=""):
    return {
        "source": source,
        "file_name": file_name,
        "type": extraction_type,
        "extraction_timestamp": datetime.utcnow().isoformat() + "Z",
    }


def _save_json(data, file_name):
    os.makedirs(RAW_SCRAPED_DIR, exist_ok=True)
    path = os.path.join(RAW_SCRAPED_DIR, file_name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


def scrape_json_endpoint(json_endpoint):
    if not is_allowed_by_robots(json_endpoint):
        logger.warning(f"robots.txt disallows JSON endpoint: {json_endpoint}")
        return []

    time.sleep(REQUEST_DELAY_SECONDS)
    response = requests.get(json_endpoint, headers=get_headers(DEFAULT_USER_AGENT), timeout=20)
    response.raise_for_status()
    data = response.json()

    records = []
    items = data.get("results", data if isinstance(data, list) else [])
    if isinstance(items, dict):
        items = [items]
    for item in items[:20]:
        records.append(
            {
                "title": str(item.get("trackName") or item.get("name") or item.get("title") or ""),
                "description": str(item.get("artistName") or item.get("body") or item.get("description") or ""),
                "price": str(item.get("trackPrice") or item.get("price") or ""),
                "date": str(item.get("releaseDate") or item.get("date") or ""),
                "link": str(item.get("trackViewUrl") or item.get("url") or ""),
                "metadata": _metadata(json_endpoint, "dynamic-json-endpoint", "dynamic_endpoint.json"),
            }
        )

    _save_json(records, "dynamic_endpoint.json")
    logger.info(f"Dynamic JSON endpoint records: {len(records)}")
    return records


def scrape_with_playwright(url):
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        logger.warning(f"Playwright unavailable: {e}")
        return []

    records = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=DEFAULT_USER_AGENT)
            page.goto(url, wait_until="networkidle", timeout=30000)
            items = page.locator("article, .quote, .card, .item").all()
            for item in items[:20]:
                title = ""
                desc = ""
                try:
                    title = (item.locator("h1, h2, h3, .title, .text").first.text_content(timeout=2000) or "").strip()
                except Exception:
                    title = ""
                try:
                    desc = (item.locator("p, .description, .author").first.text_content(timeout=2000) or "").strip()
                except Exception:
                    desc = ""

                if not title and not desc:
                    continue

                records.append(
                    {
                        "title": title,
                        "description": desc,
                        "metadata": _metadata(url, "dynamic-playwright", "dynamic_playwright.json"),
                    }
                )
            browser.close()
    except Exception as e:
        logger.warning(f"Playwright scraping failed: {e}")
        return []

    _save_json(records, "dynamic_playwright.json")
    logger.info(f"Playwright dynamic records: {len(records)}")
    return records


def scrape_with_selenium(url):
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
    except Exception as e:
        logger.warning(f"Selenium unavailable: {e}")
        return []

    records = []
    driver = None
    try:
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument(f"user-agent={DEFAULT_USER_AGENT}")
        driver = webdriver.Chrome(options=options)
        time.sleep(REQUEST_DELAY_SECONDS)
        driver.get(url)
        time.sleep(2)
        elements = driver.find_elements("css selector", "article, .quote, .card, .item")
        for element in elements[:20]:
            text = element.text.strip()
            if text:
                records.append(
                    {
                        "title": text.split("\n")[0][:120],
                        "description": text[:400],
                        "metadata": _metadata(url, "dynamic-selenium", "dynamic_selenium.json"),
                    }
                )
    except Exception as e:
        logger.warning(f"Selenium scraping failed: {e}")
        return []
    finally:
        if driver is not None:
            driver.quit()

    _save_json(records, "dynamic_selenium.json")
    logger.info(f"Selenium dynamic records: {len(records)}")
    return records


def scrape_dynamic_content(
    page_url="https://quotes.toscrape.com/js/",
    json_endpoint="https://itunes.apple.com/search?term=coldplay&entity=song&limit=10",
):
    if is_allowed_by_robots(page_url):
        try:
            json_records = scrape_json_endpoint(json_endpoint)
            if json_records:
                return json_records
        except Exception as e:
            logger.warning(f"JSON endpoint strategy failed: {e}")

        playwright_records = scrape_with_playwright(page_url)
        if playwright_records:
            return playwright_records
        return scrape_with_selenium(page_url)

    logger.warning(f"robots.txt disallows or blocks target: {page_url}")
    return []


if __name__ == "__main__":
    results = scrape_dynamic_content()
    print(f"Dynamic scrape results: {len(results)}")
