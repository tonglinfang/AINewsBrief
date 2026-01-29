# 🤖 AI 資訊日報系統

基於 LangGraph 和 Claude Sonnet 4.5 的自動化 AI 資訊簡報系統，每日抓取、分析和推送最新 AI 資訊到 Telegram。

## ✨ 特性

- **多源抓取**: RSS (TechCrunch, MIT Tech Review 等)、Reddit、HackerNews、ArXiv、AI 公司官方博客、GitHub Releases、**X (Twitter)**、**YouTube**
- **智能分析**: 使用 Claude Sonnet 4.5 / GPT-4 / Gemini / GLM 進行摘要、分類和雙重評分（重要性 + AI 相關性）
- **雙重評分體系**: 同時評估內容重要性（0-10）和 AI 相關性（0-10），確保高質量和高相關性
- **社交媒體監控**: 追蹤 AI 領域意見領袖和公司的 X (Twitter) 動態
- **視頻內容**: 監控頂級 AI YouTube 頻道的最新視頻
- **自動發送**: 每日自動生成 Markdown 簡報並發送到 Telegram
- **GitHub Actions**: 無需服務器，使用 GitHub Actions 自動化執行
- **版本控制**: 所有簡報自動保存到 repository

## 🏗️ 技術架構

- **LangGraph**: 狀態工作流編排
- **多 LLM 支持**: Anthropic Claude / OpenAI GPT / Google Gemini（可配置）
- **Pydantic**: 數據模型和配置管理
- **Python Telegram Bot**: 消息發送
- **GitHub Actions**: 定時任務調度

## 📋 工作流程

```
抓取節點 → 過濾節點 → AI分析節點 → 格式化節點 → 發送節點
```

1. **Fetch**: 並行抓取所有來源的文章
2. **Filter**: 時間過濾、去重、質量檢查
3. **Analyze**: Claude 批量分析文章（摘要、分類、評分、洞察）
4. **Format**: 生成結構化 Markdown 簡報
5. **Send**: 發送到 Telegram 並保存到文件

## 📊 雙重評分體系

系統採用兩個獨立的評分維度來確保內容質量：

### 1. **重要性評分** (Importance Score: 0-10)
評估內容本身的重要程度：
- **9-10分**: 行業突破性進展（如 GPT-5 發布、重大技術突破）
- **7-8分**: 重要新聞或重大研究成果
- **5-6分**: 有價值的更新和進展
- **0-4分**: 一般性內容或次要信息

### 2. **AI 相關性評分** (AI Relevance Score: 0-10)
評估內容與 AI 領域的相關程度：
- **9-10分**: AI 核心技術（新模型架構、訓練方法、LLM、神經網絡）
- **7-8分**: AI 工具/平台/框架（PyTorch、TensorFlow 等）
- **5-6分**: AI 產業動態（融資、政策、市場趨勢）
- **3-4分**: AI 應用案例（醫療、金融等領域應用）
- **0-2分**: 與 AI 幾乎無關

### 過濾策略
只有**同時滿足**兩個條件的文章才會被包含在簡報中：
- 重要性評分 ≥ 5 分（默認，可配置）
- AI 相關性評分 ≥ 5 分（默認，可配置）

這種雙重過濾機制確保推送的內容既**重要**又**相關**，有效過濾掉低質量和非 AI 相關的內容。

## 🚀 快速開始

> 💡 **Windows 用户**？查看 [WINDOWS_SETUP.md](WINDOWS_SETUP.md) 获取详细的 Windows 环境设置指南和一键安装脚本！

### 1. 克隆項目

```bash
git clone <your-repo-url>
cd 02.AINewsBrief
```

### 2. 創建虛擬環境（推薦）

**Linux/Mac**:
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows**:
```powershell
# PowerShell
.\venv\Scripts\Activate.ps1

# 或使用一键安装脚本
setup.bat
```

### 3. 安裝依賴

```bash
pip install -r requirements.txt
```

### 3. 配置環境變量

複製 `.env.example` 到 `.env` 並填入你的 API keys：

```bash
cp .env.example .env
```

編輯 `.env`（選擇一個 LLM 提供商）：

```env
# LLM 配置（選擇一個）
LLM_PROVIDER=anthropic  # 或 openai, google
ANTHROPIC_API_KEY=sk-ant-...

# Telegram 配置
TELEGRAM_BOT_TOKEN=123456789:ABC...
TELEGRAM_CHAT_ID=123456789
```

**支持的 LLM 提供商**:
- **Anthropic Claude** (推薦): 最強推理能力，優秀中文支持
- **OpenAI GPT**: 成熟穩定，多模型選擇
- **Google Gemini**: 快速免費，慷慨額度
- **智谱 AI (GLM)**: 國產大模型，中文優化

詳細配置指南: [docs/LLM_PROVIDERS.md](docs/LLM_PROVIDERS.md)

#### 獲取 LLM API Key

選擇一個 LLM 提供商並獲取 API key:

- **Anthropic**: [console.anthropic.com](https://console.anthropic.com/) → API Keys
- **OpenAI**: [platform.openai.com](https://platform.openai.com/) → API keys
- **Google**: [aistudio.google.com/apikey](https://aistudio.google.com/app/apikey)

📖 詳細說明: [docs/LLM_PROVIDERS.md](docs/LLM_PROVIDERS.md)

#### 獲取 Telegram Bot Token 和 Chat ID

1. **創建 Telegram Bot**:
   - 在 Telegram 中搜索 [@BotFather](https://t.me/botfather)
   - 發送 `/newbot` 並按提示創建 bot
   - 記下 bot token

2. **獲取 Chat ID**:
   - 在 Telegram 中搜索 [@userinfobot](https://t.me/userinfobot)
   - 向它發送任意消息，它會返回你的 chat ID
   - 或者創建一個群組，將 bot 加入群組，使用群組 ID

### 4. 本地測試

```bash
# 運行一次完整工作流
python -m src.agent
```

成功運行後，你應該會在 Telegram 收到簡報，並在 `reports/` 目錄下看到生成的 Markdown 文件。

## ⚙️ GitHub Actions 設置

> 🚀 **快速啟動**：查看 [docs/QUICK_START_ACTIONS.md](docs/QUICK_START_ACTIONS.md) 獲取 2 分鐘快速配置指南（包含 X & YouTube）

### 1. 配置 Secrets

在 GitHub repository 中設置以下 secrets（Settings → Secrets and variables → Actions → New repository secret）：

**必需**:
- LLM API Key（根據選擇的提供商）:
  - `ANTHROPIC_API_KEY` (如果使用 Claude)
  - `OPENAI_API_KEY` (如果使用 GPT)
  - `GOOGLE_API_KEY` (如果使用 Gemini)
- `LLM_PROVIDER`: LLM 提供商（anthropic/openai/google）
- `LLM_MODEL`: 模型名稱（見 [LLM_PROVIDERS.md](docs/LLM_PROVIDERS.md)）
- `TELEGRAM_BOT_TOKEN`: Telegram bot token
- `TELEGRAM_CHAT_ID`: Telegram chat ID

**可選（新功能）**:
- `YOUTUBE_API_KEY`: YouTube Data API v3 密鑰（啟用 YouTube 視頻抓取）✨
- `REDDIT_CLIENT_ID`: Reddit API client ID（如果需要 Reddit 數據）
- `REDDIT_CLIENT_SECRET`: Reddit API client secret（如果需要 Reddit 數據）

> 📖 **詳細配置指南**：[docs/GITHUB_ACTIONS_SETUP.md](docs/GITHUB_ACTIONS_SETUP.md)
> 📖 **X & YouTube 設置**：[docs/X_YOUTUBE_SETUP.md](docs/X_YOUTUBE_SETUP.md)

### 2. 啟用 GitHub Actions

1. 確保 repository 的 Actions 已啟用（Settings → Actions → General → Allow all actions）
2. 確保 workflow 有寫權限（Settings → Actions → General → Workflow permissions → Read and write permissions）
3. X (Twitter) 無需 API key，開箱即用 🎉
4. YouTube 需要 API key（可選，不配置也能運行其他數據源）

### 3. 手動觸發測試

1. 進入 "Actions" 標籤
2. 選擇 "Daily AI News Brief" workflow
3. 點擊 "Run workflow" → "Run workflow"

### 4. 自動執行

Workflow 會在每天 UTC 00:00（北京時間 08:00）自動運行。

## 📁 項目結構

```
02.AINewsBrief/
├── .github/
│   └── workflows/
│       └── daily-brief.yml      # GitHub Actions workflow
├── src/
│   ├── agent.py                 # 主入口
│   ├── config.py                # 配置管理
│   ├── graph/
│   │   ├── state.py            # 狀態定義
│   │   ├── nodes.py            # 5個節點實現
│   │   └── workflow.py         # LangGraph 工作流
│   ├── tools/
│   │   ├── rss_fetcher.py      # RSS 抓取
│   │   ├── api_fetcher.py      # Reddit/HN 抓取
│   │   ├── arxiv_fetcher.py    # ArXiv 抓取
│   │   └── telegram_sender.py  # Telegram 發送
│   ├── models/
│   │   ├── article.py          # Article 模型
│   │   ├── analysis.py         # AnalysisResult 模型
│   │   └── report.py           # DailyReport 模型
│   ├── analyzers/
│   │   └── llm_analyzer.py     # Claude 分析器
│   ├── formatters/
│   │   └── markdown_formatter.py  # Markdown 格式化
│   └── utils/
│       ├── deduplication.py    # 去重邏輯
│       └── report_saver.py     # 報告保存
├── reports/                     # 生成的簡報（自動提交）
├── tests/                       # 測試文件
├── .env.example                 # 環境變量模板
├── .gitignore
├── requirements.txt
├── pyproject.toml
└── README.md
```

## 🔧 配置選項

在 `.env` 中可以配置以下選項：

```env
# 文章數量控制
MAX_TOTAL_ARTICLES=50          # 最多處理的文章數
MAX_ARTICLES_PER_SOURCE=20     # 每個來源最多抓取的文章數
ARTICLE_AGE_HOURS=24           # 只抓取最近 N 小時的文章

# 評分過濾（雙重評分體系）
MIN_IMPORTANCE_SCORE=5         # 最低重要性評分（0-10）
MIN_AI_RELEVANCE_SCORE=5       # 最低 AI 相關性評分（0-10）

# 去重設置
DEDUP_HISTORY_DAYS=30          # 去重歷史記憶天數（1-365）

# Data source toggles
ENABLE_RSS=true                # RSS feeds
ENABLE_REDDIT=true             # Reddit
ENABLE_HACKERNEWS=true         # HackerNews
ENABLE_ARXIV=true              # ArXiv
ENABLE_BLOGS=true              # Official blogs
ENABLE_GITHUB=true             # GitHub releases
ENABLE_X=true                  # X (Twitter)
ENABLE_YOUTUBE=true            # YouTube

# LLM 設置
LLM_PROVIDER=anthropic         # anthropic/openai/google/zhipu
LLM_MODEL=claude-sonnet-4-5-20250929
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=4096

# 時區
TIMEZONE=Asia/Shanghai
```

## 📊 簡報示例

生成的簡報包含：

- 📊 統計信息（總文章數、平均重要性）
- 🔥 Breaking News（重大新聞）
- 🔬 Research（學術研究）
- 🛠️ Tools/Products（工具和產品）
- 💼 Business（商業動態）
- 📚 Tutorial（教程文章）

每篇文章包含：
- ⭐ 重要性星級評分（9+分=5星、7+分=4星、5+分=3星、3+分=2星、其他=1星）
- 標題和來源
- AI 生成的摘要（基於原文內容）
- 💡 關鍵洞察（提煉核心價值）
- 原文鏈接

**評分維度**：
- **重要性評分**（0-10）：內容本身的重要程度
- **AI 相關性評分**（0-10）：與 AI 領域的相關程度
- 只有雙重評分同時 ≥ 5 分的文章才會被包含

## 🧪 測試

```bash
# 安裝開發依賴
pip install -e ".[dev]"

# 運行測試
pytest

# 代碼格式化
black src/ tests/

# Linting
ruff check src/ tests/
```

## 🐛 故障排除

### 1. GitHub Actions 失敗

- 檢查 Secrets 是否正確設置
- 查看 Actions 日誌了解詳細錯誤
- 確保 workflow 有寫權限

### 2. Telegram 未收到消息

- 確認 `TELEGRAM_BOT_TOKEN` 和 `TELEGRAM_CHAT_ID` 正確
- 確保你已經與 bot 開始對話（發送 `/start`）
- 如果使用群組，確保 bot 已加入群組並有發送權限

### 3. 本地運行失敗

- 檢查 `.env` 文件是否存在且配置正確
- 確認 API keys 有效
- 檢查網絡連接

## 📝 自定義

### 添加新的資訊來源

1. 在 `src/tools/` 中創建新的 fetcher
2. 實現 `fetch_all()` 方法返回 `List[Article]`
3. 在 `src/graph/nodes.py` 的 `fetch_news_node` 中添加新 fetcher

### 修改簡報格式

編輯 `src/formatters/markdown_formatter.py` 中的 `TEMPLATE` 字符串。

### 調整分析提示詞

修改 `src/analyzers/llm_analyzer.py` 中的 `SYSTEM_PROMPT` 和 `ANALYSIS_PROMPT_TEMPLATE`。

## 📄 License

MIT

## 🙏 致謝

- [LangGraph](https://github.com/langchain-ai/langgraph) - 工作流編排
- [Anthropic Claude](https://www.anthropic.com) - LLM 分析
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram 集成
