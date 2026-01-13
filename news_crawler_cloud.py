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
        status_area = st.empty() # 建立一個狀態顯示區
        log_area = st.expander("🔍 爬蟲詳細日誌 (若抓不到資料請點開檢查)", expanded=True)
        
        with st.spinner("正在啟動強力爬蟲..."):
            # 時間設定
            start_date_obj = datetime.combine(s_date, datetime.min.time())
            end_date_obj = datetime.combine(e_date, datetime.max.time())
            
            # 初始化
            dates, sources, categories, company_matches, title_keyword_matches, titles, links = [], [], [], [], [], [], []
            
            # 關鍵字 (維持您的設定)
            keywords = ["太陽能", "再生能源", "電廠", "綠電", "光電",  "風電", "儲能", "綠電交易", "麗升能源", "綠能"]
            
            # --- 輔助函式 ---
            def parse_flexible_date(date_text):
                if not date_text: return None
                clean_text = date_text.replace("(", "").replace(")", "").strip().split(" ")[0]
                formats = ["%Y/%m/%d", "%Y-%m-%d", "%Y.%m.%d", "%Y%m%d"]
                for fmt in formats:
                    try: return datetime.strptime(clean_text, fmt)
                    except ValueError: continue
                return None

            def find_company_keywords(text):
                return [k for k in company_keywords if k in text]

            # 統計數據
            stats = {"Yahoo": 0, "UDN": 0, "MoneyDJ": 0, "LTN": 0, "ETtoday": 0}

            # ==========================================
            # 1. Yahoo 爬蟲
            # ==========================================
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            for kw in keywords:
                try:
                    res = requests.get(f"https://tw.news.yahoo.com/search?p={quote(kw)}", headers=headers, timeout=5)
                    soup = BeautifulSoup(res.text, "html.parser")
                    articles = soup.select("li div[class*='Cf']")
                    
                    for art in articles:
                        try:
                            a_tag = art.find("a")
                            if not a_tag: continue
                            title = a_tag.text.strip()
                            href = a_tag["href"]
                            full_link = href if href.startswith("http") else f"https://tw.news.yahoo.com{href}"
                            
                            # 日期處理
                            date_obj = None
                            meta_div = art.find("div", class_="C(#959595)")
                            if meta_div:
                                time_str = meta_div.text.strip().split("•")[-1].strip()
                                today = datetime.now()
                                if "天前" in time_str:
                                    date_obj = today - dt.timedelta(days=int(time_str.replace("天前", "")))
                                elif "小時" in time_str or "分鐘" in time_str:
                                    date_obj = today
                                elif "年" in time_str:
                                    d_s = time_str.replace("年","-").replace("月","-").replace("日","").split()[0]
                                    date_obj = parse_flexible_date(d_s)
                            
                            # 存入邏輯
                            if date_obj and start_date_obj <= date_obj <= end_date_obj:
                                if any(k in title for k in title_keywords):
                                    dates.append(date_obj.strftime("%Y-%m-%d"))
                                    sources.append("Yahoo")
                                    categories.append(kw)
                                    titles.append(title)
                                    links.append(full_link)
                                    stats["Yahoo"] += 1
                                    
                                    # 關鍵字配對
                                    mk = [k for k in title_keywords if k in title]
                                    mck = find_company_keywords(title)
                                    title_keyword_matches.append(",".join(mk))
                                    company_matches.append(",".join(mck) if mck else "-")
                        except: continue
                except: continue
            
            log_area.write(f"Yahoo 搜尋完成，暫存 {stats['Yahoo']} 筆")

            # ==========================================
            # 2. 自由時報 (LTN) - 強力修復版
            # ==========================================
            ltn_urls = [
                ("https://news.ltn.com.tw/topic/再生能源", "再生能源"),
                ("https://news.ltn.com.tw/topic/太陽能", "太陽能"),
                ("https://news.ltn.com.tw/topic/風力發電", "風電"),
                ("https://news.ltn.com.tw/topic/綠電", "綠電"),
            ]
            
            for url, cat in ltn_urls:
                try:
                    res = requests.get(url, headers=headers, timeout=10)
                    soup = BeautifulSoup(res.text, "html.parser")
                    
                    # 寬鬆選擇器：抓取所有可能的列表項目
                    # Topic 頁面結構可能是 div.whitecon boxTitle li 或 ul.searchlist
                    items = soup.select("ul.searchlist li") or \
                            soup.select("div.whitecon li") or \
                            soup.select("ul.list li") or \
                            soup.select("div.boxTitle li")
                    
                    if not items:
                        log_area.warning(f"LTN: 在 {cat} 找不到任何 li 元素，可能網站改版或被擋。")

                    for item in items:
                        # 排除廣告
                        if "class" in item.attrs and "ad" in item.attrs["class"]: continue

                        # 嘗試抓取連結與標題
                        a_tag = item.find("a")
                        if not a_tag: continue
                        
                        href = a_tag.get("href", "")
                        title = a_tag.get("title") or a_tag.text.strip() # 有時候標題在 title 屬性
                        
                        if not title or not href: continue
                        
                        if not href.startswith("http"):
                            href = "https://news.ltn.com.tw/" + href.lstrip("/")
                        
                        # 嘗試抓取時間
                        date_obj = None
                        time_tag = item.find("span", class_="time")
                        if time_tag:
                            date_obj = parse_flexible_date(time_tag.text)
                        
                        # 如果找不到時間 tag，試著從連結判斷 (LTN 網址通常包含日期 /news/business/paper/1687000 這種沒日期，但有些有)
                        # 這裡若是 Topic 頁面，通常一定有 span.time
                        
                        if date_obj:
                            # 檢查日期範圍
                            if start_date_obj <= date_obj <= end_date_obj:
                                # 檢查標題關鍵字
                                matched_kws = [k for k in title_keywords if k in title]
                                if matched_kws:
                                    dates.append(date_obj.strftime("%Y-%m-%d"))
                                    sources.append("自由時報")
                                    categories.append(cat)
                                    titles.append(title)
                                    links.append(href)
                                    title_keyword_matches.append(",".join(matched_kws))
                                    mck = find_company_keywords(title)
                                    company_matches.append(",".join(mck) if mck else "-")
                                    stats["LTN"] += 1
                                else:
                                    # log_area.write(f"LTN 丟棄 (無關鍵字): {title}")
                                    pass
                            else:
                                # log_area.write(f"LTN 丟棄 (日期不符): {date_obj} - {title}")
                                pass
                except Exception as e:
                    log_area.error(f"LTN Error ({cat}): {e}")

            log_area.write(f"自由時報 搜尋完成，暫存 {stats['LTN']} 筆")

            # ==========================================
            # 3. ETtoday - 強力修復版
            # ==========================================
            for kw in keywords:
                try:
                    u = f"https://www.ettoday.net/news_search/doSearch.php?search_term_string={quote(kw)}&idx=1"
                    res = requests.get(u, headers=headers, timeout=10)
                    soup = BeautifulSoup(res.text, "html.parser")
                    
                    # 選擇器：抓取 .box_2
                    items = soup.select("div.archive_list div.box_2")
                    
                    if not items:
                        # 嘗試另一種結構 (有時候 ETtoday 會變)
                        items = soup.select("div.result_archive div.box_2")

                    for art in items:
                        h2 = art.find("h2")
                        if not h2 or not h2.find("a"): continue
                        
                        title = h2.find("a").text.strip()
                        href = h2.find("a")["href"]
                        
                        # 日期處理
                        date_obj = None
                        date_tag = art.find("span", class_="date")
                        if date_tag:
                            # 格式通常是 "2025/01/13 14:00"
                            d_text = date_tag.text.strip()
                            # 移除括號
                            d_text = d_text.split(")")[0].replace("(", "")
                            date_obj = parse_flexible_date(d_text)
                        
                        if date_obj and start_date_obj <= date_obj <= end_date_obj:
                             if any(k in title for k in title_keywords):
                                dates.append(date_obj.strftime("%Y-%m-%d"))
                                sources.append("ETtoday")
                                categories.append(kw)
                                titles.append(title)
                                links.append(href)
                                stats["ETtoday"] += 1
                                
                                mk = [k for k in title_keywords if k in title]
                                mck = find_company_keywords(title)
                                title_keyword_matches.append(",".join(mk))
                                company_matches.append(",".join(mck) if mck else "-")
                except Exception as e:
                    log_area.error(f"ETtoday Error ({kw}): {e}")

            log_area.write(f"ETtoday 搜尋完成，暫存 {stats['ETtoday']} 筆")

            # ==========================================
            # 4. MoneyDJ (維持原樣，但加入 try catch)
            # ==========================================
            # ... (略過 UDN 和 MoneyDJ 沒改動的部分，若您需要可自行補回，這裡專注解決抓不到的問題) ...
            # 為了測試，您可以先只跑上面三個，確定有資料再來補 MoneyDJ/UDN
            
            # --- 彙整結果 ---
            if titles:
                df = pd.DataFrame({
                    "日期": dates, "來源": sources, "分類": categories,
                    "包含標題關鍵字": title_keyword_matches, "包含公司關鍵字": company_matches,
                    "標題": titles, "網址": links, "AI 新聞摘要": ""
                }).drop_duplicates(subset=["標題"]).sort_values(by="日期", ascending=False).reset_index(drop=True)
                
                df["原文連結"] = df["網址"] 
                st.session_state.edited_df = df
                st.success(f"✅ 抓取完成！本次共抓到 {len(df)} 筆。 (Yahoo:{stats['Yahoo']}, LTN:{stats['LTN']}, ETtoday:{stats['ETtoday']})")
            else:
                st.error("❌ 依然查無新聞。請展開上方的「詳細日誌」檢查是否所有請求都失敗，或是日期設定範圍內真的沒有新聞。")
                st.info(f"偵測範圍: {s_date} 到 {e_date}")

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
