import streamlit as st
import os
import base64
import requests
import aiohttp
import asyncio
from dotenv import load_dotenv

# =============================
# 環境變數
# =============================
load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llava:latest")
OLLAMA_URL = "http://localhost:11434/api/generate"

ANYTHINGLLM_API = os.getenv("ANYTHINGLLM_API")
ANYTHINGLLM_API_KEY = os.getenv("ANYTHINGLLM_API_KEY")

HEADERS = {"Authorization": f"Bearer {ANYTHINGLLM_API_KEY}"} if ANYTHINGLLM_API_KEY else {}

# =============================
# Async helpers
# =============================
async def list_workspaces():
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{ANYTHINGLLM_API}/workspaces", headers=HEADERS) as resp:
            if resp.status != 200:
                return None, f"取得 Workspace 失敗 ({resp.status})"
            data = await resp.json()
            slugs = [w.get("slug") for w in data.get("workspaces", []) if w.get("slug")]
            return slugs, None

async def query_workspace_chat(workspace, prompt):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{ANYTHINGLLM_API}/workspace/{workspace}/chat",
            headers=HEADERS,
            json={
                "message": prompt,
                "mode": "chat",
                "returnSourceDocs": False
            }
        ) as resp:
            text = await resp.text()
            if resp.status != 200:
                return None, f"API {resp.status}: {text[:200]}"
            data = await resp.json()
            return data.get("textResponse") or data.get("text"), None

# =============================
# Streamlit App
# =============================
st.title("垃圾分類圖片分析系統")
st.write("上傳圖片，LLaVA 進行描述，AnythingLLM 進行分類推理")

# -----------------------------
# 選擇 Workspace
# -----------------------------
if "workspace" not in st.session_state:
    st.session_state.workspace = None

if st.button("載入 規範"):
    workspaces, error = asyncio.run(list_workspaces())
    if error:
        st.error(error)
    elif workspaces:
        st.session_state.available_workspaces = workspaces
    else:
        st.warning("沒有任何 Workspace")

if "available_workspaces" in st.session_state:
    ws_choice = st.selectbox("選擇 規範", st.session_state.available_workspaces)
    if st.button("切換 規範"):
        st.session_state.workspace = ws_choice
        st.success(f"已切換至 規範：{ws_choice}")

if st.session_state.workspace:
    st.info(f"目前 規範：{st.session_state.workspace}")

# -----------------------------
# 上傳圖片
# -----------------------------
uploaded_file = st.file_uploader("上傳圖片", type=["jpg", "jpeg", "png"])
if uploaded_file and st.session_state.workspace:
    img_bytes = uploaded_file.read()
    img_base64 = base64.b64encode(img_bytes).decode("utf-8")
    st.image(img_bytes, caption="上傳圖片", use_column_width=True)

    st.write("開始分析圖片...")

    # -------- LLaVA 描述 --------
    vision_prompt = (
        "You are a visual understanding model specialized in analyzing waste and trash items. "
        "Your task is not to classify the garbage, but to provide an **objective, highly detailed, "
        "and descriptive analysis** of the item's appearance, material, texture, color, shape, structure, "
        "and cleanliness. Write in English and use complete sentences. Be verbose, descriptive, and comprehensive. "
        "Include details about: "
        "1. Item type and general shape, size, and color. "
        "2. Material composition (single material or composite, presence of coatings, metal, glass, plastic, paper, etc.). "
        "3. Surface condition and cleanliness (clean, slightly dirty, oily, stained, etc.). "
        "4. Any distinguishing features, logos, texts, patterns, or labels visible. "
        "5. Transparency, reflectivity, or texture details. "
        "6. Avoid any guesses about the item's purpose or category, focus only on visible attributes. "
        "Make the description as long and detailed as possible without speculating."
    )

    try:
        ollama_res = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": vision_prompt,
                "images": [img_base64],
                "stream": False
            },
            timeout=120
        )
        ollama_res.raise_for_status()
        image_description = ollama_res.json().get("response", "").strip()
        st.write("📷 **圖片描述**：")
        st.write(image_description)
    except Exception as e:
        st.error(f"LLaVA 圖片描述失敗：{e}")
        image_description = None

    # -------- AnythingLLM 分類 --------
    if image_description:
        classification_prompt = f"""
        你是一個垃圾分類推理模型，負責根據「垃圾圖片的文字描述」，並依照「知識庫中的垃圾分類規則」進行分類推理
        【垃圾描述】
        {image_description}
        【分類原則】
        1. 分類時必須以知識庫中的分類規則為最高優先依據
        2. 若知識庫中未明確定義該物品，請基於垃圾材質、結構與使用狀態進行合理推理
        3. 若物品為複合材質，請判斷是否需要拆解後再分類，並於說明中清楚指出
        4. 若垃圾含有殘渣、油污或液體，請將清潔度納入分類考量
        5. 請避免臆測影像中無法判斷的資訊
        請直接回答分類名稱：可回收物、一般垃圾、廚餘、資源回收、其他特殊廢棄物、需拆解或是知識庫類明確定義分類。
        """.strip()

        classification, error = asyncio.run(query_workspace_chat(st.session_state.workspace, classification_prompt))
        if error:
            st.error(f"AnythingLLM 分類失敗：{error}")
        else:
            st.write("🗑️ **垃圾分類結果**：")
            st.success(classification)
else:
    if not st.session_state.workspace:
        st.warning("請先選擇 Workspace")
