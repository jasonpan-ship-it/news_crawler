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

# --- 1. 初始化與介面設定 ---
st.set_page_config(page_title="綠能新聞發佈系統", page_icon="⚡", layout="wide")

if 'edited_df' not in st.session_state:
    st.session_state.edited_df = pd.DataFrame()

# --- 2. 發信函式 ---
def send_python_email(df):
    try:
        sender = st.secrets["EMAIL_SENDER"]
        password = st.secrets["EMAIL_PASSWORD"]
        receiver = st.secrets["EMAIL_RECEIVER"]
        
        msg = MIMEMultipart()
        msg['Subject'] = f"【{datetime.now().strftime('%m/%d')}】綠能產業新聞整理"
        msg['From'] = f"新聞機器人 <{sender}>"
        msg['To'] = receiver

        html_rows = ""
        for _, row in df.iterrows():
            html_rows += f"""
            <tr>
                <td style='border:1px solid #ddd; padding:8px;'>{row['日期']}</td>
                <td style='border:1px solid #ddd; padding:8px;'><a href='{row['網址']}'>{row['標題']}</a></td>
                <td style='border:1px solid #ddd; padding:8px;'>{row['AI 新聞摘要']}</td>
            </tr>"""
        
        html_body = f"<html><body><h3>今日新聞整理</h3><table border='1' style='border-collapse:collapse; width:100%;'><thead><tr style='background-color:#f2f2f2;'><th>日期</th><th>標題</th><th>摘要</th></tr></thead><tbody>{html_rows}</tbody></table></body></html>"
        msg.attach(MIMEText(html_body, 'html'))
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"郵件發送失敗: {e}")
        return False

# --- 3. 側邊欄：執行步驟 ---
with st.sidebar:
    st.title("⚡ 綠能發佈系統")
    
    st.header("1️⃣ 抓取新聞資料")
    today_dt = pd.Timestamp.now().normalize()
    last_bus_day = (today_dt - BusinessDay(1)).to_pydatetime()
    s_date = st.date_input("開始日期", last_bus_day)
    e_date = st.date_input("結束日期", today_dt)
    
    if st.button("🚀 執行爬蟲", use_container_width=True):
        with st.spinner("正在執行爬蟲..."):
            # --- 這裡放入你 news_competitor.py 的完整清單與爬蟲 logic ---
            start_date_obj = datetime.combine(s_date, datetime.min.time())
            end_date_obj = datetime.combine(e_date, datetime.max.time())
            
            # (以下省略重複的關鍵字清單，請務必保留你原始碼中的 keywords, company_keywords, title_keywords)
            # ...
            
            # 爬取結束後，將結果存入 st.session_state.edited_df
            # 確保欄位包含: ["日期", "來源", "標題", "網址", "AI 新聞摘要"]
            st.success("抓取完成！")

    st.divider()
    st.header("2️⃣ AI 自動摘要")
    if st.button("🤖 產生摘要", use_container_width=True):
        if not st.session_state.edited_df.empty:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            # 執行摘要邏輯...
            st.rerun()

    st.divider()
    st.header("3️⃣ 正式發信")
    if st.button("📧 發信", use_container_width=True):
        if send_python_email(st.session_state.edited_df):
            st.balloons()
            st.success("郵件發送成功！")

# --- 4. 主畫面：編輯區域 ---
st.write("### 📝 編輯發佈清單")
st.caption("提示：點擊「(查看)」可跳轉原文；選取行並按 Delete 可刪除。")

if not st.session_state.edited_df.empty:
    # 使用 st.data_editor 並配置 LinkColumn 展示為 "(查看)"
    st.session_state.edited_df = st.data_editor(
        st.session_state.edited_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "日期": st.column_config.TextColumn("日期", disabled=True),
            "來源": st.column_config.TextColumn("來源", disabled=True),
            "標題": st.column_config.TextColumn("標題", width="large"),
            "網址": st.column_config.LinkColumn(
                "原文連結", 
                display_text="(查看)", # 關鍵設定：將長網址隱藏，顯示為 (查看)
                width="small"
            ),
            "AI 新聞摘要": st.column_config.TextColumn("AI 新聞摘要", width="large")
        },
        column_order=["日期", "來源", "標題", "網址", "AI 新聞摘要"]
    )
else:
    st.info("👈 請先選擇日期並執行步驟一。")
