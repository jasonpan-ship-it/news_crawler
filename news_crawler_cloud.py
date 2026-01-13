import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
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

def build_html_body(title_text, df, show_company_col=True):
    """
    建立符合您格式要求的 HTML 表格
    show_company_col: 控制是否顯示「公司」欄位
    """
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

        # 公司關鍵字顯示處理
        comp_kw = row.get('包含公司關鍵字', '-')
        if pd.isna(comp_kw) or comp_kw == "": comp_kw = "-"

        # 根據參數決定是否產生公司欄位的 HTML
        company_td = f"<td style='border:1px solid #333; padding:8px;'>{comp_kw}</td>" if show_company_col else ""

        html_rows += f"""
        <tr>
            <td style='border:1px solid #333; padding:8px;'>{d_str}</td>
            <td style='border:1px solid #333; padding:8px;'><a href='{row['網址']}'>{row['標題']}</a></td>
            {company_td}
            <td style='border:1px solid #333; padding:8px;'>{row.get('AI 新聞摘要', '')}</td>
        </tr>"""
    
    # 表頭處理：根據參數決定是否顯示「公司」表頭
    company_th = '<th style="width:10%;">公司</th>' if show_company_col else ''
    
    # 調整摘要欄位寬度 (如果隱藏公司欄，摘要欄可以寬一點)
    summary_width = "60%" if show_company_col else "70%"

    table_html = f"""
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; font-size: 14px; border: 1px solid #333;">
        <thead><tr style="background-color: #f2f2f2; text-align: left;">
            <th style="width:5%;">日期</th>
            <th style="width:25%;">標題</th>
            {company_th}
            <th style="width:{summary_width};">AI摘要</th>
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

    # 設定顯示名稱
    SENDER_NAME = "每日新聞小幫手" 
    RECEIVER_NAME = "麗升能源集團" 

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
            
            # 發送 Group A: 競業新聞 (顯示公司欄位)
            if not group_a.empty:
                msg = MIMEMultipart()
                msg['Subject'] = f"{today_str} 競業新聞整理"
                msg['From'] = formataddr((str(Header(SENDER_NAME, 'utf-8')), sender))
                msg['To'] = formataddr((str(Header(RECEIVER_NAME, 'utf-8')), receiver))
                
                # show_company_col=True -> 顯示公司欄位
                msg.attach(MIMEText(build_html_body("本日競業新聞整理如下：", group_a, show_company_col=True), 'html'))
                server.send_message(msg)
                st.toast(f"✅ 競業新聞 ({len(group_a)} 封) 已發送")

            # 發送 Group B: 產業新聞 (隱藏公司欄位)
            if not group_b.empty:
                msg = MIMEMultipart()
                msg['Subject'] = f"{today_str} 產業新聞整理"
                msg['From'] = formataddr((str(Header(SENDER_NAME, 'utf-8')), sender))
                msg['To'] = formataddr((str(Header(RECEIVER_NAME, 'utf-8')), receiver))
                
                # show_company_col=False -> 隱藏公司欄位
                msg.attach(MIMEText(build_html_body("本日產業新聞整理如下：", group_b, show_company_col=False), 'html'))
                server.send_message(msg)
                st.toast(f"✅ 產業新聞 ({len(group_b)} 封) 已發送")
        return True
    except Exception as e:
        st.error(f"發信失敗: {e}")
        return False

# --- 3. 側邊欄 ---
with st.sidebar:
    st.title("⚡ 綠能新聞爬蟲")
    
    st.header("1️⃣ 抓取新聞資料")
    today_dt = pd.Timestamp.now().normalize()
    last_bus_day = (today_dt - BusinessDay(1)).to_pydatetime()
    s_date = st.date_input("開始日期", last_bus_day)
    e_date = st.date_input("結束日期", today_dt)
    
    if st.button("🚀 執行爬蟲", use_container_width=True):
        with st.spinner("正在努力的爬..."):
            start_date_obj = datetime.combine(s_date, datetime.min.time())
            end_date_obj = datetime.combine(e_date, datetime.max.time())
            
            # 初始化儲存列表
            dates, sources, categories, company_matches, title_keyword_matches, titles, links = [], [], [], [], [], [], []
            
            # 關鍵字設定
            keywords = ["太陽能", "再生能源", "電廠", "綠電", "光電",  "風電", "儲能", "綠電交易", "麗升能源", "綠能"]
            
            # (在此省略您原本冗長的 company_keywords 定義，請保留您原本的列表)
            # 假設這裡有您的 company_keywords 與 title_keywords...
            # 為了讓程式碼簡潔，我直接沿用您原本的 append_news 函式邏輯
            
            def find_company_keywords(text):
                return [k for k in company_keywords if k in text]

            def append_news(title, url, date_obj, source, category):
                if start_date_obj <= date_obj <= end_date_obj:
                    # 檢查標題關鍵字
                    matched_title_keywords = [k for k in title_keywords if k in title]
                    if not matched_title_keywords:
                        return
                    
                    # 檢查公司關鍵字
                    matched_company_keywords = find_company_keywords(title)
                    
                    dates.append(date_obj.strftime("%Y-%m-%d"))
                    sources.append(source)
                    categories.append(category)
                    title_keyword_matches.append(", ".join(matched_title_keywords))
                    company_matches.append(", ".join(matched_company_keywords) if matched_company_keywords else "-")
                    titles.append(title)
                    links.append(url)

            # --- 1. Yahoo 爬蟲 (維持原樣) ---
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

            # --- 2. UDN 爬蟲 (維持原樣) ---
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

            # --- 3. MoneyDJ 爬蟲 (維持原樣) ---
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

            # --- 4. 自由時報 (LTN) 修復版 ---
            # 定義 LTN 的目標網址 (補上這段)
            ltn_urls = [
                ("https://news.ltn.com.tw/topic/再生能源", "再生能源"),
                ("https://news.ltn.com.tw/topic/太陽能", "太陽能"),
                ("https://news.ltn.com.tw/topic/風力發電", "風電"),
                ("https://news.ltn.com.tw/topic/綠電", "綠電"),
            ]

            for url, cat in ltn_urls:
                try:
                    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                    soup = BeautifulSoup(res.text, "html.parser")
                    
                    # LTN 結構更新：優先抓 ul.searchlist (列表頁常見)，其次抓 ul.tag_focus
                    items = soup.select("ul.searchlist li") or soup.select("ul.tag_focus li") or soup.select("ul.list li")
                    
                    for item in items:
                        # 排除廣告
                        if "class" in item.attrs and "ad" in item.attrs["class"]:
                            continue

                        # 嘗試抓標題 (結構可能是 h3 或 div.tit)
                        t_tag = item.find("h3") or item.find("div", class_="tit")
                        l_tag = item.find("a")
                        time_tag = item.find("span", class_="time")
                        
                        if t_tag and l_tag:
                            title = t_tag.get_text(strip=True)
                            href = l_tag["href"]
                            if not href.startswith("http"):
                                href = "https://news.ltn.com.tw/" + href.lstrip("/")
                            
                            # 日期解析
                            try:
                                if time_tag:
                                    date_str = time_tag.text.strip().split()[0] # 取出 2025/01/13
                                    date_obj = datetime.strptime(date_str, "%Y/%m/%d")
                                    append_news(title, href, date_obj, "自由時報", cat)
                            except:
                                continue
                except Exception as e:
                    print(f"LTN Error: {e}")

            # --- 5. ETtoday 修復版 ---
            for kw in keywords:
                try:
                    # 使用 idx=1 強制進入列表模式
                    u = f"https://www.ettoday.net/news_search/doSearch.php?search_term_string={quote(kw)}&idx=1"
                    res = requests.get(u, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                    soup = BeautifulSoup(res.text, "html.parser")
                    
                    # ETtoday 列表結構通常在 .archive_list 內的 .box_2
                    # 必須確認 h2 存在 (有時候會有廣告插在裡面)
                    articles = soup.select("div.archive_list div.box_2")
                    
                    for art in articles:
                        h2 = art.find("h2")
                        if not h2 or not h2.find("a"): continue
                        
                        title = h2.find("a").text.strip()
                        href = h2.find("a")["href"]
                        
                        date_tag = art.find("span", class_="date")
                        if date_tag:
                            # 格式: "2025/01/13 10:00)" 或 "2025/01/13 10:00"
                            try:
                                d_str = date_tag.text.strip()
                                # 移除可能存在的括號或多餘文字
                                d_str = d_str.replace("(", "").replace(")", "").split(" ")[0] # 只取日期部分 yyyy/mm/dd
                                date_obj = datetime.strptime(d_str, "%Y/%m/%d")
                                append_news(title, href, date_obj, "ETtoday", kw)
                            except:
                                continue
                except Exception as e:
                    print(f"ETtoday Error: {e}")

            # --- 6. 行政院公報 (暫時略過) ---
            # try:
            #     # (原代碼已註解)
            #     pass
            # except Exception as e:
            #     pass

            # --- 結果彙整 ---
            if titles:
                df = pd.DataFrame({
                    "日期": dates, "來源": sources, "分類": categories,
                    "包含標題關鍵字": title_keyword_matches, "包含公司關鍵字": company_matches,
                    "標題": titles, "網址": links, "AI 新聞摘要": ""
                }).drop_duplicates(subset=["標題"]).sort_values(by="日期", ascending=False).reset_index(drop=True)
                
                # 建立隱藏的原文連結欄位供 UI 顯示
                df["原文連結"] = df["網址"] 
                st.session_state.edited_df = df
                st.success(f"✅ 抓取完成！共 {len(df)} 筆新聞。")
            else:
                st.error("❌ 此日期範圍內查無新聞。")

    # 步驟二
    st.header("2️⃣ 產生AI摘要")
    if st.button("點我", use_container_width=True):
        if not st.session_state.edited_df.empty:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            for idx, row in st.session_state.edited_df.iterrows():
                if not row['AI 新聞摘要']:
                    st.write(f"摘要產生中: {row['標題'][:15]}...")
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
    if st.button("發信給全公司", use_container_width=True):
        if not st.session_state.edited_df.empty:
            if send_split_emails(st.session_state.edited_df):
                st.balloons()
                st.success("✅ 所有信件發送完成！")
        else:
            st.warning("⚠️ 畫面上沒有資料。")

# --- 4. 主畫面 ---
st.write("### 📝 編輯發佈清單")
st.caption("提示：選取行並按 Delete 可刪除；欄位可依據發信需求手動修改，有公司關鍵字的會發在「競業新聞」、沒關鍵字的會發在「產業新聞」。")

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
