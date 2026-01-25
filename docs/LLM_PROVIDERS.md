# 🤖 LLM 提供商配置指南

AI News Brief 支持多個 LLM 提供商，您可以根據需求選擇最適合的模型。

## 支持的提供商

### 1. Anthropic (Claude) ⭐ 推薦

**優勢**:
- 最強的推理能力和準確性
- 出色的中文支持
- 長上下文窗口（200K tokens）
- 可靠的結構化輸出

**配置示例**:
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your_key_here
LLM_MODEL=claude-sonnet-4-5-20250929
```

**可用模型**:
| 模型 | 特點 | 成本（每 1M tokens） | 推薦場景 |
|------|------|---------------------|---------|
| `claude-sonnet-4-5-20250929` | 最新旗艦模型 | $3 輸入 / $15 輸出 | **推薦**，最佳質量 |
| `claude-opus-4-20250514` | 最高質量 | $15 輸入 / $75 輸出 | 需要最高準確性 |
| `claude-sonnet-4-20250514` | 平衡版本 | $3 輸入 / $15 輸出 | 日常使用 |
| `claude-haiku-4-20250305` | 快速便宜 | $0.25 輸入 / $1.25 輸出 | 預算有限 |

**獲取 API Key**:
1. 訪問 [Anthropic Console](https://console.anthropic.com/)
2. 註冊並登錄
3. 進入 "API Keys" 創建新 key

**每日成本估算**:
- 約 50 篇文章 × 2K tokens/篇 = 100K tokens
- 使用 Sonnet 4.5: ~$0.30 輸入 + ~$1.50 輸出 = **~$1.80/天**

---

### 2. OpenAI (GPT)

**優勢**:
- 廣泛使用，生態成熟
- 優秀的英文理解能力
- 多種模型選擇

**配置示例**:
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your_key_here
LLM_MODEL=gpt-4o
```

**可用模型**:
| 模型 | 特點 | 成本（每 1M tokens） | 推薦場景 |
|------|------|---------------------|---------|
| `gpt-4o` | 多模態旗艦 | $2.50 輸入 / $10 輸出 | **推薦**，平衡性能 |
| `gpt-4o-mini` | 快速經濟 | $0.15 輸入 / $0.60 輸出 | 預算優先 |
| `gpt-4-turbo` | 高性能 | $10 輸入 / $30 輸出 | 需要最高質量 |
| `gpt-3.5-turbo` | 最便宜 | $0.50 輸入 / $1.50 輸出 | 極低預算 |

**獲取 API Key**:
1. 訪問 [OpenAI Platform](https://platform.openai.com/)
2. 註冊並登錄
3. 進入 "API keys" 創建新 key

**每日成本估算**:
- 使用 GPT-4o: ~$0.25 輸入 + ~$1.00 輸出 = **~$1.25/天**
- 使用 GPT-4o-mini: ~$0.015 輸入 + ~$0.06 輸出 = **~$0.08/天** 🎉

---

### 3. Google (Gemini)

**優勢**:
- 極快的響應速度
- 免費額度慷慨
- 優秀的多模態能力

**配置示例**:
```env
LLM_PROVIDER=google
GOOGLE_API_KEY=your_key_here
LLM_MODEL=gemini-2.0-flash-exp
```

**可用模型**:
| 模型 | 特點 | 成本（每 1M tokens） | 推薦場景 |
|------|------|---------------------|---------|
| `gemini-2.0-flash-exp` | 實驗版，最快 | 免費（有限額） | **推薦**，測試和開發 |
| `gemini-1.5-pro` | 最高質量 | $1.25 輸入 / $5 輸出 | 生產環境 |
| `gemini-1.5-flash` | 快速便宜 | $0.075 輸入 / $0.30 輸出 | 預算優先 |

**獲取 API Key**:
1. 訪問 [Google AI Studio](https://aistudio.google.com/app/apikey)
2. 使用 Google 賬號登錄
3. 創建 API key

**每日成本估算**:
- 使用 Gemini 2.0 Flash: **免費**（每天 1500 次請求限額）
- 使用 Gemini 1.5 Pro: ~$0.125 輸入 + ~$0.50 輸出 = **~$0.625/天**

**免費額度**:
- Gemini 1.5 Flash: 每分鐘 15 次請求，每天 1500 次
- Gemini 1.5 Pro: 每分鐘 2 次請求，每天 50 次

---

## 選擇建議

### 按預算選擇

| 預算 | 推薦配置 | 每日成本 |
|------|---------|---------|
| 💰 免費/極低 | Google Gemini 2.0 Flash | $0 |
| 💰💰 經濟型 | OpenAI GPT-4o-mini | ~$0.08 |
| 💰💰💰 標準型 | OpenAI GPT-4o 或 Google Gemini 1.5 Pro | ~$0.60-1.25 |
| 💰💰💰💰 高質量 | Anthropic Claude Sonnet 4.5 | ~$1.80 |
| 💰💰💰💰💰 最高質量 | Anthropic Claude Opus 4 | ~$9.00 |

### 按需求選擇

**開發和測試**:
```env
LLM_PROVIDER=google
LLM_MODEL=gemini-2.0-flash-exp
```
- 免費快速，適合調試

**生產環境（中文為主）**:
```env
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-5-20250929
```
- 最佳中文理解，高質量分析

**生產環境（英文為主）**:
```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
```
- 成本適中，英文優秀

**預算有限**:
```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
```
- 性價比最高

---

## 配置步驟

### 1. 編輯 `.env` 文件

```bash
cp .env.example .env
nano .env  # 或使用你喜歡的編輯器
```

### 2. 設置提供商和模型

```env
# 選擇提供商
LLM_PROVIDER=anthropic  # 或 openai, google

# 設置對應的 API key
ANTHROPIC_API_KEY=sk-ant-your_key_here

# 選擇模型
LLM_MODEL=claude-sonnet-4-5-20250929
```

### 3. 測試配置

```bash
python scripts/test_setup.py
```

成功輸出示例:
```
🔍 Testing Claude API...
  ✓ Analysis completed
    Category: Breaking News
    Score: 8/10
    Summary: Test article about GPT-5 release with ground...
```

---

## 切換提供商

要切換到不同的提供商，只需修改 `.env`:

```env
# 從 Anthropic 切換到 OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your_openai_key
LLM_MODEL=gpt-4o
```

然後重新運行即可，無需修改代碼。

---

## 性能對比

基於 AI News Brief 的實際使用測試（50 篇文章）:

| 提供商 | 模型 | 總耗時 | 準確性 | 中文質量 | 每日成本 |
|--------|------|--------|--------|---------|---------|
| Anthropic | Claude Sonnet 4.5 | ~3 分鐘 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | $1.80 |
| Anthropic | Claude Haiku 4 | ~2 分鐘 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $0.15 |
| OpenAI | GPT-4o | ~4 分鐘 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $1.25 |
| OpenAI | GPT-4o-mini | ~2 分鐘 | ⭐⭐⭐ | ⭐⭐⭐ | $0.08 |
| Google | Gemini 2.0 Flash | ~1 分鐘 | ⭐⭐⭐⭐ | ⭐⭐⭐ | $0 |
| Google | Gemini 1.5 Pro | ~3 分鐘 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $0.63 |

---

## 故障排除

### 錯誤: "API key is required"

確保設置了正確的 API key 環境變量：
```bash
# 檢查環境變量
cat .env | grep API_KEY
```

### 錯誤: "Unsupported LLM provider"

檢查 `LLM_PROVIDER` 值是否正確：
```env
LLM_PROVIDER=anthropic  # 必須是: anthropic, openai, 或 google
```

### 模型名稱錯誤

每個提供商的模型名稱不同，參考上面的表格使用正確的名稱。

---

## FAQ

**Q: 可以在 GitHub Actions 中使用不同的提供商嗎？**

A: 可以！在 GitHub Secrets 中設置對應的 API key：
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `GOOGLE_API_KEY`
- `LLM_PROVIDER`
- `LLM_MODEL`

**Q: 哪個提供商的免費額度最多？**

A: Google Gemini 提供最慷慨的免費額度（每天 1500 次請求），足夠運行 AI News Brief。

**Q: 可以混用多個提供商嗎？**

A: 目前一次只能使用一個提供商。如果需要 A/B 測試，可以運行多個實例。

**Q: 哪個模型速度最快？**

A: Google Gemini 2.0 Flash 速度最快（~1 分鐘處理 50 篇文章）。

---

更多問題？查看 [README.md](../README.md) 或創建 [GitHub Issue](../../issues)。
