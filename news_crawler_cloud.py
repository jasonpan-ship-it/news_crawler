import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# --- 1. 初始化設定 ---
st.set_page_config(page_title="綠能新聞系統", page_icon="⚡", layout="wide")

if 'edited_df' not in st.session_state:
    st.session_state.edited_df = pd.DataFrame()

# --- 2. 發信函式 (Python 原生實作) ---
def send_python_email(df):
    sender = st.secrets["EMAIL_SENDER"]
    password = st.secrets["EMAIL_PASSWORD"]
    receiver = st.secrets["EMAIL_RECEIVER"]
    
    msg = MIMEMultipart()
    today = datetime.now().strftime("%Y-%m-%d")
    msg['Subject'] = f"【{today}】綠能產業新聞整理"
    msg['From'] = f"新聞機器人 <{sender}>"
    msg['To'] = receiver

    # 建立 HTML 表格內容
    html_rows = ""
    for _, row in df.iterrows():
        html_rows += f"""
        <tr>
            <td style='border:1px solid #ddd; padding:8px;'>{row['日期']}</td>
            <td style='border:1px solid #ddd; padding:8px;'><a href='{row['新聞網址']}'>{row['標題']}</a></td>
            <td style='border:1px solid #ddd; padding:8px;'>{row['AI 新聞摘要']}</td>
        </tr>
        """
    
    html_body = f"""
    <html>
    <body>
        <h2>今日新聞摘要</h2>
        <table style='border-collapse: collapse; width: 100%; font-family: sans-serif;'>
            <thead style='background-color: #f2f2f2;'>
                <tr>
                    <th style='border:1px solid #ddd; padding:8px;'>日期</th>
                    <th style='border:1px solid #ddd; padding:8px;'>標題 (點擊開啟)</th>
                    <th style='border:1px solid #ddd; padding:8px;'>AI 摘要</th>
                </tr>
            </thead>
            <tbody>{html_rows}</tbody>
        </table>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(html_body, 'html'))
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"郵件發送失敗: {e}")
        return False

# --- 3. 側邊欄工作流 ---
with st.sidebar:
    st.title("⚡ 綠能發佈系統")
    
    st.header("1️⃣ 抓取新聞")
    # (此處保留你原本運作正常的爬蟲 logic，執行後將結果存入 st.session_state.edited_df)
    if st.button("🚀 開始爬蟲", use_container_width=True):
        # 範例資料結構
        test_data = {
            "日期": ["2025-12-29", "2025-12-29"],
            "標題": ["聚陽雙軸轉型 深化ESG佈局", "位速揪伴攻太陽能"],
            "新聞網址": ["https://tw.news.yahoo.com/...", "https://udn.com/..."],
            "AI 新聞摘要": ["", ""]
        }
        st.session_state.edited_df = pd.DataFrame(test_data)
        st.success("抓取完成！")

    st.divider()

    st.header("2️⃣ 產生摘要")
    if st.button("🤖 產生 AI 摘要", use_container_width=True):
        if not st.session_state.edited_df.empty:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            for idx, row in st.session_state.edited_df.iterrows():
                if not row['AI 新聞摘要']:
                    # 此處呼叫你原本的 OpenAI 摘要邏輯
                    st.session_state.edited_df.at[idx, 'AI 新聞摘要'] = "AI 生成的測試摘要內容..."
            st.rerun()

    st.divider()

    st.header("3️⃣ 發送信件")
    if st.button("📧 依照畫面結果發信", use_container_width=True):
        if send_python_email(st.session_state.edited_df):
            st.balloons()
            st.success("✅ 郵件已成功送達！")

# --- 4. 主畫面：互動式編輯器 ---
st.write("### 📝 編輯發佈清單 (可直接點擊標題開啟網頁)")

if not st.session_state.edited_df.empty:
    # 設定標題為超連結，並隱藏原始網址欄位以保持整潔
    edited_df = st.data_editor(
        st.session_state.edited_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "標題": st.column_config.LinkColumn("標題 (點選跳轉)", help="點擊標題直接開啟新聞", validate="^http", 
                                             display_text="點我查看", # 或是直接顯示標題
                                             width="large"),
            "新聞網址": None, # 隱藏原始網址欄位
            "AI 新聞摘要": st.column_config.TextColumn("AI 新聞摘要", width="large")
        }
    )
    # 若要讓「標題」點下去就是原本的網址，可以這樣處理：
    # 這裡的標題會變成藍色底線的超連結
    st.session_state.edited_df = edited_df
else:
    st.info("👈 請點擊左側按鈕抓取今日新聞。")
