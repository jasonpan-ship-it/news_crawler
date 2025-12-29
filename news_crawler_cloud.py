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
            html_rows += f"""
            <tr>
                <td style='border:1px solid #ddd; padding:8px;'>{row['日期']}</td>
                <td style='border:1px solid #ddd; padding:8px;'><a href='{row['網址']}'>{row['標題']}</a></td>
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
            
            dates, sources, categories, company_matches, title_keyword_matches, titles, links = [], [], [], [], [], [], []
            keywords = ["太陽能", "再生能源", "電廠", "綠電", "光電",  "風電", "儲能", "綠電交易", "麗升能源", "綠能"]
            company_keywords = ["麗升", "陽光伏特家電力" ,"陽光伏特家" ,"台汽電綠能" ,"台汽電" ,"富威電力" ,"富威" ,"瓦特先生" ,"南方電力" ,"石門山新電力" ,"奇異果新能源" ,"首美綠能" ,"首美" ,"三地怪獸電力" ,"三地怪獸" ,"樺銳綠電科技" ,"樺銳綠電" ,"星星電力" ,"星星" ,"天能綠電" ,"開陽電力" ,"開陽" ,"博曜電力" ,"博曜" ,"亞福儲能" ,"莫比綠電" ,"華城能源" ,"華城" ,"名竣綠能" ,"名竣" ,"大同智能" ,"太陽神電力" ,"太陽神" ,"大自然能源電業" ,"寶富電力" ,"寶富" ,"中曜" ,"阿波羅電力" ,"阿波羅" ,"瓦力電能" ,"陽光綠電" ,"續興" ,"能元超商" ,"台灣碳資產電業" ,"康展電力" ,"康展" ,"台化綠能" ,"台化" ,"上晟能源科技" ,"上晟能源" ,"晨星電力" ,"晨星" ,"傑傅能源" ,"傑傅" ,"詮實能源" ,"詮實" ,"寶島陽光電力事業" ,"誠新電力" ,"雲豹能源科技" ,"雲豹能源" ,"香印永續" ,"義電智慧能源" ,"義電智慧" ,"宇軒電業" ,"玖暉永續電能" ,"曜越綠電" ,"艾涅爾電力" ,"艾涅爾" ,"興旺能源" ,"興旺" ,"茂欣能源" ,"茂欣" ,"和同能源" ,"和同" ,"安瑟樂威" ,"上集能源" ,"和潤電力" ,"和潤" ,"澎湖綠電" ,"禾丰電力" ,"禾丰" ,"新鑫電力" ,"新鑫" ,"台達能源" ,"台達" ,"精華能源" ,"精華" ,"國碩能源" ,"國碩" ,"永餘智能" ,"恆利電能" ,"恆利電能" ,"艾地電力" ,"艾地" ,"新晶太陽光電科技" ,"新晶太陽光電" ,"天勢能源" ,"天勢" ,"承研能源科技" ,"承研能源" ,"統益能源" ,"統益" ,"怡和綠電超商" ,"中華系統整合" ,"裕鴻能源" ,"裕鴻" ,"明徽電力" ,"明徽" ,"弘昌泰" ,"昶峰綠能科技" ,"昶峰綠能" ,"成綠能" ,"有成" ,"十萬伏特電力" ,"十萬伏特" ,"友達電力" ,"友達" ,"澤生能源" ,"澤生" ,"光合作用" ,"昕明電力" ,"昕明" ,"鴻晶新科技" ,"鴻晶新" ,"毓盈" ,"天麋電力" ,"天麋" ,"新光源電力" ,"新光源" ,"恆立能源" ,"恆立" ,"星辰電力" ,"星辰" ,"辰昇能源" ,"辰昇" ,"康誠能源" ,"康誠" ,"寬域能源" ,"寬域" ,"大創電力" ,"大創" ,"太創能源" ,"太創" ,"大猩猩電能交易" ,"奉天電力" ,"台灣威迪克艾內斯達能源" ,"育成電力" ,"橙鑫電力" ,"橙鑫" ,"耀鼎資源循環" ,"中日電力" ,"茂鴻電力" ,"茂鴻" ,"台灣智能漁電科技" ,"海利普新能源" ,"海利普" ,"特興能源顧問" ,"台灣智慧電能" ,"聯旭能源開發" ,"錦振能源" ,"錦振" ,"安能電業" ,"安能電業" ,"金豬能源科技" ,"金豬能源" ,"台塑綠電" ,"華璽能源" ,"華璽" ,"育渲投資" ,"歐悅能源" ,"歐悅" ,"庭林" ,"晟鋐科技" ,"星崴電力" ,"星崴" ,"漢為科技工程" ,"立豐光能" ,"立豐光能" ,"琉璃光綠能" ,"琉璃光" ,"道達爾能源" ,"東泰綠能投資" ,"富陽能開發" ,"偉祥科技" ,"偉祥" ,"凱智綠能科技" ,"永豐太陽能能源" ,"路加太陽能投資顧問" ,"如晅綠能開發" ,"力山綠能科技" ,"東之億綠能" ,"聯宏聚能科技" ,"太能系統" ,"易晶綠能系統" ,"永滔綠能" ,"永滔" ,"台灣所樂太陽能科技" ,"翰可能源" ,"翰可" ,"和合資源綠能" ,"維知科技" ,"加雲聯網" ,"汎武電機工業" ,"前進綠能科技" ,"光旭盈科技" ,"光旭盈" ,"晴棠寬能源工程" ,"凱米克實業" ,"大日頭" ,"新晶光電" ,"恆利能源" ,"光鼎能源科技" ,"環亞光電" ,"宣冠" ,"衆崴能源" ,"衆崴" ,"樂陽能源" ,"台灣和暄綠能" ,"聖展光能" ,"創睿能源" ,"創睿" ,"百利富能源" ,"百利富" ,"金電發能源" ,"鼎承能源科技" ,"昶耀開發" ,"星能" ,"日勝再生能源" ,"國軒科技" ,"國軒" ,"雲豹能源科技" ,"昇鈺光電" ,"昇鈺光電" ,"綠順科技" ,"綠順" ,"裕電能源" ,"裕電" ,"暘光綠能實業" ,"凡展綠能科技" ,"旭誠綠能" ,"大瀚鋼鐵" ,"綠葳能源科技" ,"中租電力科技" ,"歐得能源工程" ,"光煜能源" ,"光煜" ,"朝日能源" ,"嘉毅達光電企業" ,"始復能源" ,"始復" ,"銘懋工業" ,"宇軒鋼鐵工程" ,"晶成能源" ,"元晶太陽能科技" ,"兆信電通科技" ,"百盛能源科技" ,"百盛能源" ,"禾原新能源科技" ,"旭天能源" ,"全日光" ,"騰揚綠電" ,"綠農電科" ,"臺鹽綠能" ,"臺鹽" ,"昕毅科技" ,"潔力能源事業" ,"茂鴻電力" ,"茂鴻" ,"首美能源" ,"首美" ,"永日昇綠能" ,"夏爾特拉太陽能科技" ,"環球大宇宙太陽能工業" ,"凌積應用科技" ,"凌積應用" ,"崑鼎綠能環保" ,"盛齊綠能" ,"盛齊" ,"安哲益工程" ,"安哲益工程" ,"南亞光電" ,"南亞光電" ,"家紳能源" ,"家紳" ,"久研開發節能" ,"久研開發節能有限公司" ,"士能科技" ,"士能科技有限公司" ,"凱煬太陽能" ,"凱煬太陽能" ,"關鍵應用科技" ,"關鍵應用" ,"普晴科技實業" ,"普晴科技實業" ,"向陽優能電力" ,"向陽優能" ,"信邦電子" ,"信邦電子" ,"善騰太陽能源科技商社" ,"善騰太陽能源科技商社" ,"台灣達亨能源科技" ,"台灣達亨能源" ,"天泰能源" ,"天泰" ,"泓筌科技" ,"泓筌" ,"成精密" ,"有成精密" ,"曜昇綠能" ,"曜昇" ,"金陽機電工程" ,"東元電機" ,"東元電機" ,"兆洋太陽能源" ,"兆洋太陽能源有限公司" ,"鑫盈能源" ,"鑫盈" ,"重光電線電纜企業" ,"重光電線電纜企業" ,"統益機電工程" ,"統益機電工程" ,"明軒科技" ,"明軒科技有限公司" ,"紹洲興業" ,"紹洲興業" ,"博盛光電科技" ,"博盛光電科技有限公司" ,"泓德能源科技" ,"泓德能源" ,"綠源科技" ,"綠源" ,"日山能源科技" ,"日山能源科技有限公司"]
            company_keywords = [k.strip() for k in company_keywords if k.strip() != ""]
            title_keywords = ["小水力","光電","綠能","綠電","風能","太陽能","再生","儲能","減碳","ESG","電池","地熱","風力","發電","魚塭","土地","水力","淨零","漁電","光儲","低地力","售電","台電","配電","輸電","升壓","環社","用電大戶","饋線","電表","表前","表後","需量反應","電網","土地開發","電廠","備轉","調頻","PCS","EMS","BMS","電力交易","併網","籌設","風電","電價","電業","香夾蘭","農業補助","CPPA","農電","農業設施許可","沼氣","生質能","Solar","PV","energy","solar","storage","光伏","能源政策","碳權","碳費","躉購","能源署","電業法","躉購費率","漁電共生"]

            def append_news(title, url, date_obj, source, category):
                if start_date_obj <= date_obj <= end_date_obj:
                    m_title = [k for k in title_keywords if k in title]
                    if not m_title: return
                    m_comp = [k for k in company_keywords if k in title]
                    dates.append(date_obj.strftime("%Y-%m-%d"))
                    sources.append(source)
                    categories.append(category)
                    title_keyword_matches.append(", ".join(m_title))
                    company_matches.append(", ".join(m_comp) if m_comp else "-")
                    titles.append(title)
                    links.append(url)

            headers = {"User-Agent": "Mozilla/5.0"}
            for kw in keywords:
                try: # Yahoo
                    res = requests.get(f"https://tw.news.yahoo.com/search?p={quote(kw)}", headers=headers)
                    soup = BeautifulSoup(res.text, "html.parser")
                    for art in soup.select("li div[class*='Cf']"):
                        a = art.find("a")
                        m = art.find("div", class_="C(#959595)")
                        if a and m:
                            t = a.text.strip()
                            l = a["href"] if a["href"].startswith("http") else f"https://tw.news.yahoo.com{a['href']}"
                            t_str = m.text.strip().split("•")[-1].strip()
                            now = datetime.now()
                            d_obj = None
                            if "天前" in t_str: d_obj = now - dt.timedelta(days=int(t_str.replace("天前","")))
                            elif "小時" in t_str or "分鐘" in t_str: d_obj = now
                            else:
                                try: d_obj = datetime.strptime(t_str.replace("早上","").replace("下午","").replace("年","-").replace("月","-").replace("日","").split()[0], "%Y-%m-%d")
                                except: continue
                            if d_obj: append_news(t, l, d_obj, "Yahoo", kw)
                except: continue
                try: # UDN
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
                st.session_state.edited_df = df
                st.success(f"✅ 抓取完成！共 {len(df)} 筆新聞。")
            else:
                st.error("❌ 此日期範圍內查無新聞。")

    st.divider()

    st.header("2️⃣ AI 自動摘要")
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
                            messages=[{"role": "user", "content": f"請以繁體中文條列約40個字的簡短摘要重點：\n\n{text[:2500]}"}]
                        )
                        st.session_state.edited_df.at[idx, 'AI 新聞摘要'] = res.choices[0].message.content.strip()
            st.rerun()

    st.divider()

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
    st.session_state.edited_df = st.data_editor(
        st.session_state.edited_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "日期": st.column_config.TextColumn("日期", disabled=True),
            "標題": st.column_config.TextColumn("標題", width="large"),
            "網址": st.column_config.LinkColumn("原文連結", display_text="(查看)", width="small"),
            "AI 新聞摘要": st.column_config.TextColumn("AI 新聞摘要", width="large")
        },
        column_order=["日期", "來源", "標題", "網址", "AI 新聞摘要"]
    )
else:
    st.info("👈 請先從左側執行「步驟一」抓取新聞。")
