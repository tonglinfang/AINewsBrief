# 🚀 快速開始指南

5 分鐘內讓 AI News Brief 運行起來！

## 步驟 1: 獲取 API Keys

### Anthropic API Key

1. 訪問 [Anthropic Console](https://console.anthropic.com/)
2. 登錄或註冊賬號
3. 進入 "API Keys" 頁面
4. 創建新的 API key
5. 複製 key（格式：`sk-ant-...`）

### Telegram Bot

1. 在 Telegram 搜索 [@BotFather](https://t.me/botfather)
2. 發送 `/newbot`
3. 按提示設置 bot 名稱和用戶名
4. 複製 bot token（格式：`123456789:ABC...`）
5. 與你的 bot 開始對話（發送 `/start`）

### Telegram Chat ID

1. 在 Telegram 搜索 [@userinfobot](https://t.me/userinfobot)
2. 向它發送任意消息
3. 它會返回你的 chat ID（一串數字）

## 步驟 2: 本地測試

```bash
# 1. 克隆項目
cd /mnt/e/07.agents/02.AINewsBrief

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 配置環境變量
cp .env.example .env
# 編輯 .env 填入你的 API keys

# 4. 測試設置
python scripts/test_setup.py

# 5. 運行一次完整工作流
python -m src.agent
```

如果一切正常，你會：
- 在終端看到進度日誌
- 在 Telegram 收到簡報消息
- 在 `reports/` 目錄看到生成的 Markdown 文件

## 步驟 3: GitHub Actions 設置

### 3.1 推送代碼到 GitHub

```bash
cd /mnt/e/07.agents/02.AINewsBrief
git init
git add .
git commit -m "Initial commit: AI News Brief system"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

### 3.2 配置 Secrets

在 GitHub repository 頁面：

1. 進入 **Settings** → **Secrets and variables** → **Actions**
2. 點擊 **New repository secret**
3. 添加以下 secrets：

   - **Name**: `ANTHROPIC_API_KEY`
     **Secret**: 你的 Anthropic API key

   - **Name**: `TELEGRAM_BOT_TOKEN`
     **Secret**: 你的 Telegram bot token

   - **Name**: `TELEGRAM_CHAT_ID`
     **Secret**: 你的 Telegram chat ID

### 3.3 啟用 GitHub Actions

1. 進入 **Settings** → **Actions** → **General**
2. 在 "Workflow permissions" 選擇 **Read and write permissions**
3. 保存更改

### 3.4 手動觸發測試

1. 進入 **Actions** 標籤
2. 選擇 "Daily AI News Brief" workflow
3. 點擊 **Run workflow** → **Run workflow**
4. 等待執行完成（約 3-5 分鐘）

如果成功：
- Workflow 狀態為綠色 ✅
- Telegram 收到簡報
- `reports/` 目錄有新文件被提交

## 步驟 4: 享受自動化

從現在開始，系統會：
- 每天 UTC 00:00（北京時間 08:00）自動運行
- 抓取最新 AI 資訊
- 分析並生成簡報
- 發送到你的 Telegram
- 保存到 GitHub repository

## 故障排除

### 本地運行失敗

**問題**: `ModuleNotFoundError`
**解決**: 確保在項目根目錄運行，且已安裝依賴

**問題**: `pydantic.error_wrappers.ValidationError`
**解決**: 檢查 `.env` 文件是否存在且配置正確

**問題**: Telegram 未收到消息
**解決**:
- 確認已與 bot 開始對話
- 檢查 bot token 和 chat ID 是否正確
- 查看終端日誌了解具體錯誤

### GitHub Actions 失敗

**問題**: Workflow 報錯 "Error: Process completed with exit code 1"
**解決**:
- 點擊失敗的 workflow 查看詳細日誌
- 檢查 Secrets 是否正確設置
- 確認 Secrets 名稱完全匹配（區分大小寫）

**問題**: Workflow 無法提交報告
**解決**:
- 檢查 workflow 是否有寫權限
- Settings → Actions → General → Workflow permissions → Read and write

**問題**: Schedule 不觸發
**解決**:
- GitHub Actions 的 cron 可能有延遲（5-15 分鐘）
- 確保 repository 不是私有的，或者有 Actions 使用配額
- 嘗試手動觸發測試

## 自定義配置

編輯 `.env` 文件調整設置：

```env
# 每天最多處理 30 篇文章
MAX_TOTAL_ARTICLES=30

# 只顯示重要性 >= 7 的文章
MIN_IMPORTANCE_SCORE=7

# 只抓取最近 12 小時的文章
ARTICLE_AGE_HOURS=12
```

## 下一步

- 📖 閱讀 [README.md](README.md) 了解詳細功能
- 🛠️ 查看 [CONTRIBUTING.md](CONTRIBUTING.md) 學習如何自定義
- 🐛 遇到問題？查看 GitHub Issues 或創建新 issue

享受你的 AI 資訊日報！🤖✨
