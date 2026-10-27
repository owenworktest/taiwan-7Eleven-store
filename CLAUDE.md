# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 專案概述

Python 網頁爬蟲，從各超商官方網站抓取全台門市資料並輸出結構化 YAML / JSON 檔案。
屬於 go-edpay.com 付款系統的一部分，門市資料供帳務前端做門市查詢使用。

目前涵蓋四家超商，每家一支獨立爬蟲、一組獨立輸出檔：

| 超商 | 爬蟲 | 輸出前綴 | 資料量 |
| --- | --- | --- | --- |
| 7-ELEVEN | `711.py` | `stores` | ~7,330 |
| 全家 | `familymart.py` | `stores-familymart` | ~4,540 |
| 萊爾富 | `hilife.py` | `stores-hilife` | ~1,870 |
| OK超商 | `okmart.py` | `stores-okmart` | ~370 |

## 常用指令

```bash
pip install -r requirements.txt   # 安裝依賴

python 711.py                     # 7-ELEVEN
python familymart.py              # 全家
python hilife.py                  # 萊爾富
python okmart.py                  # OK超商
```

本專案無測試或 lint 設定。

## 架構

`store_io.py` 為三支爬蟲共用：

- `normalize(text)` — 全形轉半形（刻意不用 NFKC，避免動到中文字）
- `write_outputs(stores, basename)` — 正規化後輸出 `{basename}.json` 與 `{basename}-pretty.json`
- `update_readme(brand, count)` — 更新 README.MD 資料表中該品牌的筆數與日期

每支爬蟲只負責抓取與正規化，最後呼叫這兩個函式。新增超商時照同樣模式加一支檔案，
並在 README 資料表與 `.github/workflows/auto_update.yml` 各加一列/一步。

## 各站資料來源

**7-ELEVEN** — `https://www.ibon.com.tw`
1. GET `/retail_inquiry.aspx` 取得縣市列表
2. 逐縣市 POST `/retail_inquiry_ajax.aspx`（`strTargetField=COUNTY`）
3. 解析 HTML 表格 `table.font16`，取門市編號 / 名稱 / 地址

**全家** — `http://api.map.com.tw`（圖資廠商，非 family.com.tw 本身）
1. GET `https://www.family.com.tw/Marketing/storemap/`，regex 取出 `getAPI.asp?v=1&key=<KEY>` 的金鑰
2. GET `/net/familyShop.aspx?l=10&searchType=ShowStore&type=&vLeft=...&key=<KEY>`
3. 以經緯度框選而非縣市迴圈，一次回傳全部門市
4. 回應是包在小括號裡的 UTF-8 JSON `([{...}])`，欄位 `pkey` / `NAME` / `addr`

**萊爾富** — `https://www.hilife.com.tw`
1. GET `/webapi/api/AntiForgery/GetAntiForgeryToken` 取 token（cookie 與 header 兩者缺一不可）
2. POST `/webapi/api/ShopServices/GetShopServices`，body 必須帶齊
   `{City_Id, Town_Id, Shop_Id, Services, Shop_Name}` 五個鍵（只送 `{}` 會回 0 筆）
3. 一次回傳全部門市；回應欄位 `shop_id` / `shop_name` / `shop_adr`

**OK超商** — `https://www.okmart.com.tw`
1. GET `/convenient_shopSearch_Result.aspx`，查詢參數全留空即取得全部門市
2. `/convenient_shopSearch_Result_mini.aspx` 為 OK mini 清單，一併併入
3. 回應是 HTML 片段；店號在 `showshop('0005', ...)` 的第一個參數，店名在 `<h2>`、地址在 `<span>`

## 輸出格式

四家格式一致，key 為門市編號字串：

```json
{
  "110817": { "store": "千翔", "address": "台北市中正區許昌街17號1樓" }
}
```

## 主要依賴

- `httpx` — HTTP 客戶端
- `beautifulsoup4` — HTML 解析

## 注意事項

- 四家用的都是非公開 API，程式內未內建速率限制，請勿密集呼叫
- **全家的 `l=10` 參數必填**，省略會回傳空陣列 `([])`；`searchType=ShopList`
  那組 city/area 參數已失效一律回空，不要改寫成縣市迴圈
- 全家 bbox 的 `vLeft` 必須是 118.0，用 119.0 會漏掉 14 間金門門市
- `api.map.com.tw` 的 https 無法連線（TLS 交握失敗），只能用 http；
  且必須帶 `family.com.tw` 的 Referer，否則回空白 HTML
- 各家原始資料的全形使用差異極大（全家 99% 全形、OK 25%、7-11 幾乎全半形），
  `store_io.normalize()` 在輸出前統一轉半形，四支爬蟲都經過它所以不會漏
- **萊爾富有 Akamai WAF**：短時間內約十幾次請求就會整站 403 封鎖數小時。
  其 API 一次就能取回全部門市，絕對不要改寫成逐縣市迴圈，也不要反覆重試
- 萊爾富原始 `shop_adr` 帶 3 碼郵遞區號前綴，爬蟲已移除以對齊其他品牌
- 萊爾富約 164 筆門市名稱含 `(暫歇中)`，資料刻意保留原樣，過濾交由下游決定
- 萊爾富僅在 17 個縣市設點（無花蓮、台東、澎湖、金門、連江）
- 所有 `stores*.json` 有提交至 git，作為下游使用的快取資料集
- GitHub Action 每日自動更新，各爬蟲步驟設 `continue-on-error`，
  單一超商網站故障不會中斷其他品牌的更新；最後有「回報爬蟲失敗」步驟，
  排在提交之後，確保資料照常更新的同時失敗仍會讓 workflow 顯示紅燈
