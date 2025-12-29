import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import datetime as dt
from pandas.tseries.offsets import BusinessDay

# --- 1. 初始化設定 ---
st.set_page_config(page_title="綠能新聞發佈系統", page_icon="⚡", layout="wide")

# 確保資料在換頁或按鈕點擊後能保留
if 'edited_df' not in st.session_state:
    st.session_state.edited_df = pd.DataFrame()

# --- 2. 發信函式 (使用 Python 原生 SMTP) ---
def send_python_email(df):
    try:
        sender = st.secrets["EMAIL_SENDER"]
        password = st.secrets["EMAIL_PASSWORD"]
        receiver = st.secrets["EMAIL_RECEIVER"]
        
        msg = MIMEMultipart()
        today = datetime.now().strftime("%Y-%m-%d")
        msg['Subject'] = f"【{today}】綠能產業新聞整理"
        msg['From'] = f"新聞機器人 <{sender}>"
        msg['To'] = receiver

        # 建立 HTML 表格 (這部分會發送到信箱)
        html_rows = ""
        for _, row in df.iterrows():
            html_rows += f"""
            <tr>
                <td style='border:1px solid #ddd; padding:8px;'>{row['日期']}</td>
                <td style='border:1px solid #ddd; padding:8px;'><a href='{row['新聞網址']}'>{row['標題']}</a></td>
                <td style='border:1px solid #ddd; padding:8px;'>{row.get('包含公司關鍵字', '-')}</td>
                <td style='border:1px solid #ddd; padding:8px;'>{row['AI 新聞摘要']}</td>
            </tr>
            """
        
        html_body = f"<html><body><h2>今日新聞摘要</h2><table border='1' style='border-collapse: collapse; width: 100%;'><thead><tr style='background-color: #f2f2f2;'><th>日期</th><th>標題</th><th>公司</th><th>AI 摘要</th></tr></thead><tbody>{html_rows}</tbody></table></body></html>"
        msg.attach(MIMEText(html_body, 'html'))
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"郵件發送失敗: {e}")
        return False

# --- 3. 側邊欄：四步驟導航 ---
with st.sidebar:
    st.title("⚡ 綠能發佈系統")
    
    # 步驟一：日期選擇與爬蟲 (確保選擇框永遠顯示)
    st.header("1️⃣ 抓取新聞資料")
    today_dt = pd.Timestamp.now().normalize()
    last_bus_day = (today_dt - BusinessDay(1)).to_pydatetime()
    
    # 日期輸入框放在這裡
    s_date = st.date_input("開始日期", last_bus_day)
    e_date = st.date_input("結束日期", today_dt)
    
    if st.button("🚀 執行爬蟲", use_container_width=True):
        with st.spinner("新聞爬取中..."):
            # 這裡呼叫你原本 news_competitor.py 的爬蟲函數
            # 假設爬取完得到的 DataFrame 叫 crawler_df
            # st.session_state.edited_df = crawler_df
            st.success("抓取完成！")

    st.divider()

    st.header("2️⃣ 人工審核")
    st.info("請在右側表格直接刪除不需要的新聞列。")

    st.divider()

    st.header("3️⃣ AI 自動摘要")
    if st.button("🤖 產生畫面上新聞摘要", use_container_width=True):
        if not st.session_state.edited_df.empty:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            # 針對畫面上現有的每一行抓取內容並摘要
            # (摘要邏輯實作於此...)
            st.success("AI 摘要生成完畢！")
            st.rerun()

    st.divider()

    st.header("4️⃣ 正式發信")
    if st.button("📧 依照畫面結果發信", use_container_width=True):
        if not st.session_state.edited_df.empty:
            if send_python_email(st.session_state.edited_df):
                st.balloons()
                st.success("✅ 郵件已發送！")
        else:
            st.error("畫面上沒有資料可以發送。")

# --- 4. 主畫面：編輯區域 ---
st.write("### 📝 編輯發佈清單")
st.caption("提示：點擊「標題」可直接跳轉新聞網頁；如需刪除，請選取該列並按鍵盤 Delete。")

if not st.session_state.edited_df.empty:
    # 這裡實作「標題即超連結」的展示方式
    # 我們讓標題欄位直接與新聞網址連動
    edited_df = st.data_editor(
        st.session_state.edited_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "標題": st.column_config.LinkColumn(
                "標題 (點擊查看)", 
                help="直接點擊標題即可開啟原始新聞網頁",
                # 這裡最關鍵：讓 LinkColumn 讀取標題文字，但實際跳轉到新聞網址欄位
                # 備註：Streamlit 目前 LinkColumn 需填入網址，我們維持展示標題與網址兩欄
                width="large"
            ),
            "新聞網址": st.column_config.LinkColumn("原始連結", width="small"),
            "AI 新聞摘要": st.column_config.TextColumn("AI 新聞摘要", width="large"),
            "日期": st.column_config.TextColumn("日期", disabled=True),
        },
        # 隱藏不需要直接編輯的技術欄位
        column_order=["日期", "來源", "標題
