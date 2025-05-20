import streamlit as st
import requests
import base64
import mimetypes
from gtts import gTTS
import tempfile
import os

# 🗝️ 載入 Gemini API 金鑰（從 secrets）
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

st.set_page_config(page_title="長者友善標籤小幫手", layout="centered")
st.title("👵 長者友善標籤小幫手")
st.write("上傳商品標籤圖片，我們會幫你解讀成分內容，並提供語音播放。")
uploaded_file = st.file_uploader("請上傳商品標籤圖片（jpg 或 png）", type=["jpg", "png"])

if uploaded_file:
    # 🧊 暫存圖片檔
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
        temp_file.write(uploaded_file.read())
        image_path = temp_file.name

    # 🧠 轉成 base64 並偵測圖片 MIME 類型
    mime_type, _ = mimetypes.guess_type(image_path)
    with open(image_path, "rb") as img_file:
        img_base64 = base64.b64encode(img_file.read()).decode('utf-8')

    # 📜 Gemini Prompt
    prompt_text = """
這是一張商品標籤的圖片，請：

1. 用簡單中文說明它是食品或藥品。
2. 清楚列出以下內容：
   - 類型（食品 / 藥品）
   - 中文名稱（如果有）
   - 主要成分：針對每個成分簡單說明它的用途（例如：增加口感、防腐、代糖等），並指出是否需要特別注意（例如對某些族群不建議、可能引起過敏、實際無健康價值但常被使用）。
3. 使用不超過國中程度的中文說明，適合長者與一般民眾理解。
4. 若可行，請為重要的成分提供簡單的資料來源（如食藥署、WHO 等）。
    """

    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_text},
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": img_base64
                        }
                    }
                ]
            }
        ]
    }

    # 📡 發送 API 請求
    with st.spinner("AI 正在閱讀標籤中，請稍候..."):
        response = requests.post(url, json=payload)

    if response.status_code == 200:
        try:
            text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            st.subheader("📝 成分說明")
            st.write(text)

            # 🎧 語音合成
            tts = gTTS(text, lang='zh-TW')
            temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tts.save(temp_audio.name)

            audio_file = open(temp_audio.name, 'rb')
            st.audio(audio_file.read(), format='audio/mp3')

        except Exception as e:
            st.error(f"✅ 回傳成功但處理失敗：{e}")
    else:
        st.error(f"❌ 發送請求失敗，錯誤碼：{response.status_code}\n內容：{response.text}")