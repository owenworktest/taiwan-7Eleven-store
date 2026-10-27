import json
import re

import httpx

from store_io import update_readme, write_outputs

STOREMAP_URL = "https://www.family.com.tw/Marketing/storemap/"
# api.map.com.tw 的 https 無法連線（TLS 交握失敗），只能走 http
API_URL = "http://api.map.com.tw/net/familyShop.aspx"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    # 沒帶 family.com.tw 的 Referer 會回傳空白 HTML 而不是資料
    "Referer": STOREMAP_URL,
}

API_KEY = re.compile(r"getAPI\.asp\?v=1&key=(\w+)")

# 以經緯度框選，範圍需涵蓋金門（118.2）與連江，不可縮到 119 否則會漏掉外島門市
# l（圖資縮放層級）必須帶，省略的話 API 一律回傳空陣列
QUERY = {
    "l": "10",
    "searchType": "ShowStore",
    "type": "",
    "vLeft": "118.0",
    "vRight": "122.5",
    "vTop": "26.5",
    "vBottom": "21.5",
}


def fetch_api_key(client: httpx.Client) -> str:
    """從店鋪地圖頁面取出 api.map.com.tw 的金鑰，避免寫死在程式中。"""
    html = client.get(STOREMAP_URL, follow_redirects=True).text
    match = API_KEY.search(html)
    if not match:
        raise RuntimeError("無法從全家店鋪地圖頁面取得 api.map.com.tw 金鑰")
    return match.group(1)


def main():
    with httpx.Client(headers=HEADERS, timeout=60) as client:
        key = fetch_api_key(client)

        res = client.get(API_URL, params={**QUERY, "key": key})
        res.raise_for_status()

        # 回應是包在小括號裡的 UTF-8 JSON：([{...},{...}])
        body = res.text.strip()
        if not body.startswith("("):
            raise RuntimeError("全家 API 回應格式非預期，可能是金鑰失效或 Referer 被擋")
        entries = json.loads(body[1:-1])

    stores = {
        entry["pkey"]: {
            "store": entry["NAME"].strip(),
            "address": entry["addr"].strip(),
        }
        for entry in entries
    }

    write_outputs(stores, "stores-familymart")
    update_readme("全家", len(stores))


if __name__ == "__main__":
    main()
