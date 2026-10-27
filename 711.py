import httpx
from bs4 import BeautifulSoup

from store_io import update_readme, write_outputs


def main():
    all_stores = {}

    with httpx.Client(base_url="https://www.ibon.com.tw") as client:
        # 取得城市列表
        res = client.get("/retail_inquiry.aspx")
        cities = [opt.text.strip() for opt in BeautifulSoup(res.text, "html.parser").select("#Class1 option")]
        
        print(f"正在處理 {len(cities)} 個城市...")

        for city in cities:
            print(f"處理城市: {city}")
            res = client.post("/retail_inquiry_ajax.aspx", data={"strTargetField": "COUNTY", "strKeyWords": city})

            # 只選擇 store_table 中的 tr，排除表頭和其他 tr
            table = BeautifulSoup(res.text, "html.parser").select_one("table.font16")
            if not table:
                print(f"  找不到表格，繼續下一個城市")
                continue
            print(f"  找到表格，有 {len(table.select('tr'))} 行")

            all_stores.update({
                cols[0].text.strip(): {
                    "store": cols[1].text.strip(),
                    "address": cols[2].text.strip()
                }
                for row in table.select("tr")
                if row.get("style") and (cols := row.select("td")) and len(cols) >= 3
            })
            print(f"  完成，已處理 {len([r for r in table.select('tr') if r.get('style')])} 筆店鋪")

    write_outputs(all_stores, "stores")
    update_readme("7-ELEVEN", len(all_stores))

if __name__ == "__main__":
    main()