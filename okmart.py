import re

import httpx
from bs4 import BeautifulSoup

from store_io import update_readme, write_outputs

BASE_URL = "https://www.okmart.com.tw"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Referer": f"{BASE_URL}/convenient_shopsearch",
}

# 店號藏在 <a href="javascript:showshop('0005','新北市三重區成功路97號');">
SHOP_ID = re.compile(r"showshop\('([^']+)'")

# 查詢條件全部留空即可一次取得全部門市
QUERY = {"city": "", "zipcode": "", "key": "", "service": "", "service2": ""}

# 一般門市與 OK mini 兩份清單
ENDPOINTS = ["/convenient_shopSearch_Result.aspx", "/convenient_shopSearch_Result_mini.aspx"]


def parse_stores(html: str) -> dict:
    stores = {}
    for li in BeautifulSoup(html, "html.parser").select("li"):
        name, address, link = li.select_one("h2"), li.select_one("span"), li.select_one("a")
        if not (name and address and link):
            continue
        match = SHOP_ID.search(link.get("href", ""))
        if not match:
            continue
        stores[match.group(1)] = {
            "store": name.text.strip(),
            "address": address.text.strip(),
        }
    return stores


def main():
    all_stores = {}

    with httpx.Client(base_url=BASE_URL, headers=HEADERS, timeout=60) as client:
        for endpoint in ENDPOINTS:
            res = client.get(endpoint, params=QUERY)
            res.raise_for_status()
            stores = parse_stores(res.text)
            print(f"{endpoint} 取得 {len(stores)} 筆門市")
            all_stores.update(stores)

    write_outputs(all_stores, "stores-okmart")
    update_readme("OK超商", len(all_stores))


if __name__ == "__main__":
    main()
