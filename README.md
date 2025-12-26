# 🗑️ 垃圾分類圖片分析系統

**(LLaVA × AnythingLLM × Streamlit × Discord Bot)**

本專案是一套結合 **視覺理解（LLaVA）** 與 **RAG 知識庫推理（AnythingLLM）** 的垃圾分類系統，
同時提供：

* 🌐 **Web 介面（Streamlit）**

https://github.com/user-attachments/assets/5269f0b8-12ff-4e0b-b4fc-f2ffc59bf91f
* 🤖 **Discord Bot 介面**


https://github.com/user-attachments/assets/784ee485-e18b-4450-89f4-e4ba5cc5fd04


使用者可透過圖片上傳，依據 **垃圾分類規範知識庫（Workspace）** 進行分類推理。

---

## 🧠 系統架構概念

```text
            ┌──────────────┐
            │   使用者     │
            └──────┬───────┘
                   │
        ┌──────────┴──────────┐
        │ Streamlit / Discord │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │  LLaVA (Ollama)     │
        │  圖片 → 文字描述   │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │ AnythingLLM         │
        │ Workspace 知識庫   │
        │ 垃圾分類推理 (RAG) │
        └──────────┬──────────┘
                   │
              分類結果輸出
```

---

## ✨ 功能特色

* 📷 上傳垃圾圖片（jpg / png）
* 🔍 LLaVA 產生**客觀、詳細、不臆測**的圖片描述
* 📚 AnythingLLM Workspace 作為垃圾分類「規範知識庫」
* ♻️ 推理垃圾類型（可回收、一般垃圾、需拆解等）
* 🌐 Streamlit Web UI
* 🤖 Discord Bot 指令操作
* 👤 每位 Discord 使用者可獨立選擇 Workspace

---

## 🛠 系統需求

* Python 3.9+
* Ollama（已安裝 LLaVA 模型）
* AnythingLLM（本機或遠端）
* Discord Bot Token（如使用 Bot）

---

## 📦 安裝套件

```bash
pip install streamlit discord.py aiohttp requests python-dotenv
```

---

## ⚙️ 環境變數設定

在專案根目錄建立 `.env`：

```env
# Discord
DISCORD_TOKEN=你的_Discord_Bot_Token

# Ollama
OLLAMA_MODEL=llava:latest

# AnythingLLM
ANYTHINGLLM_API=http://localhost:3001/api/v1
ANYTHINGLLM_API_KEY=你的_API_KEY
```

### 環境變數說明

| 變數                  | 說明                  |
| ------------------- | ------------------- |
| DISCORD_TOKEN       | Discord Bot Token   |
| OLLAMA_MODEL        | LLaVA 模型名稱          |
| ANYTHINGLLM_API     | AnythingLLM API 位址  |
| ANYTHINGLLM_API_KEY | AnythingLLM API Key |

---

## 📚 AnythingLLM Workspace 說明

Workspace 需包含 **垃圾分類規範知識庫**，例如：

* 各類垃圾分類定義
* 複合材質是否需拆解
* 污染程度（油污 / 殘渣）
* 特殊廢棄物規範

📌 **分類時以 Workspace 知識庫為最高優先依據**

---

# 🌐 Streamlit 圖片分析系統

## 🚀 啟動方式

```bash
streamlit run app.py
```

瀏覽器開啟：

```
http://localhost:8501
```

---

## 🧭 操作流程

### 1️⃣ 載入垃圾分類規範（Workspace）

* 點擊 **「載入 規範」**
* 從下拉選單選擇 Workspace
* 點擊 **「切換 規範」**

---

### 2️⃣ 上傳圖片

* 支援 `jpg / jpeg / png`
* 顯示圖片預覽

---

### 3️⃣ LLaVA 圖片描述

LLaVA 會輸出詳細描述，包括：

* 外觀、顏色、形狀
* 材質（塑膠 / 金屬 / 紙 / 複合）
* 表面狀態（乾淨 / 油污 / 殘渣）
* 可見標誌、文字、透明度

⚠️ **不進行分類、不猜測用途**

---

### 4️⃣ AnythingLLM 分類推理

依據：

* 圖片文字描述
* Workspace 垃圾分類規範
* 材質、清潔度、是否需拆解

輸出分類結果。

---

# 🤖 Discord 垃圾分類 Bot

## 🚀 啟動 Bot

```bash
python bot.py
```

終端機顯示：

```
已登入：BotName#1234
```

---

## 📖 Discord 指令列表

### 🗂 Workspace 管理

| 指令                 | 說明             |
| ------------------ | -------------- |
| `!workspaces`      | 列出所有 Workspace |
| `!use <workspace>` | 切換 Workspace   |
| `!whereami`        | 顯示目前 Workspace |

---

### 🖼 圖片分析

| 指令               | 說明          |
| ---------------- | ----------- |
| `!describe + 圖片` | 上傳圖片並進行垃圾分類 |
| `!描述圖片 + 圖片`     | 中文指令        |

---

### ℹ️ 說明

| 指令      | 說明     |
| ------- | ------ |
| `!help` | 顯示指令說明 |

---

## 🤖 Discord 分析流程

```text
Discord 上傳圖片
        ↓
LLaVA (Ollama) 產生圖片描述
        ↓
AnythingLLM Workspace (RAG)
        ↓
回傳垃圾分類結果
```

---

## ⚠️ 常見問題

### Q1：圖片描述成功，但分類失敗？

* Workspace 無對應規範
* API Key 錯誤
* Workspace slug 錯誤

### Q2：LLaVA 無回應？

* Ollama 未啟動
* 模型名稱錯誤
* 圖片過大或 timeout

---

## 📂 專案結構建議

```text
.
├── app.py        # Streamlit Web App
├── bot.py        # Discord Bot
├── .env
├── README.md
└── requirements.txt
```

---

## 📄 License

MIT License
可自由修改、研究與部署。

---


