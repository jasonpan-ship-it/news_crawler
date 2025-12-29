import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import quote
import urllib.request as req
import bs4
from datetime import datetime
import datetime as dt
from pandas.tseries.offsets import BusinessDay
import warnings
import time as tt

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

def build_html_body(title_text, df):
    """建立符合您格式要求的 HTML 表格"""
    intro = f"""
    {title_text}<br>
    <p style="color:gray; font-style:italic;">
    (抓取包含 <a href="#">特定關鍵字</a> 的新聞，如果需要增加新聞網站或關鍵字請聯繫JP)</p>
    """
    
    html_rows = ""
    for _, row in df.iterrows():
        # 日期格式化
        try:
            d_str = datetime.strptime(str(row['日期']), "%Y-%m-%d").strftime("%m/%d")
        except:
            d_str = str(row['日期'])

        # 公司關鍵字顯示
        comp_kw = row.get('包含公司關鍵字', '-')
        if pd.isna(comp_kw) or comp_kw == "": comp_kw = "-"

        html_rows += f"""
        <tr>
            <td style='border:1px solid #333; padding:8px;'>{d_str}</td>
            <td style='border:1px solid #333; padding:8px;'><a href='{row['網址']}'>{row['標題']}</a></td>
            <td style='border:1px solid #333; padding:8px;'>{comp_kw}</td>
            <td style='border:1px solid #333; padding:8px;'>{row.get('AI 新聞摘要', '')}</td>
        </tr>"""
    
    table_html = f"""
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; font-size: 14px; border: 1px solid #333;">
        <thead><tr style="background-color: #f2f2f2; text-align: left;">
            <th style="width:5%;">日期</th>
            <th style="width:25%;">標題</th>
            <th style="width:10%;">公司</th>
            <th style="width:60%;">AI摘要</th>
        </tr></thead>
        <tbody>{html_rows}</tbody>
    </table>
    """
    return f"<html><body>{intro}{table_html}</body></html>"

def send_split_emails(df):
    sender = st.secrets["EMAIL_SENDER"]
    password = st.secrets["EMAIL_PASSWORD"]
    receiver = st.secrets["EMAIL_RECEIVER"]
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # 邏輯：有公司關鍵字 -> Group A (競業)；沒有 -> Group B (產業)
    def has_company_kw(val):
        if not val or pd.isna(val): return False
        s = str(val).strip().replace("-", "")
        return len(s) > 0

    group_a = df[df['包含公司關鍵字'].apply(has_company_kw)]
    group_b = df[~df['包含公司關鍵字'].apply(has_company_kw)]

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            
            # 發送 Group A
            if not group_a.empty:
                msg = MIMEMultipart()
                msg['Subject'] = f"{today_str} 競業新聞整理"
                msg['From'] = f"新聞機器人 <{sender}>"
                msg['To'] = receiver
                msg.attach(MIMEText(build_html_body("本日競業新聞整理如下：", group_a), 'html'))
                server.send_message(msg)
                st.toast(f"✅ 競業新聞 ({len(group_a)} 封) 已發送")

            # 發送 Group B
            if not group_b.empty:
                msg = MIMEMultipart()
                msg['Subject'] = f"{today_str} 產業新聞整理"
                msg['From'] = f"新聞機器人 <{sender}>"
                msg['To'] = receiver
                msg.attach(MIMEText(build_html_body("本日產業新聞整理如下：", group_b), 'html'))
                server.send_message(msg)
                st.toast(f"✅ 產業新聞 ({len(group_b)} 封) 已發送")
        return True
    except Exception as e:
        st.error(f"發信失敗: {e}")
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
        with st.spinner("正在執行全網爬蟲..."):
            start_date_obj = datetime.combine(s_date, datetime.min.time())
            end_date_obj = datetime.combine(e_date, datetime.max.time())
            
            # === 以下為您 news_competitor.py 的完整清單與邏輯 ===
            
            # 初始化
            dates, sources, categories, company_matches, title_keyword_matches, titles, links = [], [], [], [], [], [], []
            
            keywords = ["太陽能", "再生能源", "電廠", "綠電", "光電",  "風電", "儲能", "綠電交易", "麗升能源", "綠能"]
            
            company_keywords = ["麗升", "陽光伏特家電力" ,"陽光伏特家" ,"台汽電綠能" ,"台汽電" ,"富威電力" ,"富威" ,"瓦特先生" ,"瓦特先生" ,"南方電力" ,"" ,"花蓮綠能" ,"" ,"石門山新電力" ,"" ,"奇異果新能源" ,"" ,"首美綠能" ,"首美" ,"三地怪獸電力" ,"三地怪獸" ,"樺銳綠電科技" ,"樺銳綠電" ,"星星電力" ,"星星" ,"天能綠電" ,"天能綠電" ,"開陽電力" ,"開陽" ,"博曜電力" ,"博曜" ,"亞福儲能" ,"亞福儲能" ,"莫比綠電" ,"莫比綠電" ,"華城能源" ,"華城" ,"名竣綠能" ,"名竣" ,"大同智能" ,"大同智能" ,"太陽神電力" ,"太陽神" ,"大自然能源電業" ,"大自然能源電業" ,"寶富電力" ,"寶富" ,"中曜" ,"中曜" ,"阿波羅電力" ,"阿波羅" ,"瓦力電能" ,"瓦力電能" ,"陽光綠電" ,"陽光綠電" ,"續興" ,"續興" ,"能元超商" ,"能元超商" ,"台灣碳資產電業" ,"台灣碳資產電業" ,"康展電力" ,"康展" ,"台化綠能" ,"台化" ,"上晟能源科技" ,"上晟能源" ,"晨星電力" ,"晨星" ,"傑傅能源" ,"傑傅" ,"詮實能源" ,"詮實" ,"寶島陽光電力事業" ,"寶島陽光電力事業" ,"誠新電力" ,"" ,"雲豹能源科技" ,"雲豹能源" ,"香印永續" ,"香印永續" ,"義電智慧能源" ,"義電智慧" ,"宇軒電業" ,"宇軒電業" ,"玖暉永續電能" ,"玖暉永續電能" ,"曜越綠電" ,"曜越綠電" ,"艾涅爾電力" ,"艾涅爾" ,"興旺能源" ,"興旺" ,"茂欣能源" ,"茂欣" ,"和同能源" ,"和同" ,"安瑟樂威" ,"安瑟樂威" ,"上集能源" ,"上集" ,"和潤電力" ,"和潤" ,"澎湖綠電" ,"澎湖綠電" ,"禾丰電力" ,"禾丰" ,"新鑫電力" ,"新鑫" ,"台達能源" ,"台達" ,"精華能源" ,"精華" ,"國碩能源" ,"國碩" ,"永餘智能" ,"永餘智能" ,"恆利電能" ,"恆利電能" ,"艾地電力" ,"艾地" ,"新晶太陽光電科技" ,"新晶太陽光電" ,"天勢能源" ,"天勢" ,"承研能源科技" ,"承研能源" ,"統益能源" ,"統益" ,"怡和綠電超商" ,"怡和綠電超商" ,"中華系統整合" ,"中華系統整合" ,"裕鴻能源" ,"裕鴻" ,"明徽電力" ,"明徽" ,"弘昌泰" ,"弘昌泰" ,"昶峰綠能科技" ,"昶峰綠能" ,"成綠能" ,"有成" ,"十萬伏特電力" ,"十萬伏特" ,"友達電力" ,"友達" ,"澤生能源" ,"澤生" ,"光合作用" ,"光合作用" ,"昕明電力" ,"昕明" ,"鴻晶新科技" ,"鴻晶新" ,"毓盈" ,"毓盈" ,"天麋電力" ,"天麋" ,"新光源電力" ,"新光源" ,"恆立能源" ,"恆立" ,"星辰電力" ,"星辰" ,"辰昇能源" ,"辰昇" ,"康誠能源" ,"康誠" ,"寬域能源" ,"寬域" ,"大創電力" ,"大創" ,"太創能源" ,"太創" ,"大猩猩電能交易" ,"大猩猩電能交易" ,"奉天電力" ,"奉天" ,"台灣威迪克艾內斯達能源" ,"台灣威迪克艾內斯達" ,"育成電力" ,"" ,"橙鑫電力" ,"橙鑫" ,"耀鼎資源循環" ,"耀鼎資源循環" ,"中日電力" ,"" ,"茂鴻電力" ,"茂鴻" ,"台灣智能漁電科技" ,"台灣智能漁電" ,"海利普新能源" ,"海利普" ,"特興能源顧問" ,"特興能源顧問" ,"台灣智慧電能" ,"台灣智慧電能" ,"聯旭能源開發" ,"聯旭能源開發" ,"錦振能源" ,"錦振" ,"安能電業" ,"安能電業" ,"金豬能源科技" ,"金豬能源" ,"台塑綠電" ,"台塑綠電" ,"華璽能源" ,"華璽" ,"育渲投資" ,"育渲投資有限公司" ,"歐悅能源" ,"歐悅" ,"庭林" ,"庭林" ,"晟鋐科技" ,"晟鋐科技有限公司" ,"星崴電力" ,"星崴" ,"漢為科技工程" ,"漢為科技工程有限公司" ,"立豐光能" ,"立豐光能" ,"琉璃光綠能" ,"琉璃光" ,"道達爾能源" ,"" ,"東泰綠能投資" ,"東泰綠能投資有限公司" ,"富陽能開發" ,"富陽能開發" ,"偉祥科技" ,"偉祥" ,"凱智綠能科技" ,"凱智綠能" ,"永豐太陽能能源" ,"永豐太陽能能源有限公司" ,"路加太陽能投資顧問" ,"路加太陽能投資顧問" ,"如晅綠能開發" ,"如晅綠能開發有限公司" ,"力山綠能科技" ,"力山綠能科技有限公司" ,"東之億綠能" ,"東之億綠能有限公司" ,"聯宏聚能科技" ,"聯宏聚能科技有限公司" ,"太能系統" ,"太能系統" ,"易晶綠能系統" ,"易晶綠能系統有限公司" ,"永滔綠能" ,"永滔" ,"台灣所樂太陽能科技" ,"台灣所樂太陽能" ,"翰可能源" ,"翰可" ,"和合資源綠能" ,"和合資源綠能有限公司" ,"維知科技" ,"維知【贊助】" ,"加雲聯網" ,"加雲聯網" ,"汎武電機工業" ,"汎武電機工業" ,"前進綠能科技" ,"前進綠能科技有限公司" ,"光旭盈科技" ,"光旭盈" ,"晴棠寬能源工程" ,"晴棠寬能源工程有限公司" ,"凱米克實業" ,"凱米克實業" ,"大日頭" ,"大日頭" ,"新晶光電" ,"新晶光電" ,"恆利能源" ,"恆利" ,"光鼎能源科技" ,"光鼎能源科技有限公司" ,"環亞光電" ,"環亞光電" ,"宣冠" ,"宣冠" ,"衆崴能源" ,"衆崴" ,"樂陽能源" ,"樂陽能源有限公司" ,"台灣和暄綠能" ,"台灣和暄" ,"聖展光能" ,"聖展光能" ,"創睿能源" ,"創睿" ,"百利富能源" ,"百利富" ,"金電發能源" ,"金電發能源有限公司" ,"鼎承能源科技" ,"鼎承能源" ,"昶耀開發" ,"昶耀開發有限公司" ,"星能" ,"星能" ,"日勝再生能源" ,"日勝再生能源有限公司(台灣大根公司集團)" ,"國軒科技" ,"國軒" ,"雲豹能源科技" ,"雲豹能源" ,"昇鈺光電" ,"昇鈺光電" ,"綠順科技" ,"綠順" ,"裕電能源" ,"裕電" ,"暘光綠能實業" ,"暘光綠能實業" ,"凡展綠能科技" ,"凡展綠能" ,"旭誠綠能" ,"旭誠綠能有限公司" ,"大瀚鋼鐵" ,"大瀚鋼鐵" ,"綠葳能源科技" ,"綠葳能源科技有限公司" ,"中租電力科技" ,"中租電力" ,"歐得能源工程" ,"歐得能源工程有限公司" ,"光煜能源" ,"光煜" ,"朝日能源" ,"朝日能源有限公司" ,"嘉毅達光電企業" ,"嘉毅達光電企業" ,"始復能源" ,"始復" ,"銘懋工業" ,"銘懋工業" ,"宇軒鋼鐵工程" ,"" ,"晶成能源" ,"晶成" ,"元晶太陽能科技" ,"元晶太陽能" ,"兆信電通科技" ,"兆信電通科技有限公司" ,"百盛能源科技" ,"百盛能源" ,"禾原新能源科技" ,"禾原新能源" ,"旭天能源" ,"旭天" ,"全日光" ,"全日光有限公司" ,"騰揚綠電" ,"騰揚綠電有限公司" ,"綠農電科" ,"綠農電科" ,"臺鹽綠能" ,"臺鹽" ,"昕毅科技" ,"昕毅科技有限公司" ,"潔力能源事業" ,"潔力能源事業有限公司" ,"茂鴻電力" ,"茂鴻" ,"首美能源" ,"首美" ,"永日昇綠能" ,"永日昇綠能有限公司" ,"夏爾特拉太陽能科技" ,"夏爾特拉太陽能" ,"環球大宇宙太陽能工業" ,"環球大宇宙太陽能工業有限公司" ,"凌積應用科技" ,"凌積應用" ,"崑鼎綠能環保" ,"崑鼎綠能環保" ,"盛齊綠能" ,"盛齊" ,"安哲益工程" ,"安哲益工程" ,"南亞光電" ,"南亞光電" ,"家紳能源" ,"家紳" ,"久研開發節能" ,"久研開發節能有限公司" ,"士能科技" ,"士能科技有限公司" ,"凱煬太陽能" ,"凱煬太陽能" ,"關鍵應用科技" ,"關鍵應用" ,"普晴科技實業" ,"普晴科技實業" ,"向陽優能電力" ,"向陽優能" ,"信邦電子" ,"信邦電子" ,"善騰太陽能源科技商社" ,"善騰太陽能源科技商社" ,"台灣達亨能源科技" ,"台灣達亨能源" ,"天泰能源" ,"天泰" ,"泓筌科技" ,"泓筌" ,"成精密" ,"有成精密" ,"曜昇綠能" ,"曜昇" ,"金陽機電工程" ,"金陽機電工程有限公司" ,"東元電機" ,"東元電機" ,"兆洋太陽能源" ,"兆洋太陽能源有限公司" ,"鑫盈能源" ,"鑫盈" ,"重光電線電纜企業" ,"重光電線電纜企業" ,"統益機電工程" ,"統益機電工程" ,"明軒科技" ,"明軒科技有限公司" ,"紹洲興業" ,"紹洲興業" ,"博盛光電科技" ,"博盛光電科技有限公司" ,"泓德能源科技" ,"泓德能源" ,"綠源科技" ,"綠源" ,"日山能源科技" ,"日山能源科技有限公司"]
            company_keywords = [k.strip() for k in company_keywords if k.strip() != ""]
            
            title_keywords= ["小水力","光電","綠能","綠電","風能","太陽能","再生","儲能","減碳","ESG","電池","地熱","風力","發電","魚塭","土地","水力","淨零","漁電","光儲","低地力","售電","台電","配電","輸電","升壓","環社","用電大戶","饋線","電表","表前","表後","需量反應","電網","土地開發","電廠","備轉","調頻","PCS","EMS","BMS","電力交易","併網","籌設","風電","電價","電業","香夾蘭","農業補助","CPPA","農電","農業設施許可","沼氣","生質能","Solar","PV","energy","solar","storage","光伏","能源政策","碳權","碳費","躉購","能源署","電業法","躉購費率","漁電共生"]

            def find_company_keywords(text):
                return [k for k in company_keywords if k in text]

            def append_news(title, url, date_obj, source, category):
                if start_date_obj <= date_obj <= end_date_obj:
                    matched_title_keywords = [k for k in title_keywords if k in title]
                    if not matched_title_keywords:
                        return
                    matched_company_keywords = find_company_keywords(title)
                    dates.append(date_obj.strftime("%Y-%m-%d"))
                    sources.append(source)
                    categories.append(category)
                    title_keyword_matches.append(", ".join(matched_title_keywords))
                    company_matches.append(", ".join(matched_company_keywords) if matched_company_keywords else "-")
                    titles.append(title)
                    links.append(url)

            # --- Yahoo 爬蟲 ---
            headers = {"User-Agent": "Mozilla/5.0"}
            for kw in keywords:
                try:
                    q = quote(kw)
                    res = requests.get(f"https://tw.news.yahoo.com/search?p={q}", headers=headers)
                    soup = BeautifulSoup(res.text, "html.parser")
                    articles = soup.select("li div[class*='Cf']")
                    for art in articles:
                        a_tag = art.find("a")
                        meta_div = art.find("div", class_="C(#959595)")
                        if not a_tag: continue
                        title = a_tag.text.strip()
                        href = a_tag["href"]
                        full_link = href if href.startswith("http") else f"https://tw.news.yahoo.com{href}"
                        date_obj = None
                        if meta_div:
                            time_str = meta_div.text.strip().split("•")[-1].strip()
                            today = datetime.now()
                            if "天前" in time_str:
                                try: date_obj = today - dt.timedelta(days=int(time_str.replace("天前", "")))
                                except: pass
                            elif "小時前" in time_str or "分鐘前" in time_str: date_obj = today
                            elif "年" in time_str:
                                try: date_obj = datetime.strptime(time_str.replace("早上","").replace("下午","").replace("晚上","").replace("年","-").replace("月","-").replace("日","").split()[0], "%Y-%m-%d")
                                except: continue
                        if date_obj: append_news(title, full_link, date_obj, "Yahoo", kw)
                    tt.sleep(0.5)
                except: continue

            # --- UDN 爬蟲 ---
            for i in range(len(keywords)):
                try:
                    kw = keywords[i]
                    url = f"https://udn.com/search/word/2/{quote(kw)}"
                    req_obj = req.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                    with req.urlopen(req_obj) as response:
                        data = response.read().decode("utf-8")
                    soup = bs4.BeautifulSoup(data, "html.parser")
                    ti_box = soup.find("div", class_="context-box__content story-list__holder story-list__holder--full")
                    if not ti_box: continue
                    ti_h2 = ti_box.find_all("h2")
                    ti_time = ti_box.find_all("time", class_="story-list__time")
                    for l, title_tag in enumerate(ti_h2):
                        a_tag = title_tag.find("a")
                        if not a_tag or l >= len(ti_time): continue
                        title = a_tag.get_text(strip=True)
                        href = a_tag.get("href")
                        try:
                            date_obj = datetime.strptime(ti_time[l].get_text(strip=True)[:10], "%Y-%m-%d")
                            append_news(title, href, date_obj, "UDN", kw)
                        except: continue
                except: continue

            # --- MoneyDJ 爬蟲 ---
            urls_mdj = [
                ("https://www.moneydj.com/kmdj/common/listnewarticles.aspx?svc=NW&a=X0300023", "能源"),
                ("https://www.moneydj.com/kmdj/common/listnewarticles.aspx?index1=2&svc=NW&a=X0300023", "能源"),
                ("https://www.moneydj.com/kmdj/common/listnewarticles.aspx?svc=NW&a=C0.C099368", "太陽能")
            ]
            for url, cat in urls_mdj:
                try:
                    req_obj = req.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                    with req.urlopen(req_obj) as response:
                        data = response.read().decode("utf-8")
                    soup = bs4.BeautifulSoup(data, "html.parser")
                    ti = soup.find("div", class_="forumgridBox")
                    if not ti: continue
                    titles7 = ti.find_all("td", class_="ArticleTitle")
                    times7 = ti.find_all("td")
                    base_year = datetime.today().year
                    for i, t_tag in enumerate(titles7):
                        if not t_tag.a: continue
                        href = "https://www.moneydj.com/" + t_tag.a.get("href")
                        title = t_tag.a.text.strip().replace("-MoneyDJ理財網", "")
                        try:
                            raw_date = times7[i * 3].text.strip()
                            date_obj = datetime.strptime(f"{base_year}/{raw_date}", "%Y/%m/%d")
                            append_news(title, href, date_obj, "MoneyDJ", cat)
                        except: continue
                except: continue

            # --- 自由時報 ---
            ltn_urls = [
                ("https://news.ltn.com.tw/topic/%E7%B6%A0%E8%83%BD", "綠能"),
                ("https://news.ltn.com.tw/topic/%E5%A4%AA%E9%99%BD%E8%83%BD", "太陽能")
            ]
            for url, cat in ltn_urls:
                try:
                    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
                    soup = BeautifulSoup(res.text, "html.parser")
                    for item in soup.select("ul.list li"):
                        t_tag = item.find("h3", class_="title")
                        time_tag = item.find("span", class_="time")
                        l_tag = item.find("a", class_="tit")
                        if t_tag and time_tag and l_tag:
                            title = t_tag.text.strip()
                            href = "https:" + l_tag["href"] if l_tag["href"].startswith("//") else l_tag["href"]
                            try:
                                date_obj = datetime.strptime(time_tag.text.strip()[:10], "%Y/%m/%d")
                                append_news(title, href, date_obj, "自由時報", cat)
                            except: continue
                except: continue

            # --- ETtoday ---
            for kw in keywords:
                try:
                    u = f"https://www.ettoday.net/news_search/doSearch.php?search_term_string={quote(kw)}"
                    res = requests.get(u, headers={"User-Agent": "Mozilla/5.0"})
                    soup = BeautifulSoup(res.text, "html.parser")
                    for art in soup.select("div.box_2"):
                        h2 = art.find("h2")
                        if not h2 or not h2.find("a"): continue
                        title = h2.find("a").text.strip()
                        href = h2.find("a")["href"]
                        detail = art.find("p", class_="detail")
                        if detail and detail.find("span", class_="date"):
                            raw_text = detail.find("span", class_="date").get_text()
                            try:
                                d_str = raw_text.split("/")[-1].replace(")", "").strip()
                                date_obj = datetime.strptime(d_str, "%Y-%m-%d %H:%M")
                                append_news(title, href, date_obj, "ETtoday", kw)
                            except: continue
                except: continue

            # --- 結果彙整 ---
            if titles:
                df = pd.DataFrame({
                    "日期": dates, "來源": sources, "分類": categories,
                    "包含標題關鍵字": title_keyword_matches, "包含公司關鍵字": company_matches,
                    "標題": titles, "網址": links, "AI 新聞摘要": ""
                }).drop_duplicates(subset=["標題"]).sort_values(by="日期", ascending=False)
                
                # 建立隱藏的原文連結欄位供 UI 顯示
                df["原文連結"] = df["網址"] 
                st.session_state.edited_df = df
                st.success(f"✅ 抓取完成！共 {len(df)} 筆新聞。")
            else:
                st.error("❌ 此日期範圍內查無新聞。")

    st.divider()

    # 步驟二
    st.header("2️⃣ 產生摘要")
    if st.button("🤖 產生摘要", use_container_width=True):
        if not st.session_state.edited_df.empty:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            for idx, row in st.session_state.edited_df.iterrows():
                if not row['AI 新聞摘要']:
                    st.write(f"正在摘要: {row['標題'][:15]}...")
                    text = extract_webpage_text(row['網址'])
                    if text:
                        try:
                            res = client.chat.completions.create(
                                model="gpt-4o-mini",
                                messages=[{"role": "user", "content": f"請以繁體中文摘要約40個字：\n\n{text[:2500]}"}]
                            )
                            st.session_state.edited_df.at[idx, 'AI 新聞摘要'] = res.choices[0].message.content.strip()
                        except: pass
            st.rerun()

    st.divider()

    # 步驟三
    st.header("3️⃣ 正式發信")
    if st.button("📧 分開發送電子報", use_container_width=True):
        if not st.session_state.edited_df.empty:
            if send_split_emails(st.session_state.edited_df):
                st.balloons()
                st.success("✅ 所有信件發送完成！")
        else:
            st.warning("⚠️ 畫面上沒有資料。")

# --- 4. 主畫面 ---
st.write("### 📝 編輯發佈清單")
st.caption("提示：點擊「(查看)」可跳轉原文；選取行並按 Delete 可刪除；公司關鍵字欄位可依據發信需求手動修改。")

if not st.session_state.edited_df.empty:
    st.session_state.edited_df = st.data_editor(
        st.session_state.edited_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "日期": st.column_config.TextColumn("日期", disabled=True),
            "標題": st.column_config.TextColumn("標題", width="large"),
            "原文連結": st.column_config.LinkColumn("連結", display_text="(查看)", width="small"),
            "網址": None, # 隱藏原始網址
            "包含公司關鍵字": st.column_config.TextColumn("公司關鍵字", width="medium"),
            "AI 新聞摘要": st.column_config.TextColumn("AI 新聞摘要", width="large")
        },
        column_order=["日期", "來源", "標題", "原文連結", "包含公司關鍵字", "AI 新聞摘要"]
    )
else:
    st.info("👈 請先從左側執行「步驟一」抓取新聞。")
