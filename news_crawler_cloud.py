if st.button("🚀 執行爬蟲", use_container_width=True):
        # 引入 urllib3 用來關閉 SSL 警告
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        status_area = st.empty() 
        log_area = st.expander("🔍 爬蟲詳細日誌 (若抓不到資料請點開檢查)", expanded=True)
        
        with st.spinner("正在啟動強力爬蟲 (含 UDN)..."):
            # 時間設定
            start_date_obj = datetime.combine(s_date, datetime.min.time())
            end_date_obj = datetime.combine(e_date, datetime.max.time())
            
            # 初始化儲存空間
            dates, sources, categories, company_matches, title_keyword_matches, titles, links = [], [], [], [], [], [], []
            
            # --- 關鍵字定義 ---
            keywords = ["太陽能", "再生能源", "電廠", "綠電", "光電",  "風電", "儲能", "綠電交易", "麗升能源", "綠能"]
            
            title_keywords = ["小水力","光電","綠能","綠電","風能","太陽能","再生","儲能","減碳","ESG","電池","地熱","風力","發電","魚塭","土地","水力","淨零","漁電","光儲","低地力","售電","台電","配電","輸電","升壓","環社","用電大戶","饋線","電表","表前","表後","需量反應","電網","土地開發","電廠","備轉","調頻","PCS","EMS","BMS","電力交易","併網","籌設","風電","電價","電業","香夾蘭","農業補助","CPPA","農電","農業設施許可","沼氣","生質能","Solar","PV","energy","solar","storage","光伏","能源政策","碳權","碳費","躉購","能源署","電業法","躉購費率","漁電共生"]

            company_keywords_raw = ["麗升", "陽光伏特家電力" ,"陽光伏特家" ,"台汽電綠能" ,"台汽電" ,"富威電力" ,"富威" ,"瓦特先生" ,"瓦特先生" ,"南方電力" ,"" ,"花蓮綠能" ,"" ,"石門山新電力" ,"" ,"奇異果新能源" ,"" ,"首美綠能" ,"首美" ,"三地怪獸電力" ,"三地怪獸" ,"樺銳綠電科技" ,"樺銳綠電" ,"星星電力" ,"星星" ,"天能綠電" ,"天能綠電" ,"開陽電力" ,"開陽" ,"博曜電力" ,"博曜" ,"亞福儲能" ,"亞福儲能" ,"莫比綠電" ,"莫比綠電" ,"華城能源" ,"華城" ,"名竣綠能" ,"名竣" ,"大同智能" ,"大同智能" ,"太陽神電力" ,"太陽神" ,"大自然能源電業" ,"大自然能源電業" ,"寶富電力" ,"寶富" ,"中曜" ,"中曜" ,"阿波羅電力" ,"阿波羅" ,"瓦力電能" ,"瓦力電能" ,"陽光綠電" ,"陽光綠電" ,"續興" ,"續興" ,"能元超商" ,"能元超商" ,"台灣碳資產電業" ,"台灣碳資產電業" ,"康展電力" ,"康展" ,"台化綠能" ,"台化" ,"上晟能源科技" ,"上晟能源" ,"晨星電力" ,"晨星" ,"傑傅能源" ,"傑傅" ,"詮實能源" ,"詮實" ,"寶島陽光電力事業" ,"寶島陽光電力事業" ,"誠新電力" ,"" ,"雲豹能源科技" ,"雲豹能源" ,"香印永續" ,"香印永續" ,"義電智慧能源" ,"義電智慧" ,"宇軒電業" ,"宇軒電業" ,"玖暉永續電能" ,"玖暉永續電能" ,"曜越綠電" ,"曜越綠電" ,"艾涅爾電力" ,"艾涅爾" ,"興旺能源" ,"興旺" ,"茂欣能源" ,"茂欣" ,"和同能源" ,"和同" ,"安瑟樂威" ,"安瑟樂威" ,"上集能源" ,"上集" ,"和潤電力" ,"和潤" ,"澎湖綠電" ,"澎湖綠電" ,"禾丰電力" ,"禾丰" ,"新鑫電力" ,"新鑫" ,"台達能源" ,"台達" ,"精華能源" ,"精華" ,"國碩能源" ,"國碩" ,"永餘智能" ,"永餘智能" ,"恆利電能" ,"恆利電能" ,"艾地電力" ,"艾地" ,"新晶太陽光電科技" ,"新晶太陽光電" ,"天勢能源" ,"天勢" ,"承研能源科技" ,"承研能源" ,"統益能源" ,"統益" ,"怡和綠電超商" ,"怡和綠電超商" ,"中華系統整合" ,"中華系統整合" ,"裕鴻能源" ,"裕鴻" ,"明徽電力" ,"明徽" ,"弘昌泰" ,"弘昌泰" ,"昶峰綠能科技" ,"昶峰綠能" ,"成綠能" ,"有成" ,"十萬伏特電力" ,"十萬伏特" ,"友達電力" ,"友達" ,"澤生能源" ,"澤生" ,"光合作用" ,"光合作用" ,"昕明電力" ,"昕明" ,"鴻晶新科技" ,"鴻晶新" ,"毓盈" ,"毓盈" ,"天麋電力" ,"天麋" ,"新光源電力" ,"新光源" ,"恆立能源" ,"恆立" ,"星辰電力" ,"星辰" ,"辰昇能源" ,"辰昇" ,"康誠能源" ,"康誠" ,"寬域能源" ,"寬域" ,"大創電力" ,"大創" ,"太創能源" ,"太創" ,"大猩猩電能交易" ,"大猩猩電能交易" ,"奉天電力" ,"奉天" ,"台灣威迪克艾內斯達能源" ,"台灣威迪克艾內斯達" ,"育成電力" ,"" ,"橙鑫電力" ,"橙鑫" ,"耀鼎資源循環" ,"耀鼎資源循環" ,"中日電力" ,"" ,"茂鴻電力" ,"茂鴻" ,"台灣智能漁電科技" ,"台灣智能漁電" ,"海利普新能源" ,"海利普" ,"特興能源顧問" ,"特興能源顧問" ,"台灣智慧電能" ,"台灣智慧電能" ,"聯旭能源開發" ,"聯旭能源開發" ,"錦振能源" ,"錦振" ,"安能電業" ,"安能電業" ,"金豬能源科技" ,"金豬能源" ,"台塑綠電" ,"台塑綠電" ,"華璽能源" ,"華璽" ,"育渲投資" ,"育渲投資有限公司" ,"歐悅能源" ,"歐悅" ,"庭林" ,"庭林" ,"晟鋐科技" ,"晟鋐科技有限公司" ,"星崴電力" ,"星崴" ,"漢為科技工程" ,"漢為科技工程有限公司" ,"立豐光能" ,"立豐光能" ,"琉璃光綠能" ,"琉璃光" ,"道達爾能源" ,"" ,"東泰綠能投資" ,"東泰綠能投資有限公司" ,"富陽能開發" ,"富陽能開發" ,"偉祥科技" ,"偉祥" ,"凱智綠能科技" ,"凱智綠能" ,"永豐太陽能能源" ,"永豐太陽能能源有限公司" ,"路加太陽能投資顧問" ,"路加太陽能投資顧問" ,"如晅綠能開發" ,"如晅綠能開發有限公司" ,"力山綠能科技" ,"力山綠能科技有限公司" ,"東之億綠能" ,"東之億綠能有限公司" ,"聯宏聚能科技" ,"聯宏聚能科技有限公司" ,"太能系統" ,"太能系統" ,"易晶綠能系統" ,"易晶綠能系統有限公司" ,"永滔綠能" ,"永滔" ,"台灣所樂太陽能科技" ,"台灣所樂太陽能" ,"翰可能源" ,"翰可" ,"和合資源綠能" ,"和合資源綠能有限公司" ,"維知科技" ,"維知【贊助】" ,"加雲聯網" ,"加雲聯網" ,"汎武電機工業" ,"汎武電機工業" ,"前進綠能科技" ,"前進綠能科技有限公司" ,"光旭盈科技" ,"光旭盈" ,"晴棠寬能源工程" ,"晴棠寬能源工程有限公司" ,"凱米克實業" ,"凱米克實業" ,"大日頭" ,"大日頭" ,"新晶光電" ,"新晶光電" ,"恆利能源" ,"恆利" ,"光鼎能源科技" ,"光鼎能源科技有限公司" ,"環亞光電" ,"環亞光電" ,"宣冠" ,"宣冠" ,"衆崴能源" ,"衆崴" ,"樂陽能源" ,"樂陽能源有限公司" ,"台灣和暄綠能" ,"台灣和暄" ,"聖展光能" ,"聖展光能" ,"創睿能源" ,"創睿" ,"百利富能源" ,"百利富" ,"金電發能源" ,"金電發能源有限公司" ,"鼎承能源科技" ,"鼎承能源" ,"昶耀開發" ,"昶耀開發有限公司" ,"星能" ,"星能" ,"日勝再生能源" ,"日勝再生能源有限公司(台灣大根公司集團)" ,"國軒科技" ,"國軒" ,"雲豹能源科技" ,"雲豹能源" ,"昇鈺光電" ,"昇鈺光電" ,"綠順科技" ,"綠順" ,"裕電能源" ,"裕電" ,"暘光綠能實業" ,"暘光綠能實業" ,"凡展綠能科技" ,"凡展綠能" ,"旭誠綠能" ,"旭誠綠能有限公司" ,"大瀚鋼鐵" ,"大瀚鋼鐵" ,"綠葳能源科技" ,"綠葳能源科技有限公司" ,"中租電力科技" ,"中租電力" ,"歐得能源工程" ,"歐得能源工程有限公司" ,"光煜能源" ,"光煜" ,"朝日能源" ,"朝日能源有限公司" ,"嘉毅達光電企業" ,"嘉毅達光電企業" ,"始復能源" ,"始復" ,"銘懋工業" ,"銘懋工業" ,"宇軒鋼鐵工程" ,"" ,"晶成能源" ,"晶成" ,"元晶太陽能科技" ,"元晶太陽能" ,"兆信電通科技" ,"兆信電通科技有限公司" ,"百盛能源科技" ,"百盛能源" ,"禾原新能源科技" ,"禾原新能源" ,"旭天能源" ,"旭天" ,"全日光" ,"全日光有限公司" ,"騰揚綠電" ,"騰揚綠電有限公司" ,"綠農電科" ,"綠農電科" ,"臺鹽綠能" ,"臺鹽" ,"昕毅科技" ,"昕毅科技有限公司" ,"潔力能源事業" ,"潔力能源事業有限公司" ,"茂鴻電力" ,"茂鴻" ,"首美能源" ,"首美" ,"永日昇綠能" ,"永日昇綠能有限公司" ,"夏爾特拉太陽能科技" ,"夏爾特拉太陽能" ,"環球大宇宙太陽能工業" ,"環球大宇宙太陽能工業有限公司" ,"凌積應用科技" ,"凌積應用" ,"崑鼎綠能環保" ,"崑鼎綠能環保" ,"盛齊綠能" ,"盛齊" ,"安哲益工程" ,"安哲益工程" ,"南亞光電" ,"南亞光電" ,"家紳能源" ,"家紳" ,"久研開發節能" ,"久研開發節能有限公司" ,"士能科技" ,"士能科技有限公司" ,"凱煬太陽能" ,"凱煬太陽能" ,"關鍵應用科技" ,"關鍵應用" ,"普晴科技實業" ,"普晴科技實業" ,"向陽優能電力" ,"向陽優能" ,"信邦電子" ,"信邦電子" ,"善騰太陽能源科技商社" ,"善騰太陽能源科技商社" ,"台灣達亨能源科技" ,"台灣達亨能源" ,"天泰能源" ,"天泰" ,"泓筌科技" ,"泓筌" ,"成精密" ,"有成精密" ,"曜昇綠能" ,"曜昇" ,"金陽機電工程" ,"金陽機電工程有限公司" ,"東元電機" ,"東元電機" ,"兆洋太陽能源" ,"兆洋太陽能源有限公司" ,"鑫盈能源" ,"鑫盈" ,"重光電線電纜企業" ,"重光電線電纜企業" ,"統益機電工程" ,"統益機電工程" ,"明軒科技" ,"明軒科技有限公司" ,"紹洲興業" ,"紹洲興業" ,"博盛光電科技" ,"博盛光電科技有限公司" ,"泓德能源科技" ,"泓德能源" ,"綠源科技" ,"綠源" ,"日山能源科技" ,"日山能源科技有限公司"]
            company_keywords = [k.strip() for k in company_keywords_raw if k.strip() != ""]

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
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

            # ==========================================
            # 1. Yahoo 爬蟲
            # ==========================================
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
                            
                            if date_obj and start_date_obj <= date_obj <= end_date_obj:
                                if any(k in title for k in title_keywords):
                                    dates.append(date_obj.strftime("%Y-%m-%d"))
                                    sources.append("Yahoo")
                                    categories.append(kw)
                                    titles.append(title)
                                    links.append(full_link)
                                    stats["Yahoo"] += 1
                                    
                                    mk = [k for k in title_keywords if k in title]
                                    mck = find_company_keywords(title)
                                    title_keyword_matches.append(",".join(mk))
                                    company_matches.append(",".join(mck) if mck else "-")
                        except: continue
                except: continue
            
            log_area.write(f"Yahoo 搜尋完成，暫存 {stats['Yahoo']} 筆")

            # ==========================================
            # 2. UDN 聯合新聞網 (已整合與優化)
            # ==========================================
            for kw in keywords:
                try:
                    # 使用 requests 替代 req (urllib) 以保持一致性和 SSL 處理
                    url = f"https://udn.com/search/word/2/{quote(kw)}"
                    res = requests.get(url, headers=headers, timeout=10)
                    soup = BeautifulSoup(res.text, "html.parser")
                    
                    ti_box = soup.find("div", class_="context-box__content story-list__holder")
                    # 有時候 class 名稱會有點不同，容錯處理
                    if not ti_box:
                        ti_box = soup.find("div", class_="story-list__holder")

                    if not ti_box: continue
                    
                    ti_h2 = ti_box.find_all("h2")
                    ti_time = ti_box.find_all("time", class_="story-list__time")
                    
                    for l, title_tag in enumerate(ti_h2):
                        if l >= len(ti_time): break

                        a_tag = title_tag.find("a")
                        if not a_tag: continue
                        
                        title = a_tag.get_text(strip=True)
                        href = a_tag.get("href")
                        
                        # 日期解析 (使用萬用解析器)
                        date_obj = parse_flexible_date(ti_time[l].get_text(strip=True))
                        
                        if date_obj and start_date_obj <= date_obj <= end_date_obj:
                            if any(k in title for k in title_keywords):
                                dates.append(date_obj.strftime("%Y-%m-%d"))
                                sources.append("UDN")
                                categories.append(kw)
                                titles.append(title)
                                links.append(href)
                                stats["UDN"] += 1
                                
                                mk = [k for k in title_keywords if k in title]
                                mck = find_company_keywords(title)
                                title_keyword_matches.append(",".join(mk))
                                company_matches.append(",".join(mck) if mck else "-")
                except Exception as e:
                    log_area.error(f"UDN Error ({kw}): {e}")

            log_area.write(f"UDN 搜尋完成，暫存 {stats['UDN']} 筆")

            # ==========================================
            # 3. 自由時報 (LTN)
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
                    
                    items = soup.select("ul.searchlist li") or \
                            soup.select("div.whitecon li") or \
                            soup.select("ul.list li") or \
                            soup.select("div.boxTitle li")
                    
                    if not items:
                        log_area.warning(f"LTN: 在 {cat} 找不到任何 li 元素")

                    for item in items:
                        if "class" in item.attrs and "ad" in item.attrs["class"]: continue

                        a_tag = item.find("a")
                        if not a_tag: continue
                        
                        href = a_tag.get("href", "")
                        title = a_tag.get("title") or a_tag.text.strip()
                        
                        if not title or not href: continue
                        if not href.startswith("http"):
                            href = "https://news.ltn.com.tw/" + href.lstrip("/")
                        
                        date_obj = None
                        time_tag = item.find("span", class_="time")
                        if time_tag:
                            date_obj = parse_flexible_date(time_tag.text)
                        
                        if date_obj:
                            if start_date_obj <= date_obj <= end_date_obj:
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
                except Exception as e:
                    log_area.error(f"LTN Error ({cat}): {e}")

            log_area.write(f"自由時報 搜尋完成，暫存 {stats['LTN']} 筆")

            # ==========================================
            # 4. ETtoday (修正 SSL 問題)
            # ==========================================
            for kw in keywords:
                try:
                    u = f"https://www.ettoday.net/news_search/doSearch.php?search_term_string={quote(kw)}&idx=1"
                    # 關鍵修正：加入 verify=False 忽略 SSL 驗證
                    res = requests.get(u, headers=headers, timeout=10, verify=False)
                    soup = BeautifulSoup(res.text, "html.parser")
                    
                    items = soup.select("div.archive_list div.box_2")
                    if not items: items = soup.select("div.result_archive div.box_2")

                    for art in items:
                        h2 = art.find("h2")
                        if not h2 or not h2.find("a"): continue
                        
                        title = h2.find("a").text.strip()
                        href = h2.find("a")["href"]
                        
                        date_obj = None
                        date_tag = art.find("span", class_="date")
                        if date_tag:
                            d_text = date_tag.text.strip().split(")")[0].replace("(", "")
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

            # --- 彙整結果 ---
            if titles:
                df = pd.DataFrame({
                    "日期": dates, "來源": sources, "分類": categories,
                    "包含標題關鍵字": title_keyword_matches, "包含公司關鍵字": company_matches,
                    "標題": titles, "網址": links, "AI 新聞摘要": ""
                }).drop_duplicates(subset=["標題"]).sort_values(by="日期", ascending=False).reset_index(drop=True)
                
                df["原文連結"] = df["網址"] 
                st.session_state.edited_df = df
                st.success(f"✅ 抓取完成！本次共抓到 {len(df)} 筆。 (Yahoo:{stats['Yahoo']}, UDN:{stats['UDN']}, LTN:{stats['LTN']}, ETtoday:{stats['ETtoday']})")
            else:
                st.error("❌ 依然查無新聞。請展開上方的「詳細日誌」檢查。")
                st.info(f"偵測範圍: {s_date} 到 {e_date}")
