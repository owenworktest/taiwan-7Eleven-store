import re

from curl_cffi import requests

from store_io import update_readme, write_outputs

BASE_URL = "https://www.hilife.com.tw"
HEADERS = {"Referer": f"{BASE_URL}/filter"}

# shop_adr 開頭帶 3 碼郵遞區號（例：505彰化縣鹿港鎮…），去除以對齊 7-11 的地址格式
ZIPCODE_PREFIX = re.compile(r"^\d{3,6}")


def main():
    # 萊爾富的 Akamai WAF 會比對 TLS 指紋，httpx / requests 一律 403（連首頁都進不去）。
    # curl_cffi 的 impersonate 會重現 Chrome 的 TLS ClientHello，才能通過。
    with requests.Session(impersonate="chrome", headers=HEADERS, timeout=60) as session:
        # 取得 anti-forgery token，cookie 由 session 自動保存，兩者缺一不可
        res = session.get(f"{BASE_URL}/webapi/api/AntiForgery/GetAntiForgeryToken")
        # 被 WAF 擋下時會回 HTML，直接拋出以免後續解析出現難懂的錯誤
        res.raise_for_status()
        token = res.json()["token"]

        # 五個欄位都要帶（即使是空值），只送 {} 會回傳 0 筆
        res = session.post(
            f"{BASE_URL}/webapi/api/ShopServices/GetShopServices",
            json={"City_Id": "", "Town_Id": "", "Shop_Id": "", "Services": [], "Shop_Name": ""},
            headers={"X-XSRF-TOKEN": token},
        )
        res.raise_for_status()
        data = res.json()

    if data.get("StatusCode") != 0:
        raise RuntimeError(f"萊爾富 API 回應異常: {data.get('Message')}")

    stores = {
        entry["shop_id"]: {
            "store": entry["shop_name"].strip(),
            "address": ZIPCODE_PREFIX.sub("", entry["shop_adr"].strip()),
        }
        for entry in data["Entries"]
    }

    write_outputs(stores, "stores-hilife")
    update_readme("萊爾富", len(stores))


if __name__ == "__main__":
    main()
