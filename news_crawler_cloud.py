import streamlit as st
import pandas as pd
import datetime as dt
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import quote
import urllib.request as req
import bs4
from pandas.tseries.offsets import BusinessDay
import warnings

# 忽略警告 (延用你的原設定)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# --- 1. 介面初始化 ---
st.set_page_config(page_title="綠能新聞發佈系統", page_icon="⚡", layout="wide")

# 初始化 session_state，確保網頁端編輯的資料不會消失
if 'edited_df' not in st.session_state:
    st.session_state.edited_df = pd.DataFrame()

# --- 2. 側邊欄：四步驟執行 ---
with st.sidebar:
    st.title("⚡ 綠能發佈系統")
    
    st.header("1️⃣ 抓取新聞資料")
    # 自動計算：前一個上班日
    today_dt = pd.Timestamp.now().normalize()
    last_bus_day = (today_dt - BusinessDay(1)).to_pydatetime()
    
    # 日期輸入框 (這會傳入你的爬蟲邏輯)
    start_date = st.date_input("開始日期", last_bus_day)
    end_date = st.date_input("結束日期", today_dt)
    
    if st.button("🚀 開始執行爬蟲", use_container_width=True):
        with st.spinner("正在執行爬蟲程式..."):
            # 將選擇的日期轉為 datetime 格式，對應你原程式碼的變數名稱
            start_date_obj = datetime.combine(start_date, datetime.min.time())
            end_date_obj = datetime.combine(end_date, datetime.max.time())
            
            # --- 💡 以下為你 news_competitor.py 的原始核心邏輯 (完全不更動) ---
            dates, sources, categories, company_matches, title_keyword_matches, titles, links = [], [], [], [], [], [], []
            keywords = ["太陽能", "再生能源", "電廠", "綠電", "光電",  "風電", "儲能", "綠電交易", "麗升能源", "綠能"]
            
            # (此處請貼入你原始碼中完整的 company_keywords 與 title_keywords 清單)
            company_keywords = ["麗升", "雲豹能源", "泓德能源", "森崴能源", "台汽電", "元晶", "友達"] # 簡化示意
            title_keywords = ["光電", "綠電", "太陽能", "再生", "儲能", "發電"] # 簡化示意
            
            def append_news(title, url, d_obj, source, category):
                if start_date_obj <= d_obj <= end_date_obj:
                    m_title = [k for k in title_keywords if k in title]
                    if not m_title: return
                    m_comp = [k for k in company_keywords if k in title]
                    dates.append(d_obj.strftime("%Y-%m-%d"))
                    sources.append(source)
                    categories.append(category)
                    title_keyword_matches.append(", ".join(m_title))
                    company_matches.append(", ".join(m_comp) if m_comp else "-")
                    titles.append(title)
                    links.append(url)

            # 執行你原有的各大媒體迴圈 (Yahoo, UDN, MoneyDJ, 自由, ETtoday)
            # ... [這裡會跑完你所有的爬蟲 Loop] ...
            
            # 🧾 最後組合成 DataFrame 並存入網頁緩存
            st.session_state.edited_df = pd.DataFrame({
                "日期": dates, "來源": sources, "分類": categories,
                "包含標題關鍵字": title_keyword_matches, "包含公司關鍵字": company_matches,
                "標題": titles, "網址": links, "AI 新聞摘要": [""] * len(titles)
            }).drop_duplicates(subset=["標題"]).sort_values(by="日期", ascending=False)
            
            st.success(f"步驟一完成！抓取到 {len(st.session_state.edited_df)} 筆新聞。")

    st.divider()
    st.header("2️⃣ AI 自動摘要")
    if st.button("🤖 執行 OpenAI 摘要", use_container_width=True):
        if not st.session_state.edited_df.empty:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            # 執行摘要邏輯，並直接更新 session_state
            st.success("步驟二完成！")
            st.rerun()

    st.divider()
    st.header("3️⃣ 正式發信")
    if st.button("📧 發送電子報", use_container_width=True):
        # 執行 Python SMTP 發信邏輯，發送畫面上目前編輯後的內容
        st.balloons()
        st.success("步驟三完成！")

# --- 3. 主畫面：網頁編輯區域 ---
st.write("### 📝 編輯發佈清單")
st.caption("提示：點擊「(查看)」可跳轉原文；選取行並按 Delete 可刪除。")

if not st.session_state.edited_df.empty:
    # 這裡實作網址顯示為 (查看) 的超連結形式
    st.session_state.edited_df = st.data_editor(
        st.session_state.edited_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "日期": st.column_config.TextColumn("日期", disabled=True),
            "標題": st.column_config.TextColumn("標題", width="large"),
            "網址": st.column_config.LinkColumn(
                "原文連結", 
                display_text="(查看)", # ✅ 這會讓長網址顯示為 (查看)
                width="small"
            ),
            "AI 新聞摘要": st.column_config.TextColumn("AI 新聞摘要", width="large")
        },
        column_order=["日期", "來源", "標題", "網址", "包含公司關鍵字", "AI 新聞摘要"]
    )
else:
    st.info("👈 請先從左側選擇日期並執行「步驟一」抓取新聞。")
