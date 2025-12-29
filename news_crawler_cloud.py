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
import json

# 忽略警告
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# --- 1. 介面初始化 ---
st.set_page_config(page_title="綠能新聞發佈系統", page_icon="⚡", layout="wide")

# 初始化 session_state，確保編輯結果不會消失
if 'edited_df' not in st.session_state:
    st.session_state.edited_df = pd.DataFrame()

# --- 2. 工具函式 ---
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
    except:
        return ""

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
            # 發信時使用真正的網址連結
            target_url = row['網址']
            html_rows += f"""
            <tr>
                <td style='border:1px solid #ddd; padding:8px;'>{row['日期']}</td>
                <td style='border:1px solid #ddd; padding:8px;'><a href='{target_url}'>{row['標題']}</a></td>
                <td style='border:1px solid #ddd; padding:8px;'>{row.get('AI 新聞摘要', '')}</td>
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

# --- 3. 側邊欄 ---
with st.sidebar:
    st.title("⚡ 綠能發佈系統")
    
    st.header("1️⃣ 抓取新聞資料")
    today_dt = pd.Timestamp.now().normalize()
    last_bus_day = (today_dt - BusinessDay(1)).to_pydatetime()
    s_date = st.date_input("開始日期", last_bus_day)
    e_date = st.date_input("結束日期", today_dt)
    
    if st.button("🚀 執行爬蟲", use_container_width=True):
        with st.spinner("正在執行爬蟲程式..."):
            start_date_obj = datetime.combine(s_date, datetime.min.time())
            end_date_obj = datetime.combine(e_date, datetime.max.time())
            
            dates, sources, categories, titles, links = [], [], [], [], []
            keywords = ["太陽能", "再生能源", "電廠", "綠電", "光電",  "風電", "儲能", "綠電交易", "麗升能源", "綠能"]
            title_keywords = ["小水力","光電","綠能","綠電","風能","太陽能","再生","儲能","減碳","ESG","電池","地熱","風力","發電","魚塭","土地","水力","淨零","漁電","光儲","低地力","售電","台電","配電","輸電","升壓","環社","用電大戶","饋線","電表","表前","表後","需量反應","電網","土地開發","電廠","備轉","調頻","PCS","EMS","BMS","電力交易","併網","籌設","風電","電價","電業","香夾蘭","農業補助","CPPA","農電","農業設施許可","沼氣","生質能","Solar","PV","energy","solar","storage","光伏","能源政策","碳權","碳費","躉購","能源署","電業法","躉購費率","漁電共生"]

            def append_news(title, url, date_obj, source, category):
                if start_date_obj <= date_obj <= end_date_obj:
                    if any(k in title for k in title_keywords):
                        dates.append(date_obj.strftime("%Y-%m-%d"))
                        sources.append(source)
                        categories.append(category)
                        titles.append(title)
                        links.append(url)

            headers = {"User-Agent": "Mozilla/5.0"}
            for kw in keywords:
                try: # Yahoo 爬蟲
                    res = requests.get(f"https://tw.news.yahoo.com/search?p={quote(kw)}", headers=headers)
                    soup = BeautifulSoup(res.text, "html.parser")
                    for art in soup.select("li div[class*='Cf']"):
                        a = art.find("a")
                        m = art.find("div", class_="C(#959595)")
                        if a and m:
                            t, l = a.text.strip(), a["href"]
                            full_l = l if l.startswith("http") else f"https://tw.news.yahoo.com{l}"
                            t_str = m.text.strip().split("•")[-1].strip()
                            d_obj = datetime.now()
                            if "天前" in t_str: d_obj -= dt.timedelta(days=int(t_str.replace("天前","")))
                            elif "小時" in t_str or "分鐘" in t_str: pass
                            else:
                                try: d_obj = datetime.strptime(t_str.replace("早上","").replace("下午","").replace("年","-").replace("月","-").replace("日","").split()[0], "%Y-%m-%d")
                                except: continue
                            append_news(t, full_l, d_obj, "Yahoo", kw)
                except: continue
                try: # UDN 爬蟲
                    res = requests.get(f"https://udn.com/search/word/2/{quote(kw)}", headers=headers)
                    soup = BeautifulSoup(res.text, "html.parser")
                    ti_box = soup.find("div", class_="context-box__content story-list__holder story-list__holder--full")
                    if ti_box:
                        ti_h2 = ti_box.find_all("h2")
                        ti_time = ti_box.find_all("time", class_="story-list__time")
                        for idx, h2 in enumerate(ti_h2):
                            a = h2.find("a")
                            if a and idx < len(ti_time):
                                try:
                                    d_obj = datetime.strptime(ti_time[idx].text.strip()[:10], "%Y-%m-%d")
                                    append_news(a.text.strip(), a["href"], d_obj, "UDN", kw)
                                except: continue
                except: continue

            if titles:
                df = pd.DataFrame({
                    "日期": dates, "來源": sources, "分類": categories,
                    "標題": titles, "網址": links, "AI 新聞摘要": ""
                }).drop_duplicates(subset=["標題"]).sort_values(by="日期", ascending=False)
                
                # --- 強制將顯示欄位改成 "(查看)" ---
                df["原文連結"] = df["網址"] # 複製一份原始網址供 LinkColumn 使用
                st.session_state.edited_df = df
                st.success(f"✅ 抓取完成！共 {len(df)} 筆新聞。")
            else:
                st.error("❌ 此日期範圍內查無新聞。")

    st.divider()

    # 步驟二：產生摘要
    st.header("2️⃣ 產生摘要")
    if st.button("🤖 產生摘要", use_container_width=True):
        if not st.session_state.edited_df.empty:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            for idx, row in st.session_state.edited_df.iterrows():
                if not row['AI 新聞摘要']:
                    st.write(f"正在摘要: {row['標題'][:15]}...")
                    text = extract_webpage_text(row['網址'])
                    if text:
                        res = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role": "user", "content": f"請以繁體中文摘要約40個字：\n\n{text[:2500]}"}]
                        )
                        st.session_state.edited_df.at[idx, 'AI 新聞摘要'] = res.choices[0].message.content.strip()
            st.rerun()

    st.divider()

    # 步驟三：正式發信
    st.header("3️⃣ 正式發信")
    if st.button("📧 發送電子報", use_container_width=True):
        if not st.session_state.edited_df.empty:
            if send_python_email(st.session_state.edited_df):
                st.balloons()
                st.success("✅ 郵件發送成功！")
        else:
            st.warning("⚠️ 畫面上沒有資料。")

# --- 4. 主畫面 ---
st.write("### 📝 編輯發佈清單")
st.caption("提示：點擊「(查看)」可跳轉原文；選取行並按 Delete 可刪除。")

if not st.session_state.edited_df.empty:
    # 這裡我們採取最保險的做法：
    # 使用一欄隱藏的原始網址來驅動 LinkColumn 的點擊行為，
    # 並且強制讓顯示文字為 "(查看)"。
    st.session_state.edited_df = st.data_editor(
        st.session_state.edited_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "日期": st.column_config.TextColumn("日期", disabled=True),
            "來源": st.column_config.TextColumn("來源", disabled=True),
            "標題": st.column_config.TextColumn("標題", width="large"),
            "原文連結": st.column_config.LinkColumn(
                "原文連結",
                display_text="(查看)", # 再次明確指定
                width="small"
            ),
            "網址": None, # 徹底隱藏原始網址欄位，不讓它出現在畫面上
            "AI 新聞摘要": st.column_config.TextColumn("AI 新聞摘要", width="large")
        },
        column_order=["日期", "來源", "標題", "原文連結", "AI 新聞摘要"]
    )
else:
    st.info("👈 請先從左側執行「步驟一」抓取新聞。")
