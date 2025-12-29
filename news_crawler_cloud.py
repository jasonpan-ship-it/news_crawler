import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import gspread
from google.oauth2.service_account import Credentials
import json

# --- 側邊欄核心步驟 ---
with st.sidebar:
    st.title("📑 新聞發佈工作流")

    # --- 步驟一與二 (略) ---
    st.header("1️⃣ 抓取新聞")
    # ... 原有爬蟲代碼 ...
    st.divider()
    
    st.header("2️⃣ 人工審核")
    st.link_button("📂 開啟 Sheets 刪減文章", "你的試算表連結", use_container_width=True)
    st.divider()

    # --- 步驟三：AI 產生摘要 (整合自你的 news2chatgpt.py) ---
    st.header("3️⃣ AI 產生摘要")
    if st.button("🤖 執行 OpenAI 摘要 (逐列處理)", use_container_width=True):
        try:
            # 初始化 Google Sheets (使用 gspread)
            scope = ["https://www.googleapis.com/auth/spreadsheets"]
            service_account_info = json.loads(st.secrets["gcp_service_account"])
            creds = Credentials.from_service_account_info(service_account_info, scopes=scope)
            gc = gspread.authorize(creds)
            
            SPREADSHEET_ID = "1b2UEnsJ0hASkqpR3n9VgfLoIkTRgrHtm8aYbzRho5BA"
            sheet = gc.open_by_key(SPREADSHEET_ID).worksheet("最新新聞")
            
            # 初始化 OpenAI
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            
            rows = sheet.get_all_values()
            st.info(f"檢測到 {len(rows)-1} 筆資料，準備處理未有摘要之項目...")
            
            progress_bar = st.progress(0)
            
            for idx, row in enumerate(rows[1:], start=2):
                url = row[6] if len(row) > 6 else "" # G 欄
                summary = row[7] if len(row) > 7 else "" # H 欄

                if url.strip() and not summary.strip():
                    st.write(f"正在處理第 {idx} 列：{url[:30]}...")
                    
                    # 擷取網頁內容
                    headers = {"User-Agent": "Mozilla/5.0"}
                    resp = requests.get(url, headers=headers, timeout=10)
                    soup = BeautifulSoup(resp.text, "html.parser")
                    
                    # 抓取主體文字 (延用你的邏輯)
                    text = ""
                    for tag in ['article', 'main', 'div']:
                        content = soup.find(tag)
                        if content and len(content.text.strip()) > 200:
                            text = content.get_text(separator="\n", strip=True)
                            break
                    if not text: text = soup.get_text(separator="\n", strip=True)

                    # OpenAI 摘要
                    prompt = f"以下是新聞網頁內容，請以繁體中文條列約40個字的簡短摘要重點：\n\n{text[:3000]}\n\n請產出摘要："
                    completion = client.chat.completions.create(
                        model="gpt-4",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.5,
                    )
                    ai_summary = completion.choices[0].message.content.strip()
                    
                    # 寫回 H 欄 (第 8 欄)
                    sheet.update_cell(idx, 8, ai_summary)
                
                progress_bar.progress(idx / len(rows))
            
            st.success("✅ 所有摘要處理完成！")
            
        except Exception as e:
            st.error(f"❌ 步驟三發生錯誤: {e}")

    st.divider()

    # --- 步驟四：GAS 發信 ---
    st.header("4️⃣ 正式發信")
    if st.button("📧 觸發 GAS 發送信件", use_container_width=True):
        # 原有 requests.get(gas_url) 邏輯
        pass
