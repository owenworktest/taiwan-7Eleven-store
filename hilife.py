import re

import httpx

from store_io import update_readme, write_outputs

BASE_URL = "https://www.hilife.com.tw"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Referer": f"{BASE_URL}/storeInquiry_street.aspx",
}

# shop_adr 開頭帶 3 碼郵遞區號（例：505彰化縣鹿港鎮…），去除以對齊 7-11 的地址格式
ZIPCODE_PREFIX = re.compile(r"^\d{3,6}")


def main():
    with httpx.Client(base_url=BASE_URL, headers=HEADERS, timeout=60) as client:
        # 取得 anti-forgery token，cookie 由 client 自動保存，兩者缺一不可
        res = client.get("/webapi/api/AntiForgery/GetAntiForgeryToken")
        # 短時間密集請求會被 Akamai WAF 以 403 擋下數小時，直接拋出以免後續解析出現難懂的錯誤
        res.raise_for_status()
        token = res.json()["token"]

        # 五個欄位都要帶（即使是空值），只送 {} 會回傳 0 筆
        res = client.post(
            "/webapi/api/ShopServices/GetShopServices",
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
