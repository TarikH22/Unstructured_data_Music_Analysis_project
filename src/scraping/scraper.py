import json
import os
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from scraping.robots_utils import DEFAULT_USER_AGENT, get_headers, is_allowed_by_robots
from utils.logger import logger


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
RAW_HTML_DIR = os.path.join(ROOT_DIR, "data", "raw", "html")
RAW_SCRAPED_DIR = os.path.join(ROOT_DIR, "data", "raw", "scraped")
REQUEST_DELAY_SECONDS = 1.5


def _ensure_dirs():
    os.makedirs(RAW_HTML_DIR, exist_ok=True)
    os.makedirs(RAW_SCRAPED_DIR, exist_ok=True)


def _metadata(source, file_name, page_number=None, extraction_type="scraped"):
    return {
        "source": source,
        "file_name": file_name,
        "type": extraction_type,
        "page_number": page_number,
        "extraction_timestamp": datetime.utcnow().isoformat() + "Z",
    }


def save_raw_html(html_text, file_name):
    _ensure_dirs()
    path = os.path.join(RAW_HTML_DIR, file_name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html_text)
    return path


def save_scraped_json(records, file_name="scraped_results.json"):
    _ensure_dirs()
    path = os.path.join(RAW_SCRAPED_DIR, file_name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    return path


def parse_html_records(html_text, source, page_number=None, file_name=""):
    soup = BeautifulSoup(html_text, "lxml")
    records = []

    # Pattern 1: tabular records
    for row in soup.select("table tbody tr"):
        record = {
            "name": row.select_one("td.name").get_text(strip=True) if row.select_one("td.name") else "",
            "year": row.select_one("td.year").get_text(strip=True) if row.select_one("td.year") else "",
            "wins": row.select_one("td.wins").get_text(strip=True) if row.select_one("td.wins") else "",
            "losses": row.select_one("td.losses").get_text(strip=True) if row.select_one("td.losses") else "",
            "description": row.select_one("td.description").get_text(strip=True)
            if row.select_one("td.description")
            else "",
            "price": row.select_one("td.price").get_text(strip=True) if row.select_one("td.price") else "",
            "date": row.select_one("td.date").get_text(strip=True) if row.select_one("td.date") else "",
            "metadata": _metadata(source, file_name, page_number=page_number),
        }
        records.append(record)

    # Pattern 2: generic cards
    for card in soup.select("article, .card, .item"):
        title_node = card.select_one("h1, h2, h3, .title")
        desc_node = card.select_one("p, .description")
        price_node = card.select_one(".price, .price_color")
        date_node = card.select_one("time, .date")
        link_node = card.select_one("a[href]")

        if not title_node:
            continue

        records.append(
            {
                "title": title_node.get_text(strip=True),
                "description": desc_node.get_text(strip=True) if desc_node else "",
                "price": price_node.get_text(strip=True) if price_node else "",
                "date": date_node.get_text(strip=True) if date_node else "",
                "link": link_node.get("href", "") if link_node else "",
                "metadata": _metadata(source, file_name, page_number=page_number),
            }
        )

    return records


def scrape_single_page(url, page_number=1):
    _ensure_dirs()
    if not is_allowed_by_robots(url):
        logger.warning(f"robots.txt disallows scraping or is unreachable: {url}")
        return []

    time.sleep(REQUEST_DELAY_SECONDS)
    response = requests.get(url, headers=get_headers(DEFAULT_USER_AGENT), timeout=20)
    response.raise_for_status()

    html_file = f"page_{page_number}.html"
    save_raw_html(response.text, html_file)
    records = parse_html_records(response.text, source=url, page_number=page_number, file_name=html_file)
    logger.info(f"Scraped single page: {url} -> {len(records)} records")
    return records


def scrape_multi_page(base_url, pages=3):
    all_records = []
    for page in range(1, pages + 1):
        if "{page}" in base_url:
            url = base_url.format(page=page)
        else:
            joiner = "&" if "?" in base_url else "?"
            url = f"{base_url}{joiner}page={page}"

        try:
            page_records = scrape_single_page(url, page_number=page)
            all_records.extend(page_records)
        except Exception as e:
            logger.error(f"Failed scraping page {page} ({url}): {e}")
        time.sleep(REQUEST_DELAY_SECONDS)

    save_scraped_json(all_records, "multi_page_scraped.json")
    logger.info(f"Scraped multi-page set: {len(all_records)} records")
    return all_records


def create_local_sample_html(pages=3):
    _ensure_dirs()
    template = """
<html>
  <body>
    <table>
      <tbody>
        <tr>
          <td class='name'>{name1}</td>
          <td class='year'>{year1}</td>
          <td class='wins'>{wins1}</td>
          <td class='losses'>{losses1}</td>
          <td class='price'>{price1}</td>
          <td class='date'>{date1}</td>
          <td class='description'>{desc1}</td>
        </tr>
        <tr>
          <td class='name'>{name2}</td>
          <td class='year'>{year2}</td>
          <td class='wins'>{wins2}</td>
          <td class='losses'>{losses2}</td>
          <td class='price'>{price2}</td>
          <td class='date'>{date2}</td>
          <td class='description'>{desc2}</td>
        </tr>
      </tbody>
    </table>
  </body>
</html>
"""
    seeds = [
        ("Coldplay", "2002", "11", "2", "$19.99", "2002-08-26", "A Rush of Blood to the Head"),
        ("Radiohead", "1997", "10", "1", "$17.99", "1997-06-16", "OK Computer"),
        ("The Weeknd", "2020", "9", "3", "$21.99", "2020-03-20", "After Hours"),
        ("Taylor Swift", "2022", "12", "0", "$24.99", "2022-10-21", "Midnights"),
    ]

    for page in range(1, pages + 1):
        a = seeds[(page - 1) % len(seeds)]
        b = seeds[(page) % len(seeds)]
        html = template.format(
            name1=a[0],
            year1=a[1],
            wins1=a[2],
            losses1=a[3],
            price1=a[4],
            date1=a[5],
            desc1=a[6],
            name2=b[0],
            year2=b[1],
            wins2=b[2],
            losses2=b[3],
            price2=b[4],
            date2=b[5],
            desc2=b[6],
        )
        save_raw_html(html, f"local_page_{page}.html")


def scrape_local_html_samples(pages=3):
    create_local_sample_html(pages=pages)
    records = []
    for page in range(1, pages + 1):
        file_name = f"local_page_{page}.html"
        path = os.path.join(RAW_HTML_DIR, file_name)
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        records.extend(parse_html_records(html, source="local-html", page_number=page, file_name=file_name))

    save_scraped_json(records, "local_multi_page_scraped.json")
    logger.info(f"Scraped local HTML samples: {len(records)} records")
    return records


if __name__ == "__main__":
    data = scrape_local_html_samples(pages=3)
    print(f"Scraped {len(data)} local records")
