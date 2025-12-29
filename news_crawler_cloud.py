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

# --- 1. 基礎設定 ---
st.set_page_config(page_title="綠能新聞發佈系統", page_icon="⚡", layout="wide")

if 'edited_df' not in st.session_state:
    st.session_state.edited_df = pd.DataFrame()

# --- 2. 發信核心函式 (封裝分開寄送邏輯) ---
def build_html_body(title_text, df):
    """建立符合您格式要求的 HTML 表格"""
    intro = f"""
    {title_text}<br>
    <p style="color:gray; font-style:italic;">
    (抓取包含 <a href="https://docs.google.com/spreadsheets/d/1b2UEnsJ0hASkqpR3n9VgfLoIkTRgrHtm8aYbzRho5BA/edit?gid=235006464#gid=235006464">特定關鍵字</a> 
    的新聞，如果需要增加新聞網站或關鍵字請聯繫JP)</p>
    """
    
    html_rows = ""
    for _, row in df.iterrows():
        # 日期處理：只留月/日
        try:
            date_str = datetime.strptime(row['日期'], "%Y-%m-%d").strftime("%m/%d")
        except:
            date_str = row['日期']
            
        html_rows += f"""
        <tr>
            <td style='border:1px solid #333; padding:8px;'>{date_str}</td>
            <td style='border:1px solid #333; padding:8px;'><a href='{row['網址']}'>{row['標題']}</a></td>
            <td style='border:1px solid #333; padding:8px;'>{row.get('公司關鍵字', '-')}</td>
            <td style='border:1px solid #333; padding:8px;'>{row['AI 新聞摘要']}</td>
        </tr>"""
    
    table_head = """
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; font-size: 14px; border: 1px solid #333;">
        <thead><tr style="background-color: #f2f2f2; text-align: left;">
            <th style="width:5%;">日期</th><th style="width:25%;">標題</th><th style="width:10%;">公司</th><th style="width:60%;">AI摘要</th>
        </tr></thead><tbody>
    """
    return f"<html><body>{intro}{table_head}{html_rows}</tbody></table></body></html>"

def send_split_emails(df):
    sender = st.secrets["EMAIL_SENDER"]
    password = st.secrets["EMAIL_PASSWORD"]
    receiver = st.secrets["EMAIL_RECEIVER"]
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 分群邏輯：公司關鍵字欄位有值且不為 "-"
    group_a = df[df['公司關鍵字'].str.strip().replace("-", "") != ""]
    group_b = df[df['公司關鍵字'].str.strip().replace("-", "") == ""]

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            
            # 發送 Group A: 競業新聞
            if not group_a.empty:
                msg_a = MIMEMultipart()
                msg_a['Subject'] = f"{today} 競業新聞整理"
                msg_a['From'] = f"新聞機器人 <{sender}>"
                msg_a['To'] = receiver
                body_a = build_html_body("本日競業新聞整理如下：", group_a)
                msg_a.attach(MIMEText(body_a, 'html'))
                server.send_message(msg_a)
                st.write("✅ 競業新聞信件已發出")

            # 發送 Group B: 產業新聞
            if not group_b.empty:
                msg_b = MIMEMultipart()
                msg_b['Subject'] = f"{today} 產業新聞整理"
                msg_b['From'] = f"新聞機器人 <{sender}>"
                msg_b['To'] = receiver
                body_b = build_html_body("本日產業新聞整理如下：", group_b)
                msg_b.attach(MIMEText(body_b, 'html'))
                server.send_message(msg_b)
                st.write("✅ 產業新聞信件已發出")
        return True
    except Exception as e:
        st.error(f"發信出錯: {e}")
        return False

# --- 3. 側邊欄 ---
with st.sidebar:
    st.title("⚡ 綠能發佈系統")
    
    st.header("1️⃣ 抓取新聞資料")
    today_dt = pd.Timestamp.now().normalize()
    last_bus_day = (today_dt - BusinessDay(1)).to_pydatetime()
    s_date = st.date_input("開始日期", last_bus_day)
    e_date = st.date_input("結束日期", today_dt)
    
    if st.button("🚀 執行爬蟲", use_container_width=True):
        with st.spinner("執行原始爬蟲邏輯中..."):
            # ... (此處填入您原始的爬蟲 list 與關鍵字清單) ...
            # ... (產出的 df 需包含 '公司關鍵字' 欄位) ...
            st.success("抓取完成")

    st.divider()

    st.header("2️⃣ 產生摘要")
    if st.button("🤖 產生摘要", use_container_width=True):
        # ... (OpenAI 摘要邏輯) ...
        st.rerun()

    st.divider()

    st.header("3️⃣ 正式發信")
    if st.button("📧 分開發送電子報", use_container_width=True):
        if not st.session_state.edited_df.empty:
            if send_split_emails(st.session_state.edited_df):
                st.balloons()
                st.success("發信程序完成！")
        else:
            st.warning("畫面上無資料可發送")

# --- 4. 主畫面 ---
st.write("### 📝 編輯發佈清單")
if not st.session_state.edited_df.empty:
    st.session_state.edited_df = st.data_editor(
        st.session_state.edited_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "日期": st.column_config.TextColumn("日期", disabled=True),
            "標題": st.column_config.TextColumn("標題", width="large"),
            "網址": st.column_config.LinkColumn("原文連結", display_text="(查看)", width="small"),
            "公司關鍵字": st.column_config.TextColumn("公司關鍵字", width="medium"),
            "AI 新聞摘要": st.column_config.TextColumn("AI 新聞摘要", width="large")
        },
        column_order=["日期", "來源", "標題", "網址", "公司關鍵字", "AI 新聞摘要"]
    )
else:
    st.info("👈 請先從左側抓取新聞。")
