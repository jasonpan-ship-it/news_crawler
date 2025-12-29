import streamlit as st
import pandas as pd
import datetime as dt
from datetime import datetime
import pygsheets
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import urllib.request as req
import time as tt
import json

# --- 1. 網頁介面設定 ---
st.set_page_config(page_title="新聞監測系統", page_icon="📰")
st.title("📰 綠能產業新聞自動爬取")

# 側邊欄設定參數
st.sidebar.header("設定搜尋範圍")
start_date_input = st.sidebar.date_input("開始日期", datetime(2024, 12, 26))
end_date_input = st.sidebar.date_input("結束日期", datetime(2024, 12, 29))

# 將輸入轉為 datetime 格式（相容你原本的邏輯）
start_date = datetime.combine(start_date_input, datetime.min.time())
end_date = datetime.combine(end_date_input, datetime.max.time())

# --- 2. Google Sheets 連線設定 ---
# 這裡改用 st.secrets 讀取金鑰，不要放檔案路徑
def init_gsheet():
    try:
        # 在 Streamlit Cloud 的 Secrets 設定中貼上 JSON 內容
        service_account_info = json.loads(st.secrets["gcp_service_account"])
        gc = pygsheets.authorize(service_account_json=json.dumps(service_account_info))
        # 請確保這條網址是對的，或改成變數
        spreadsheet = gc.open_by_url('https://docs.google.com/spreadsheets/d/1b2UEnsJ0hASkqpR3n9VgfLoIkTRgrHtm8aYbzRho5BA')
        return spreadsheet.worksheet_by_title('最新新聞')
    except Exception as e:
        st.error(f"Google Sheets 連線失敗: {e}")
        return None

# --- 3. 爬蟲核心邏輯 (封裝成 function) ---
def run_crawler(start_date, end_date):
    # (此處保留你原本的 keywords, company_keywords, title_keywords 清單)
    keywords = ["太陽能", "再生能源", "電廠", "綠電", "光電", "風電", "儲能", "綠電交易", "麗升能源", "綠能"]
    # ... (其餘關鍵字清單省略，請照舊貼上) ...

    dates, sources, categories, company_matches, title_keyword_matches, titles, links = [], [], [], [], [], [], []

    def append_news(title, url, date_obj, source, category):
        if start_date <= date_obj <= end_date:
            # ... (原本的過濾邏輯) ...
            pass # 這裡請貼上你原本 append_news 內的程式碼

    progress_bar = st.progress(0)
    st.write("🔍 正在搜尋各家媒體...")

    # ... (這裡放你原本爬 Yahoo, UDN, MoneyDJ, 自由, ETtoday 的迴圈) ...
    # 記得在迴圈中加入 st.write(f"正在處理: {kw}") 讓使用者知道進度

    # 最後回傳 DataFrame
    final_df = pd.DataFrame({
        "日期": dates, "來源": sources, "分類": categories,
        "標題關鍵字": title_keyword_matches, "關聯公司": company_matches,
        "標題": titles, "網址": links, "AI 新聞摘要": [""] * len(titles)
    })
    return final_df

# --- 4. 網頁執行按鈕 ---
if st.button("🚀 開始執行爬蟲並上傳至 Google Sheets"):
    sheet = init_gsheet()
    if sheet:
        with st.spinner('爬蟲執行中，請稍候...'):
            df = run_crawler(start_date, end_date)
            
            if not df.empty:
                # 寫入 Google Sheet
                sheet.clear(start='A1')
                sheet.set_dataframe(df, 'A1')
                st.success(f"✅ 完成！成功抓取 {len(df)} 筆資料並已更新至 Google Sheets。")
                st.dataframe(df) # 網頁預覽
            else:
                st.warning("查無此日期範圍內的新聞。")