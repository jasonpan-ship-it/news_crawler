import streamlit as st
import pandas as pd
import datetime as dt
from datetime import datetime
import pygsheets
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import urllib.request as req
import bs4
import json
import gspread
from google.oauth2.service_account import Credentials
from openai import OpenAI
from pandas.tseries.offsets import BusinessDay

# --- 設定區 ---
st.set_page_config(page_title="綠能新聞發佈系統", page_icon="⚡", layout="wide")

# 關鍵字清單 (延用你的版本)
KEYWORDS = ["太陽能", "再生能源", "電廠", "綠電", "光電",  "風電", "儲能", "綠電交易", "麗升能源", "綠能"]
TITLE_KEYWORDS = ["小水力","光電","綠能","綠電","風能","太陽能","再生","儲能","減碳","ESG","電池","地熱","風力","發電","魚塭","土地","水力","淨零","漁電","光儲","低地力","售電","台電","配電","輸電","升壓","環社","用電大戶","饋線","電表","表前","表後","需量反應","電網","土地開發","電廠","備轉","調頻","PCS","EMS","BMS","電力交易","併網","籌設","風電","電價","電業","香夾蘭","農業補助","CPPA","農電","農業設施許可","沼氣","生質能","Solar","PV","energy","solar","storage","光伏","能源政策","碳權","碳費","躉購","能源署","電業法","躉購費率","漁電共生"]
COMPANY_KEYWORDS = ["麗升", "陽光伏特家電力" ,"陽光伏特家" ,"台汽電綠能" ,"台汽電" ,"富威電力" ,"富威" ,"瓦特先生" ,"南方電力" ,"石門山新電力" ,"奇異果新能源" ,"首美綠能" ,"首美" ,"三地怪獸電力" ,"三地怪獸" ,"樺銳綠電科技" ,"樺銳綠電" ,"星星電力" ,"星星" ,"天能綠電" ,"開陽電力" ,"開陽" ,"博曜電力" ,"博曜" ,"亞福儲能" ,"莫比綠電" ,"華城能源" ,"華城" ,"名竣綠能" ,"名竣" ,"大同智能" ,"太陽神電力" ,"太陽神" ,"大自然能源電業" ,"寶富電力" ,"寶富" ,"中曜" ,"阿波羅電力" ,"阿波羅" ,"瓦力電能" ,"陽光綠電" ,"續興" ,"能元超商" ,"台灣碳資產電業" ,"康展電力" ,"康展" ,"台化綠能" ,"台化" ,"上晟能源科技" ,"上晟能源" ,"晨星電力" ,"晨星" ,"傑傅能源" ,"傑傅" ,"詮實能源" ,"詮實" ,"寶島陽光電力事業" ,"誠新電力" ,"雲豹能源科技" ,"雲豹能源" ,"香印永續" ,"義電智慧能源" ,"義電智慧" ,"宇軒電業" ,"玖暉永續電能" ,"曜越綠電" ,"艾涅爾電力" ,"艾涅爾" ,"興旺能源" ,"興旺" ,"茂欣能源" ,"茂欣" ,"和同能源" ,"和同" ,"安瑟樂威" ,"上集能源" ,"和潤電力" ,"和潤" ,"澎湖綠電" ,"禾丰電力" ,"禾丰" ,"新鑫電力" ,"新鑫" ,"台達能源" ,"台達" ,"精華能源" ,"精華" ,"國碩能源" ,"國碩" ,"永餘智能" ,"恆利電能" ,"艾地電力" ,"艾地" ,"新晶太陽光電科技" ,"新晶太陽光電" ,"天勢能源" ,"天勢" ,"承研能源科技" ,"承研能源" ,"統益能源" ,"統益" ,"怡和綠電超商" ,"中華系統整合" ,"裕鴻能源" ,"裕鴻" ,"明徽電力" ,"明徽" ,"弘昌泰" ,"昶峰綠能科技" ,"昶峰綠能" ,"成綠能" ,"有成" ,"十萬伏特電力" ,"十萬伏特" ,"友達電力" ,"友達" ,"澤生能源" ,"澤生" ,"光合作用" ,"昕明電力" ,"昕明" ,"鴻晶新科技" ,"鴻晶新" ,"毓盈" ,"天麋電力" ,"天麋" ,"新光源電力" ,"新光源" ,"恆立能源" ,"恆立" ,"星辰電力" ,"星辰" ,"辰昇能源" ,"辰昇" ,"康誠能源" ,"康誠" ,"寬域能源" ,"寬域" ,"大創電力" ,"大創" ,"太創能源" ,"太創" ,"大猩猩電能交易" ,"奉天電力" ,"台灣威迪克艾內斯達能源" ,"育成電力" ,"橙鑫電力" ,"橙鑫" ,"耀鼎資源循環" ,"中日電力" ,"茂鴻電力" ,"茂鴻" ,"台灣智能漁電科技" ,"海利普新能源" ,"海利普" ,"特興能源顧問" ,"台灣智慧電能" ,"聯旭能源開發" ,"錦振能源" ,"錦振" ,"安能電業" ,"安能電業" ,"金豬能源科技" ,"金豬能源" ,"台塑綠電" ,"華璽能源" ,"華璽" ,"育渲投資" ,"歐悅能源" ,"歐悅" ,"庭林" ,"晟鋐科技" ,"星崴電力" ,"星崴" ,"漢為科技工程" ,"立豐光能" ,"立豐光能" ,"琉璃光綠能" ,"琉璃光" ,"道達爾能源" ,"東泰綠能投資" ,"富陽能開發" ,"偉祥科技" ,"偉祥" ,"凱智綠能科技" ,"永豐太陽能能源" ,"路加太陽能投資顧問" ,"如晅綠能開發" ,"力山綠能科技" ,"東之億綠能" ,"聯宏聚能科技" ,"太能系統" ,"易晶綠能系統" ,"永滔綠能" ,"永滔" ,"台灣所樂太陽能科技" ,"翰可能源" ,"翰可" ,"和合資源綠能" ,"維知科技" ,"加雲聯網" ,"汎武電機工業" ,"前進綠能科技" ,"光旭盈科技" ,"光旭盈" ,"晴棠寬能源工程" ,"凱米克實業" ,"大日頭" ,"新晶光電" ,"恆利能源" ,"光鼎能源科技" ,"環亞光電" ,"宣冠" ,"衆崴能源" ,"衆崴" ,"樂陽能源" ,"台灣和暄綠能" ,"聖展光能" ,"創睿能源" ,"創睿" ,"百利富能源" ,"百利富" ,"金電發能源" ,"鼎承能源科技" ,"昶耀開發" ,"星能" ,"日勝再生能源" ,"國軒科技" ,"國軒" ,"雲豹能源科技" ,"昇鈺光電" ,"昇鈺光電" ,"綠順科技" ,"綠順" ,"裕電能源" ,"裕電" ,"暘光綠能實業" ,"凡展綠能科技" ,"旭誠綠能" ,"大瀚鋼鐵" ,"綠葳能源科技" ,"中租電力科技" ,"歐得能源工程" ,"光煜能源" ,"光煜" ,"朝日能源" ,"嘉毅達光電企業" ,"始復能源" ,"始復" ,"銘懋工業" ,"宇軒鋼鐵工程" ,"晶成能源" ,"元晶太陽能科技" ,"兆信電通科技" ,"百盛能源科技" ,"百盛能源" ,"禾原新能源科技" ,"旭天能源" ,"全日光" ,"騰揚綠電" ,"綠農電科" ,"臺鹽綠能" ,"臺鹽" ,"昕毅科技" ,"潔力能源事業" ,"茂鴻電力" ,"茂鴻" ,"首美能源" ,"首美" ,"永日昇綠能" ,"夏爾特拉太陽能科技" ,"環球大宇宙太陽能工業" ,"凌積應用科技" ,"凌積應用" ,"崑鼎綠能環保" ,"盛齊綠能" ,"盛齊" ,"安哲益工程" ,"安哲益工程" ,"南亞光電" ,"南亞光電" ,"家紳能源" ,"家紳" ,"久研開發節能" ,"久研開發節能有限公司" ,"士能科技" ,"士能科技有限公司" ,"凱煬太陽能" ,"凱煬太陽能" ,"關鍵應用科技" ,"關鍵應用" ,"普晴科技實業" ,"普晴科技實業" ,"向陽優能電力" ,"向陽優能" ,"信邦電子" ,"信邦電子" ,"善騰太陽能源科技商社" ,"善騰太陽能源科技商社" ,"台灣達亨能源科技" ,"台灣達亨能源" ,"天泰能源" ,"天泰" ,"泓筌科技" ,"泓筌" ,"成精密" ,"有成精密" ,"曜昇綠能" ,"曜昇" ,"金陽機電工程" ,"東元電機" ,"東元電機" ,"兆洋太陽能源" ,"兆洋太陽能源有限公司" ,"鑫盈能源" ,"鑫盈" ,"重光電線電纜企業" ,"重光電線電纜企業" ,"統益機電工程" ,"統益機電工程" ,"明軒科技" ,"明軒科技有限公司" ,"紹洲興業" ,"紹洲興業" ,"博盛光電科技" ,"博盛光電科技有限公司" ,"泓德能源科技" ,"泓德能源" ,"綠源科技" ,"綠源" ,"日山能源科技" ,"日山能源科技有限公司"]
COMPANY_KEYWORDS = list(set([k.strip() for k in COMPANY_KEYWORDS if k.strip() != ""]))

# --- 工具函式 ---
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
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in ['article', 'main', 'div']:
            content = soup.find(tag)
            if content and len(content.text.strip()) > 200:
                return content.get_text(separator="\n", strip=True)
        return soup.get_text(separator="\n", strip=True)
    except: return ""

# --- 側邊欄 ---
with st.sidebar:
    st.title("⚡ 綠能新聞發佈系統")
    
    st.header("1️⃣ 抓取新聞資料")
    today_dt = pd.Timestamp.now().normalize()
    last_bus_day = (today_dt - BusinessDay(1)).to_pydatetime()
    s_date = st.date_input("開始日期", last_bus_day)
    e_date = st.date_input("結束日期", today_dt)
    
    if st.button("🚀 執行爬蟲並上傳", use_container_width=True):
        with st.spinner("新聞爬取中..."):
            start_date_obj = datetime.combine(s_date, datetime.min.time())
            end_date_obj = datetime.combine(e_date, datetime.max.time())
            
            # --- 延用你的核心爬蟲邏輯 ---
            dates, sources, categories, company_matches, title_keyword_matches, titles, links = [], [], [], [], [], [], []
            
            def append_news(title, url, date_obj, source, category):
                if start_date_obj <= date_obj <= end_date_obj:
                    m_title = [k for k in TITLE_KEYWORDS if k in title]
                    if m_title:
                        m_comp = [k for k in COMPANY_KEYWORDS if k in title]
                        dates.append(date_obj.strftime("%Y-%m-%d"))
                        sources.append(source)
                        categories.append(category)
                        title_keyword_matches.append(", ".join(m_title))
                        company_matches.append(", ".join(m_comp) if m_comp else "-")
                        titles.append(title)
                        links.append(url)

            # 🔍 Yahoo (你的邏輯)
            headers = {"User-Agent": "Mozilla/5.0"}
            for kw in KEYWORDS:
                try:
                    q = quote(kw)
                    res = requests.get(f"https://tw.news.yahoo.com/search?p={q}", headers=headers)
                    soup = BeautifulSoup(res.text, "html.parser")
                    for art in soup.select("li div[class*='Cf']"):
                        a_tag = art.find("a")
                        meta_div = art.find("div", class_="C(#959595)")
                        if not a_tag: continue
                        t = a_tag.text.strip()
                        l = a_tag["href"] if a_tag["href"].startswith("http") else f"https://tw.news.yahoo.com{a_tag['href']}"
                        d_obj = None
                        if meta_div:
                            time_str = meta_div.text.strip().split("•")[-1].strip()
                            now = datetime.now()
                            if "天前" in time_str: d_obj = now - dt.timedelta(days=int(time_str.replace("天前","")))
                            elif "小時" in time_str or "分鐘" in time_str: d_obj = now
                            else:
                                try: d_obj = datetime.strptime(time_str.replace("年","-").replace("月","-").replace("日","").split()[0], "%Y-%m-%d")
                                except: continue
                        if d_obj: append_news(t, l, d_obj, "Yahoo", kw)
                except: continue

            # 🔍 UDN (你的邏輯)
            for kw in KEYWORDS:
                try:
                    res = requests.get(f"https://udn.com/search/word/2/{quote(kw)}", headers=headers)
                    soup = BeautifulSoup(res.text, "html.parser")
                    ti_box = soup.find("div", class_="context-box__content story-list__holder story-list__holder--full")
                    if not ti_box: continue
                    ti_h2 = ti_box.find_all("h2")
                    ti_time = ti_box.find_all("time", class_="story-list__time")
                    for l_idx, h2 in enumerate(ti_h2):
                        a = h2.find("a")
                        if a and l_idx < len(ti_time):
                            d_obj = datetime.strptime(ti_time[l_idx].text.strip()[:10], "%Y-%m-%d")
                            append_news(a.text.strip(), a["href"], d_obj, "UDN", kw)
                except: continue

            # --- 組合資料 ---
            final_df = pd.DataFrame({
                "日期": dates, "來源": sources, "分類": categories,
                "包含標題關鍵字": title_keyword_matches, "包含公司關鍵字": company_matches,
                "標題": titles, "新聞網址": links, "AI 新聞摘要": [""] * len(titles)
            }).drop_duplicates(subset=["標題"]).sort_values(by="日期", ascending=False)
            
            # --- 寫入 Google Sheet ---
            wks = get_pygsheets_wks()
            wks.clear(start='A1')
            wks.set_dataframe(final_df, 'A1')
            st.success(f"步驟一完成！抓取到 {len(final_df)} 筆。")

    st.divider()
    st.header("2️⃣ 人工審核文章")
    st.link_button("📂 開啟 Sheets 刪減", "https://docs.google.com/spreadsheets/d/1b2UEnsJ0hASkqpR3n9VgfLoIkTRgrHtm8aYbzRho5BA/edit", use_container_width=True)

    st.divider()
    st.header("3️⃣ AI 自動摘要")
    if st.button("🤖 執行 OpenAI 摘要", use_container_width=True):
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        sheet = get_gspread_wks()
        rows = sheet.get_all_values()
        p = st.progress(0)
        for idx, row in enumerate(rows[1:], start=2):
            url = row[6] # 新聞網址在第 7 欄
            summary = row[7] if len(row) > 7 else ""
            if url.strip() and not summary.strip():
                st.write(f"摘要處理中: {url[:30]}...")
                text = extract_webpage_text(url)
                if text:
                    res = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": f"請以繁體中文摘要約40字：\n\n{text[:2500]}"}]
                    )
                    sheet.update_cell(idx, 8, res.choices[0].message.content.strip())
            p.progress(idx / len(rows))
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
