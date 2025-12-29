import streamlit as st
import pandas as pd
import datetime as dt
from datetime import datetime
import pygsheets
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import time as tt
import json
import gspread
from google.oauth2.service_account import Credentials
from openai import OpenAI
from pandas.tseries.offsets import BusinessDay

# --- 1. 基礎設定與關鍵字 ---
st.set_page_config(page_title="綠能新聞系統", page_icon="⚡", layout="wide")

KEYWORDS = ["太陽能", "再生能源", "電廠", "綠電", "光電", "風電", "儲能", "綠電交易", "麗升能源", "綠能"]
COMPANY_KEYWORDS = ["麗升", "雲豹能源", "泓德能源", "森崴能源", "進金生", "開陽電力", "星星電力", "中租電力", "元晶", "友達電力"]
TITLE_KEYWORDS = ["光電", "綠能", "綠電", "太陽能", "再生", "儲能", "減碳", "ESG", "發電", "漁電", "光儲", "電價"]

# --- 2. 工具函式 ---
def get_pygsheets_wks():
    service_account_info = json.loads(st.secrets["gcp_service_account"])
    gc = pygsheets.authorize(service_account_json=json.dumps(service_account_info))
    sh = gc.open_by_url('https://docs.google.com/spreadsheets/d/1b2UEnsJ0hASkqpR3n9VgfLoIkTRgrHtm8aYbzRho5BA')
    return sh.worksheet_by_title('最新新聞')

def get_gspread_wks():
    service_account_info = json.loads(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(service_account_info, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    gc = gspread.authorize(creds)
    return gc.open_by_key("1b2UEnsJ0hASkqpR3n9VgfLoIkTRgrHtm8aYbzRho5BA").worksheet("最新新聞")

def extract_webpage_text(url):
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
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
        with st.spinner("正在爬取媒體資料..."):
            start_dt = datetime.combine(s_date, datetime.min.time())
            end_dt = datetime.combine(e_date, datetime.max.time())
            
            data_list = []
            
            # --- 爬蟲實作 (Yahoo) ---
            for kw in KEYWORDS:
                url = f"https://tw.news.yahoo.com/search?p={quote(kw)}"
                try:
                    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
                    soup = BeautifulSoup(res.text, "html.parser")
                    for art in soup.select("li div[class*='Cf']"):
                        a = art.find("a")
                        m = art.find("div", class_="C(#959595)")
                        if not a or not m: continue
                        
                        title = a.text.strip()
                        link = a["href"] if a["href"].startswith("http") else f"https://tw.news.yahoo.com{a['href']}"
                        
                        # 日期處理
                        t_str = m.text.strip().split("•")[-1].strip()
                        d_obj = datetime.now()
                        if "天前" in t_str: d_obj -= dt.timedelta(days=int(t_str.replace("天前","")))
                        elif "小時" in t_str or "分鐘" in t_str: pass
                        else:
                            try:
                                clean_d = t_str.replace("年","-").replace("月","-").replace("日","").strip()
                                d_obj = datetime.strptime(clean_d.split()[0], "%Y-%m-%d")
                            except: continue
                        
                        if start_dt <= d_obj <= end_dt:
                            m_title = [k for k in TITLE_KEYWORDS if k in title]
                            if m_title:
                                m_comp = [k for k in COMPANY_KEYWORDS if k in title]
                                data_list.append([d_obj.strftime("%Y-%m-%d"), "Yahoo", kw, title, link, ", ".join(m_title), ", ".join(m_comp)])
                except: continue

            # --- 轉為 DataFrame 並寫入 ---
            if data_list:
                df = pd.DataFrame(data_list, columns=["日期", "來源", "分類", "標題", "新聞網址", "包含標題關鍵字", "包含公司關鍵字"])
                df["AI 新聞摘要"] = ""
                df = df.drop_duplicates(subset=["標題"])
                
                wks = get_pygsheets_wks()
                wks.clear(start='A1')
                wks.set_dataframe(df, 'A1')
                st.success(f"步驟一完成！抓取到 {len(df)} 筆。")
            else:
                st.error("找不到符合日期與關鍵字的新聞。")

    st.divider()
    st.header("2️⃣ 人工審核文章")
    st.link_button("📂 開啟 Sheets 刪減", "https://docs.google.com/spreadsheets/d/1b2UEnsJ0hASkqpR3n9VgfLoIkTRgrHtm8aYbzRho5BA/edit", use_container_width=True)

    st.divider()
    st.header("3️⃣ AI 自動摘要")
    if st.button("🤖 執行 OpenAI 摘要", use_container_width=True):
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        sheet = get_gspread_wks()
        rows = sheet.get_all_values()
        for idx, row in enumerate(rows[1:], start=2):
            url, summary = row[4], row[7] if len(row) > 7 else ""
            if url.strip() and not summary.strip():
                st.write(f"摘要中: {url[:30]}...")
                text = extract_webpage_text(url)
                if text:
                    res = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": f"請以繁體中文摘要約40字：\n\n{text[:2000]}"}]
                    )
                    sheet.update_cell(idx, 8, res.choices[0].message.content.strip())
        st.success("步驟三完成！")

    st.divider()
    st.header("4️⃣ 正式發信")
    if st.button("📧 發送電子報", use_container_width=True):
        key = st.secrets.get("GAS_API_KEY", "")
        gas_url = f"https://script.google.com/macros/s/AKfycbwdJ3IukgLTY0MRVrmGiwRvw9OVW5CeSKaP98VrQsz5cG_1CE4ZAyLNODv3H_AU2n8h/exec?key={key}"
        if requests.get(gas_url).status_code == 200:
            st.balloons()
            st.success("郵件發送成功！")

# --- 主畫面 ---
st.write("### 📄 目前 Sheets 中的新聞預覽")
try:
    wks = get_pygsheets_wks()
    st.dataframe(wks.get_as_df(), use_container_width=True)
except:
    st.info("尚未連線到 Sheets。")
