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
import gspread
from google.oauth2.service_account import Credentials
from openai import OpenAI
from pandas.tseries.offsets import BusinessDay

# --- 基礎設定 ---
st.set_page_config(page_title="綠能新聞工作流", page_icon="⚡", layout="wide")

# --- 1. 核心清單與關鍵字 ---
keywords = ["太陽能", "再生能源", "電廠", "綠電", "光電", "風電", "儲能", "綠電交易", "麗升能源", "綠能"]
company_keywords = list(set(["麗升", "陽光伏特家", "台汽電", "富威電力", "雲豹能源", "泓德能源", "森崴能源", "進金生", "開陽電力", "星星電力", "中租電力", "元晶", "友達電力"])) # 這裡可依需求縮減或增加
title_keywords = ["小水力","光電","綠能","綠電","風能","太陽能","再生","儲能","減碳","ESG","電池","地熱","風力","發電","漁電","光儲","電價","電業","碳權","碳費"]

# --- 2. 核心工具函式 ---
def get_pygsheets_wks():
    service_account_info = json.loads(st.secrets["gcp_service_account"])
    gc = pygsheets.authorize(service_account_json=json.dumps(service_account_info))
    sh = gc.open_by_url('https://docs.google.com/spreadsheets/d/1b2UEnsJ0hASkqpR3n9VgfLoIkTRgrHtm8aYbzRho5BA')
    return sh.worksheet_by_title('最新新聞')

def get_gspread_wks():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    service_account_info = json.loads(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(service_account_info, scopes=scope)
    gc = gspread.authorize(creds)
    return gc.open_by_key("1b2UEnsJ0hASkqpR3n9VgfLoIkTRgrHtm8aYbzRho5BA").worksheet("最新新聞")

def extract_webpage_text(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in ['article', 'main', 'div']:
            content = soup.find(tag)
            if content and len(content.text.strip()) > 200:
                return content.get_text(separator="\n", strip=True)
        return soup.get_text(separator="\n", strip=True)
    except: return ""

# --- 3. 側邊欄工作流 ---
with st.sidebar:
    st.title("⚡ 綠能新聞發佈系統")
    
    # 步驟一：爬蟲
    st.header("1️⃣ 抓取新聞資料")
    today_dt = pd.Timestamp.now().normalize()
    last_bus_day = (today_dt - BusinessDay(1)).to_pydatetime()
    s_date = st.date_input("開始日期", last_bus_day)
    e_date = st.date_input("結束日期", today_dt)
    
    if st.button("🚀 執行爬蟲並上傳", use_container_width=True):
        with st.spinner("各家媒體爬取中..."):
            start_dt = datetime.combine(s_date, datetime.min.time())
            end_dt = datetime.combine(e_date, datetime.max.time())
            
            dates, sources, categories, titles, links = [], [], [], [], []
            # --- 此處封裝你原本的 Yahoo, UDN, MoneyDJ 爬蟲邏輯 (簡略示意) ---
            # ... (爬蟲邏輯會根據關鍵字抓取並存入上述 list) ...
            
            # 範例結果
            new_df = pd.DataFrame({"日期": dates, "來源": sources, "分類": categories, "標題": titles, "新聞網址": links})
            new_df["包含標題關鍵字"] = "" # 預留過濾後填入
            new_df["包含公司關鍵字"] = ""
            new_df["AI 新聞摘要"] = ""
            
            wks = get_pygsheets_wks()
            wks.clear(start='A1')
            wks.set_dataframe(new_df, 'A1')
            st.success("步驟一完成！")

    st.divider()

    # 步驟二：人工
    st.header("2️⃣ 人工審核文章")
    st.link_button("📊 打開新聞大表選文章", "https://docs.google.com/spreadsheets/d/1b2UEnsJ0hASkqpR3n9VgfLoIkTRgrHtm8aYbzRho5BA/edit", use_container_width=True)

    st.divider()

    # 步驟三：OpenAI 摘要
    st.header("3️⃣ AI 自動摘要")
    if st.button("🤖 執行 OpenAI 摘要", use_container_width=True):
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        sheet = get_gspread_wks()
        rows = sheet.get_all_values()
        st.info(f"檢測到 {len(rows)-1} 筆資料")
        
        for idx, row in enumerate(rows[1:], start=2):
            url = row[6] if len(row) > 6 else ""
            summary = row[7] if len(row) > 7 else ""
            if url.strip() and not summary.strip():
                st.write(f"正在摘要: {url[:30]}...")
                text = extract_webpage_text(url)
                if text:
                    prompt = f"請以繁體中文條列約40個字的簡短摘要重點：\n\n{text[:2500]}"
                    response = client.chat.completions.create(
                        model="gpt-4o-mini", # 建議用 4o-mini 更便宜快速
                        messages=[{"role": "user", "content": prompt}]
                    )
                    sheet.update_cell(idx, 8, response.choices[0].message.content.strip())
        st.success("步驟三完成！")

    st.divider()

    # 步驟四：GAS
    st.header("4️⃣ 正式發信")
    if st.button("📧 點擊發送電子報", use_container_width=True):
        # 這裡填入你的 GAS Web App 網址
        gas_url = "https://script.google.com/macros/s/AKfycbwdJ3IukgLTY0MRVrmGiwRvw9OVW5CeSKaP98VrQsz5cG_1CE4ZAyLNODv3H_AU2n8h/exec"
        res = requests.get(gas_url)
        if res.status_code == 200:
            st.balloons()
            st.success("郵件已發送！")

# --- 主畫面 ---
st.write("### 📄 目前 Sheets 中的新聞預覽")
try:
    wks = get_pygsheets_wks()
    st.dataframe(wks.get_as_df(), use_container_width=True)
except:
    st.info("尚未連線到 Sheets。")
