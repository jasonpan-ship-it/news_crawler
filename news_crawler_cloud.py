import streamlit as st
import pandas as pd
import datetime as dt
from datetime import datetime
import pygsheets
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import urllib.request as req
import time as tt
import json
import warnings

# 忽略警告
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# --- 1. 介面設定 ---
st.set_page_config(page_title="新聞監測系統", page_icon="📰", layout="wide")
st.title("📰 綠能產業新聞自動爬取工具")

# 側邊欄：日期設定與執行
with st.sidebar:
    st.header("📅 搜尋參數設定")
    # 預設顯示今天
    today = datetime.now()
    start_date_input = st.date_input("開始日期", today - dt.timedelta(days=1))
    end_date_input = st.date_input("結束日期", today)
    
    start_date = datetime.combine(start_date_input, datetime.min.time())
    end_date = datetime.combine(end_date_input, datetime.max.time())
    
    run_button = st.button("🚀 開始執行爬蟲", use_container_width=True)

# --- 2. 資料清單 (從原程式碼移植) ---
keywords = ["太陽能", "再生能源", "電廠", "綠電", "光電", "風電", "儲能", "綠電交易", "麗升能源", "綠能"]

company_keywords = ["麗升", "陽光伏特家電力" ,"陽光伏特家" ,"台汽電綠能" ,"台汽電" ,"富威電力" ,"富威" ,"瓦特先生" ,"南方電力" ,"石門山新電力" ,"奇異果新能源" ,"首美綠能" ,"首美" ,"三地怪獸電力" ,"三地怪獸" ,"樺銳綠電科技" ,"樺銳綠電" ,"星星電力" ,"星星" ,"天能綠電" ,"開陽電力" ,"開陽" ,"博曜電力" ,"博曜" ,"亞福儲能" ,"莫比綠電" ,"華城能源" ,"華城" ,"名竣綠能" ,"名竣" ,"大同智能" ,"太陽神電力" ,"太陽神" ,"大自然能源電業" ,"寶富電力" ,"寶富" ,"中曜" ,"阿波羅電力" ,"阿波羅" ,"瓦力電能" ,"陽光綠電" ,"續興" ,"能元超商" ,"台灣碳資產電業" ,"康展電力" ,"康展" ,"台化綠能" ,"台化" ,"上晟能源科技" ,"上晟能源" ,"晨星電力" ,"晨星" ,"傑傅能源" ,"傑傅" ,"詮實能源" ,"詮實" ,"寶島陽光電力事業" ,"誠新電力" ,"雲豹能源科技" ,"雲豹能源" ,"香印永續" ,"義電智慧能源" ,"義電智慧" ,"宇軒電業" ,"玖暉永續電能" ,"曜越綠電" ,"艾涅爾電力" ,"艾涅爾" ,"興旺能源" ,"興旺" ,"茂欣能源" ,"茂欣" ,"和同能源" ,"和同" ,"安瑟樂威" ,"上集能源" ,"和潤電力" ,"和潤" ,"澎湖綠電" ,"禾丰電力" ,"禾丰" ,"新鑫電力" ,"新鑫" ,"台達能源" ,"台達" ,"精華能源" ,"精華" ,"國碩能源" ,"國碩" ,"永餘智能" ,"恆利電能" ,"艾地電力" ,"艾地" ,"新晶太陽光電科技" ,"新晶太陽光電" ,"天勢能源" ,"天勢" ,"承研能源科技" ,"承研能源" ,"統益能源" ,"統益" ,"怡和綠電超商" ,"中華系統整合" ,"裕鴻能源" ,"裕鴻" ,"明徽電力" ,"明徽" ,"弘昌泰" ,"昶峰綠能科技" ,"昶峰綠能" ,"成綠能" ,"有成" ,"十萬伏特電力" ,"十萬伏特" ,"友達電力" ,"友達" ,"澤生能源" ,"澤生" ,"光合作用" ,"昕明電力" ,"昕明" ,"鴻晶新科技" ,"鴻晶新" ,"毓盈" ,"天麋電力" ,"天麋" ,"新光源電力" ,"新光源" ,"恆立能源" ,"恆立" ,"星辰電力" ,"星辰" ,"辰昇能源" ,"辰昇" ,"康誠能源" ,"康誠" ,"寬域能源" ,"寬域" ,"大創電力" ,"大創" ,"太創能源" ,"太創" ,"大猩猩電能交易" ,"奉天電力" ,"台灣威迪克艾內斯達能源" ,"台灣威迪克艾內斯達" ,"育成電力" ,"橙鑫電力" ,"橙鑫" ,"耀鼎資源循環" ,"中日電力" ,"茂鴻電力" ,"茂鴻" ,"台灣智能漁電科技" ,"海利普新能源" ,"海利普" ,"特興能源顧問" ,"台灣智慧電能" ,"聯旭能源開發" ,"錦振能源" ,"錦振" ,"安能電業" ,"安能電業" ,"金豬能源科技" ,"金豬能源" ,"台塑綠電" ,"華璽能源" ,"華璽" ,"育渲投資" ,"歐悅能源" ,"歐悅" ,"庭林" ,"晟鋐科技" ,"星崴電力" ,"星崴" ,"漢為科技工程" ,"立豐光能" ,"立豐光能" ,"琉璃光綠能" ,"琉璃光" ,"道達爾能源" ,"東泰綠能投資" ,"富陽能開發" ,"偉祥科技" ,"偉祥" ,"凱智綠能科技" ,"永豐太陽能能源" ,"路加太陽能投資顧問" ,"如晅綠能開發" ,"力山綠能科技" ,"東之億綠能" ,"聯宏聚能科技" ,"太能系統" ,"易晶綠能系統" ,"永滔綠能" ,"永滔" ,"台灣所樂太陽能科技" ,"翰可能源" ,"翰可" ,"和合資源綠能" ,"維知科技" ,"加雲聯網" ,"汎武電機工業" ,"前進綠能科技" ,"光旭盈科技" ,"光旭盈" ,"晴棠寬能源工程" ,"凱米克實業" ,"大日頭" ,"新晶光電" ,"恆利能源" ,"光鼎能源科技" ,"環亞光電" ,"宣冠" ,"衆崴能源" ,"衆崴" ,"樂陽能源" ,"台灣和暄綠能" ,"聖展光能" ,"創睿能源" ,"創睿" ,"百利富能源" ,"百利富" ,"金電發能源" ,"鼎承能源科技" ,"昶耀開發" ,"星能" ,"日勝再生能源" ,"國軒科技" ,"國軒" ,"雲豹能源科技" ,"昇鈺光電" ,"昇鈺光電" ,"綠順科技" ,"綠順" ,"裕電能源" ,"裕電" ,"暘光綠能實業" ,"凡展綠能科技" ,"旭誠綠能" ,"大瀚鋼鐵" ,"綠葳能源科技" ,"中租電力科技" ,"歐得能源工程" ,"光煜能源" ,"光煜" ,"朝日能源" ,"嘉毅達光電企業" ,"始復能源" ,"始復" ,"銘懋工業" ,"宇軒鋼鐵工程" ,"晶成能源" ,"元晶太陽能科技" ,"兆信電通科技" ,"百盛能源科技" ,"百盛能源" ,"禾原新能源科技" ,"旭天能源" ,"全日光" ,"騰揚綠電" ,"綠農電科" ,"臺鹽綠能" ,"臺鹽" ,"昕毅科技" ,"潔力能源事業" ,"茂鴻電力" ,"茂鴻" ,"首美能源" ,"首美" ,"永日昇綠能" ,"夏爾特拉太陽能科技" ,"環球大宇宙太陽能工業" ,"凌積應用科技" ,"凌積應用" ,"崑鼎綠能環保" ,"盛齊綠能" ,"盛齊" ,"安哲益工程" ,"安哲益工程" ,"南亞光電" ,"家紳能源" ,"久研開發節能" ,"士能科技" ,"凱煬太陽能" ,"關鍵應用科技" ,"普晴科技實業" ,"向陽優能電力" ,"信邦電子" ,"善騰太陽能源科技商社" ,"台灣達亨能源科技" ,"天泰能源" ,"天泰" ,"泓筌科技" ,"泓筌" ,"成精密" ,"有成精密" ,"曜昇綠能" ,"曜昇" ,"金陽機電工程" ,"東元電機" ,"兆洋太陽能源" ,"鑫盈能源" ,"鑫盈" ,"重光電線電纜企業" ,"統益機電工程" ,"明軒科技" ,"紹洲興業" ,"博盛光電科技" ,"泓德能源科技" ,"泓德能源" ,"綠源科技" ,"綠源" ,"日山能源科技"]
company_keywords = list(set([k.strip() for k in company_keywords if k.strip() != ""]))

title_keywords = ["小水力","光電","綠能","綠電","風能","太陽能","再生","儲能","減碳","ESG","電池","地熱","風力","發電","魚塭","土地","水力","淨零","漁電","光儲","低地力","售電","台電","配電","輸電","升壓","環社","用電大戶","饋線","電表","表前","表後","需量反應","電網","土地開發","電廠","備轉","調頻","PCS","EMS","BMS","電力交易","併網","籌設","風電","電價","電業","香夾蘭","農業補助","CPPA","農電","農業設施許可","沼氣","生質能","Solar","PV","energy","solar","storage","光伏","能源政策","碳權","碳費","躉購","能源署","電業法","躉購費率","漁電共生"]

# --- 3. 核心功能函式 ---
def init_gsheet():
    try:
        service_account_info = json.loads(st.secrets["gcp_service_account"])
        gc = pygsheets.authorize(service_account_json=json.dumps(service_account_info))
        spreadsheet = gc.open_by_url('https://docs.google.com/spreadsheets/d/1b2UEnsJ0hASkqpR3n9VgfLoIkTRgrHtm8aYbzRho5BA')
        return spreadsheet.worksheet_by_title('最新新聞')
    except Exception as e:
        st.error(f"❌ Google Sheets 連線失敗: {e}")
        return None

# --- 4. 爬蟲主程式 ---
if run_button:
    sheet = init_gsheet()
    if sheet:
        dates, sources, categories, company_matches, title_keyword_matches, titles, links = [], [], [], [], [], [], []
        
        def append_news(title, url, date_obj, source, category):
            if start_date <= date_obj <= end_date:
                matched_title_keywords = [k for k in title_keywords if k in title]
                if not matched_title_keywords: return
                matched_company_keywords = [k for k in company_keywords if k in title]
                
                dates.append(date_obj.strftime("%Y-%m-%d"))
                sources.append(source)
                categories.append(category)
                title_keyword_matches.append(", ".join(matched_title_keywords))
                company_matches.append(", ".join(matched_company_keywords) if matched_company_keywords else "-")
                titles.append(title)
                links.append(url)

        status_text = st.empty()
        
        # --- Yahoo ---
        for kw in keywords:
            status_text.text(f"🔍 正在爬取 Yahoo: {kw}")
            try:
                q = quote(kw)
                url = f"https://tw.news.yahoo.com/search?p={q}"
                res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
                soup = BeautifulSoup(res.text, "html.parser")
                for art in soup.select("li div[class*='Cf']"):
                    a_tag = art.find("a")
                    meta_div = art.find("div", class_="C(#959595)")
                    if not a_tag or not meta_div: continue
                    title = a_tag.text.strip()
                    full_link = a_tag["href"] if a_tag["href"].startswith("http") else f"https://tw.news.yahoo.com{a_tag['href']}"
                    
                    time_str = meta_div.text.strip().split("•")[-1].strip()
                    today_now = datetime.now()
                    if "天前" in time_str:
                        date_obj = today_now - dt.timedelta(days=int(time_str.replace("天前","")))
                    elif "小時前" in time_str or "分鐘前" in time_str:
                        date_obj = today_now
                    else:
                        try:
                            cleaned = time_str.replace("早上", "").replace("下午", "").replace("晚上", "").replace("年","-").replace("月","-").replace("日","").strip()
                            date_obj = datetime.strptime(cleaned.split()[0], "%Y-%m-%d")
                        except: continue
                    append_news(title, full_link, date_obj, "Yahoo", kw)
            except: continue

        # --- UDN ---
        for kw in keywords:
            status_text.text(f"🔍 正在爬取 UDN: {kw}")
            try:
                url = f"https://udn.com/search/word/2/{quote(kw)}"
                res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
                root = BeautifulSoup(res.text, "html.parser")
                ti_list = root.find_all("h2")
                time_list = root.find_all("time", class_="story-list__time")
                for l, title_tag in enumerate(ti_list):
                    a_tag = title_tag.find("a")
                    if a_tag and l < len(time_list):
                        date_obj = datetime.strptime(time_list[l].text.strip()[:10], "%Y-%m-%d")
                        append_news(a_tag.text.strip(), a_tag["href"], date_obj, "UDN", kw)
            except: continue

        # --- MoneyDJ ---
        status_text.text("🔍 正在爬取 MoneyDJ...")
        for url, cat in [("https://www.moneydj.com/kmdj/common/listnewarticles.aspx?svc=NW&a=X0300023", "能源")]:
            try:
                res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
                soup = BeautifulSoup(res.text, "html.parser")
                titles_dj = soup.find_all("td", class_="ArticleTitle")
                times_dj = soup.find_all("td")
                for i, tag in enumerate(titles_dj):
                    href = "https://www.moneydj.com/" + tag.a["href"]
                    raw_date = times_dj[i*3].text.strip()
                    date_obj = datetime.strptime(f"{datetime.now().year}/{raw_date}"[:10], "%Y/%m/%d")
                    append_news(tag.a.text.strip(), href, date_obj, "MoneyDJ", cat)
            except: continue

        # --- 自由時報 ---
        status_text.text("🔍 正在爬取 自由時報...")
        for url, cat in [("https://news.ltn.com.tw/topic/%E7%B6%A0%E8%83%BD", "綠能")]:
            try:
                res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
                soup = BeautifulSoup(res.text, "html.parser")
                for item in soup.select("ul.list li"):
                    t_tag = item.find("h3")
                    if t_tag:
                        d_str = item.find("span", class_="time").text.strip()[:10]
                        append_news(t_tag.text.strip(), item.find("a")["href"], datetime.strptime(d_str, "%Y/%m/%d"), "自由時報", cat)
            except: continue

        # --- 組合成結果 ---
        final_df = pd.DataFrame({
            "日期": dates, "來源": sources, "分類": categories,
            "包含標題關鍵字": title_keyword_matches, "包含公司關鍵字": company_matches,
            "標題": titles, "新聞網址": links
        }).drop_duplicates(subset=["標題"]).sort_values(by="日期", ascending=False)

        if not final_df.empty:
            sheet.clear(start='A1')
            sheet.set_dataframe(final_df, 'A1')
            st.success(f"✅ 成功抓取 {len(final_df)} 筆新聞並上傳至 Google Sheets！")
            st.dataframe(final_df)
        else:
            st.warning("⚠️ 該日期範圍內沒有符合關鍵字的新聞。")
        status_text.empty()
