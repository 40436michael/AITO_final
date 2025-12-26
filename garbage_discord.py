import os
import discord
import base64
import aiohttp
import requests
from dotenv import load_dotenv

# =============================
# 環境變數
# =============================
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llava:latest")
OLLAMA_URL = "http://localhost:11434/api/generate"

ANYTHINGLLM_API = os.getenv("ANYTHINGLLM_API")
ANYTHINGLLM_API_KEY = os.getenv("ANYTHINGLLM_API_KEY")

HEADERS = {"Authorization": f"Bearer {ANYTHINGLLM_API_KEY}"} if ANYTHINGLLM_API_KEY else {}

# =============================
# Discord 設定
# =============================
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# 使用者目前選擇的 workspace
user_workspaces = {}

# =============================
# AnythingLLM API
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
# Discord Events
# =============================
@client.event
async def on_ready():
    print(f"已登入：{client.user}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    content = message.content.strip()
    if message.content.startswith("!help"):
        embed = discord.Embed(
            title="AnythingLLM Discord Bot 指令列表",
            description="這些是你可以使用的指令：",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="Workspace 管理",
            value=(
                "`!workspaces` → 列出所有可用的 Workspaces\n"
                "`!use <workspace>` → 切換到指定的 Workspace\n"
                "`!whereami` → 顯示目前使用的 Workspace"
            ),
            inline=False
        )

        # 圖片相關指令
        embed.add_field(
            name="🖼 圖片處理",
            value=(
                "`!describe <圖片>` 或 `!描述圖片` → 上傳圖片並生成描述\n"
                "  使用方法：將圖片附加在訊息中並加上指令"
            ),
            inline=False
        )

        embed.add_field(
            name="說明",
            value="`!help` → 顯示這個幫助訊息",
            inline=False
        )

        await message.channel.send(embed=embed)
        return
    # -------------------------
    # 列出 Workspace
    # -------------------------
    if content.startswith("!workspaces"):
        slugs, error = await list_workspaces()
        if error:
            await message.channel.send(error)
        elif slugs:
            await message.channel.send("可用的 Workspaces：\n" + "\n".join(slugs))
        else:
            await message.channel.send("沒有任何 Workspace")
        return

    # -------------------------
    # 切換 Workspace
    # -------------------------
    if content.startswith("!use "):
        ws = content[5:].strip()
        user_workspaces[message.author.id] = ws
        await message.channel.send(f"已切換至 Workspace：**{ws}**")
        return

    # -------------------------
    # 查詢目前 Workspace
    # -------------------------
    if content.startswith("!whereami"):
        ws = user_workspaces.get(message.author.id)
        if ws:
            await message.channel.send(f"你目前的 Workspace：**{ws}**")
        else:
            await message.channel.send("尚未選擇 Workspace，請使用 `!use <workspace>`")
        return

    # -------------------------
    # 圖片 → LLaVA → AnythingLLM
    # -------------------------
    if content.startswith("!describe") or content.startswith("!描述圖片"):
        ws = user_workspaces.get(message.author.id)
        if not ws:
            await message.channel.send("請先用 `!use <workspace>` 選擇 Workspace")
            return

        if not message.attachments:
            await message.channel.send("請上傳要分析的圖片")
            return

        attachment = message.attachments[0]
        img_bytes = await attachment.read()
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")

        await message.channel.send(f"[Workspace: {ws}] 開始分析圖片：{attachment.filename} ...")

        # -------- LLaVA：圖片描述 --------
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
        except Exception as e:
            await message.channel.send(f"[ERROR] 圖片描述失敗：{e}")
            return

        # -------- AnythingLLM：RAG 分類 --------
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

        classification, error = await query_workspace_chat(ws, classification_prompt)

        if error:
            await message.channel.send(f"[ERROR] AnythingLLM 分類失敗：{error}")
            return

        # -------- 回傳結果 --------
        await message.channel.send(
            f"📷 **圖片描述**：\n{image_description}\n\n"
            f"🗑️ **垃圾分類結果**：**{classification}**"
        )


# =============================
# 啟動 Bot
# =============================
if not TOKEN:
    raise RuntimeError("找不到 DISCORD_TOKEN")

client.run(TOKEN)