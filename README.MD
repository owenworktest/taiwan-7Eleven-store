# Taiwan Convenience Store Scraper

## Overview
這個專案提供台灣四大超商（7-ELEVEN、全家、萊爾富、OK超商）門市列表爬蟲，
也可直接取用已抓取好的資料檔快速使用。

- 採用 Github Action 每日自動更新
- 參考文章：[iThome - 使用爬蟲取得 7-11 門市清單](https://ithelp.ithome.com.tw/articles/10193779)

## 資料集

| 超商 | 檔名前綴 | 筆數 | 更新日期 | 爬蟲 | 資料來源 |
| --- | --- | --- | --- | --- | --- |
| 7-ELEVEN | `stores` | 7332 | 2026/10/27 | `711.py` | ibon 門市查詢 |
| 全家 | `stores-familymart` | 4539 | 2026/10/27 | `familymart.py` | 全家店鋪地圖 api.map.com.tw |
| 萊爾富 | `stores-hilife` | 1868 | 2026/10/27 | `hilife.py` | 萊爾富官網 webapi |
| OK超商 | `stores-okmart` | 372 | 2026/10/27 | `okmart.py` | OK超商官網門市查詢（含 OK mini） |

## Project Structure
```
.
├─ 711.py                          # 7-ELEVEN 爬蟲
├─ familymart.py                   # 全家爬蟲
├─ hilife.py                       # 萊爾富爬蟲
├─ okmart.py                       # OK超商爬蟲
├─ store_io.py                     # 共用輸出 / README 更新
├─ stores.json                     # 7-ELEVEN 門市資料（另有 -pretty 版）
├─ stores-familymart.json          # 全家門市資料
├─ stores-hilife.json              # 萊爾富門市資料
├─ stores-okmart.json              # OK超商門市資料
└─ requirements.txt                # 依賴
```

## Output Formats
每個品牌都會同步輸出兩種 JSON，內容完全相同，依使用情境選用：

| 檔名 | 格式 | 適合用途 |
| --- | --- | --- |
| `{前綴}.json` | JSON（單行壓縮） | 程式讀取、檔案最小化 |
| `{前綴}-pretty.json` | JSON（indent=2） | 給人看、版本控制 diff 友善 |

四個品牌的資料結構一致，皆以門市編號為 key：
```json
{
  "110817": { "store": "千翔", "address": "台北市中正區許昌街17號1樓" }
}
```

## Usage

若不需要最新資料，可直接使用 repo 內已生成的 JSON，不必跑爬蟲。

### 本地執行

四支爬蟲各自獨立，**跑哪支就只更新哪家的檔案**，彼此不影響。
請在 repo 根目錄執行（四支共用 `store_io.py`，換目錄會 import 失敗）。

```bash
cd /path/to/taiwan-7Eleven-store

# 1. 建立虛擬環境並安裝依賴（第一次才需要）
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt     # Windows
# source .venv/bin/activate && pip install -r requirements.txt   # macOS / Linux

# 2. 只更新想要的超商
.venv/Scripts/python okmart.py        # OK超商
.venv/Scripts/python familymart.py    # 全家
.venv/Scripts/python hilife.py        # 萊爾富
.venv/Scripts/python 711.py           # 7-ELEVEN
```

啟用虛擬環境後（`source .venv/Scripts/activate`）可直接用 `python okmart.py`。

| 指令 | 產出檔案 | 請求數 |
| --- | --- | --- |
| `python 711.py` | `stores.json` / `stores-pretty.json` | 24 |
| `python familymart.py` | `stores-familymart.json` / `-pretty.json` | 2 |
| `python hilife.py` | `stores-hilife.json` / `-pretty.json` | 2 |
| `python okmart.py` | `stores-okmart.json` / `-pretty.json` | 2 |

每支跑完會順手更新上方資料表中**自己那一列**的筆數與日期，不會動到其他品牌。

> **跑 `hilife.py` 請節制。** 萊爾富有 Akamai WAF，會比對 TLS 指紋（故改用
> `curl_cffi` 偽裝 Chrome），且短時間內約十幾次請求就會整站 403 封鎖數小時。
> 它一次請求就能取回全部門市，失敗時不要重試，等待即可。

### 直接讀取資料檔

```python
import json

with open("stores-familymart.json", encoding="utf-8") as f:
    stores = json.load(f)

print(stores["020909"])
# {'store': '全家芳苑王功店', 'address': '彰化縣芳苑鄉芳漢路王功段535號'}
```

合併四家（店號在不同品牌間可能重複，建議加上品牌前綴）：

```python
import json

BRANDS = {
    "711": "stores.json",
    "familymart": "stores-familymart.json",
    "hilife": "stores-hilife.json",
    "okmart": "stores-okmart.json",
}

all_stores = {}
for brand, path in BRANDS.items():
    with open(path, encoding="utf-8") as f:
        for store_id, info in json.load(f).items():
            all_stores[f"{brand}-{store_id}"] = {"brand": brand, **info}
```

### 不想自己跑爬蟲

直接抓 repo 內每日更新的檔案即可（raw 連結，記得換成自己的 repo 路徑）：

```bash
curl -O https://raw.githubusercontent.com/<user>/<repo>/master/stores-familymart.json
```

## Notes
- 使用非公開 API 請保持禮貌，避免造成伺服器負擔。
- 各家原始資料的全形使用差異極大（全家約 99% 地址用全形數字，7-ELEVEN 幾乎全半形），
  輸出前已統一轉為半形，下游可直接做跨品牌地址搜尋。
- 萊爾富約 164 筆門市名稱含 `(暫歇中)`，資料保留原樣，如需過濾請自行處理。
- 全家的 `api.map.com.tw` 金鑰由爬蟲從店鋪地圖頁面即時抓取，不寫死；該站僅支援 `http`。
- 萊爾富 API 一次請求即可取回全部門市，**請勿**改寫成逐縣市迴圈，其 WAF 會在短時間多次請求後封鎖 IP。
- 萊爾富的 Akamai WAF 會比對 TLS 指紋，一般 HTTP 客戶端（httpx / requests）會直接 403，
  因此 `hilife.py` 使用 `curl_cffi` 以 Chrome 指紋連線。
- 萊爾富部分門市名稱含有 `(暫歇中)` 標記，資料保留原樣，下游如需過濾請自行處理。
- 萊爾富原始地址帶有 3 碼郵遞區號前綴，爬蟲已移除以對齊其他品牌格式。
- 萊爾富僅在 17 個縣市設點（無花蓮、台東、澎湖、金門、連江）。
- 請勿過度大量呼叫，建議對資料做好快取與重用，如果你沒有特殊需求歡迎直接每日從本專案抓取最新資訊。
- 爬蟲行為需遵循相關網站使用規範與法律。

## License
資料來源為各超商官方網站，請依照原服務條款使用；
