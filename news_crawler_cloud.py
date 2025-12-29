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
from urllib.parse import quote
import json

# --- 1. 初始化設定 ---
st.set_page_config(page_title="綠能新聞發佈系統", page_icon="⚡", layout="wide")

# 初始化 session_state，確保編輯結果不會因為網頁刷新消失
if 'edited_df' not in st.session_state:
    st.session_state.edited_df = pd.DataFrame()

# 關鍵字與公司清單 (節錄自你的原代碼)
KEYWORDS = ["太陽能", "再生能源", "電廠", "綠電", "光電", "風電", "儲能", "綠電交易", "麗升能源", "綠能"]
TITLE_KEYWORDS = ["光電", "綠能", "綠電", "太陽能", "再生", "儲能", "發電", "風電"]
COMPANY_KEYWORDS = ["麗升", "雲豹能源", "泓德能源", "森崴能源", "台汽電", "進金生", "元晶", "友達"]

# --- 2. 工具函式：Python 發信 ---
def send_python_email(df):
    try:
        sender = st.secrets["EMAIL_SENDER"]
        password = st.secrets["EMAIL_PASSWORD"]
        receiver = st.secrets["EMAIL_RECEIVER"]
        
        msg = MIMEMultipart()
        msg['Subject'] = f"【{datetime.now().strftime('%Y-%m-%d')}】綠能產業新聞整理"
        msg['From'] = f"新聞機器人 <{sender}>"
        msg['To'] = receiver

        # 建立 HTML 表格，並將標題封裝成超連結
        html_rows = ""
        for _, row in df.iterrows():
            html_rows += f"""
            <tr>
                <td style='border:1px solid #ddd; padding:8px;'>{row['日期']}</td>
                <td style='border:1px solid #ddd; padding:8px;'><a href='{row['新聞網址']}'>{row['標題']}</a></td>
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

# --- 3. 側邊欄控制流程 ---
with st.sidebar:
    st.title("⚡ 綠能發佈系統")
    
    st.header("1️⃣ 抓取新聞資料")
    today_dt = pd.Timestamp.now().normalize()
    last_bus_day = (today_dt - BusinessDay(1)).to_pydatetime()
    s_date = st.date_input("開始日期", last_bus_day)
    e_date = st.date_input("結束日期", today_dt)
    
    if st.button("🚀 執行爬蟲", use_container_width=True):
        with st.spinner("各家媒體爬取中..."):
            start_date_obj = datetime.combine(s_date, datetime.min.time())
            end_date_obj = datetime.combine(e_date, datetime.max.time())
            
            # --- 核心爬蟲迴圈 (移植自你的 news_competitor.py) ---
            all_data = []
            headers = {"User-Agent": "Mozilla/5.0"}
            
            for kw in KEYWORDS:
                # 以 Yahoo 為例示範完整抓取邏輯
                url = f"https://tw.news.yahoo.com/search?p={quote(kw)}"
                try:
                    res = requests.get(url, headers=headers, timeout=10)
                    soup = BeautifulSoup(res.text, "html.parser")
                    for art in soup.select("li div[class*='Cf']"):
                        a_tag = art.find("a")
                        meta_div = art.find("div", class_="C(#959595)")
                        if not a_tag or not meta_div: continue
                        
                        title = a_tag.text.strip()
                        link = a_tag["href"] if a_tag["href"].startswith("http") else f"https://tw.news.yahoo.com{a_tag['href']}"
                        
                        # 日期處理 (修正抓不到問題)
                        time_str = meta_div.text.strip().split("•")[-1].strip()
                        d_obj = datetime.now()
                        if "天前" in time_str: d_obj -= dt.timedelta(days=int(time_str.replace("天前","")))
                        elif "年" in time_str: d_obj = datetime.strptime(time_str.replace("年","-").replace("月","-").replace("日","").split()[0], "%Y-%m-%d")
                        
                        if start_date_obj <= d_obj <= end_date_obj:
                            m_title = [k for k in TITLE_KEYWORDS if k in title]
                            if m_title:
                                m_comp = [k for k in COMPANY_KEYWORDS if k in title]
                                all_data.append({
                                    "日期": d_obj.strftime("%Y-%m-%d"),
                                    "來源": "Yahoo",
                                    "標題": title,
                                    "新聞網址": link,
                                    "包含公司關鍵字": ", ".join(m_comp) if m_comp else "-",
                                    "AI 新聞摘要": ""
                                })
                except: continue
            
            if all_data:
                st.session_state.edited_df = pd.DataFrame(all_data).drop_duplicates(subset=["標題"])
                st.success(f"抓取完成！共 {len(st.session_state.edited_df)} 筆。")
            else:
                st.error("此日期範圍內查無新聞，請嘗試擴大開始日期。")

    st.divider()
    st.header("2️⃣ AI 自動摘要")
    if st.button("🤖 產生畫面上摘要", use_container_width=True):
        if not st.session_state.edited_df.empty:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            for idx, row in st.session_state.edited_df.iterrows():
                if not row['AI 新聞摘要']:
                    st.write(f"正在摘要: {row['標題'][:15]}...")
                    # 此處呼叫你原本的摘要邏輯 summarize_text(row['新聞網址'])
                    st.session_state.edited_df.at[idx, 'AI 新聞摘要'] = "AI 摘要內容..."
            st.success("摘要生成完畢！")
            st.rerun()

    st.divider()
    st.header("3️⃣ 正式發信")
    if st.button("📧 依照目前畫面發信", use_container_width=True):
        if send_python_email(st.session_state.edited_df):
            st.balloons()
            st.success("郵件已發送！")

# --- 4. 主畫面：互動編輯器 ---
st.write("### 📝 編輯發佈清單")
st.caption("提示：點擊「標題連結」可開啟網頁；選取行並按 Delete 可刪除。")

if not st.session_state.edited_df.empty:
    # 這裡實作標題點擊跳轉
    display_df = st.session_state.edited_df.copy()
    
    edited_result = st.data_editor(
        display_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "標題": st.column_config.TextColumn("標題", width="large"),
            "新聞網址": st.column_config.LinkColumn("標題連結", help="點擊開啟新聞網頁", width="medium"),
            "AI 新聞摘要": st.column_config.TextColumn("AI 新聞摘要", width="large"),
            "日期": st.column_config.TextColumn("日期", disabled=True),
        },
        column_order=["日期", "來源", "標題", "包含公司關鍵字", "AI 新聞摘要", "新聞網址"]
    )
    # 保存編輯後的結果回到 session_state
    st.session_state.edited_df = edited_result
else:
    st.info("👈 請先從左側選擇日期並執行步驟一。")
