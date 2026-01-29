# GitHub Actions 配置指南

本指南说明如何在 GitHub Actions 中配置 AI News Brief 自动化运行，包括新添加的 X 和 YouTube 数据源。

---

## 📋 前置准备

1. 将代码推送到 GitHub repository
2. 准备所需的 API keys
3. 配置 GitHub Secrets

---

## 🔑 必需的 GitHub Secrets

在 GitHub repository 设置中添加以下 secrets：

### 步骤：Settings → Secrets and variables → Actions → New repository secret

### 1. LLM Provider（必需，选择一个）

#### 选项 A: Anthropic Claude（推荐）
```
Secret Name: ANTHROPIC_API_KEY
Secret Value: sk-ant-your_key_here
```

#### 选项 B: OpenAI GPT
```
Secret Name: OPENAI_API_KEY
Secret Value: sk-your_key_here
```

#### 选项 C: Google Gemini
```
Secret Name: GOOGLE_API_KEY
Secret Value: your_key_here
```

#### 选项 D: Zhipu AI (GLM)
```
Secret Name: ZHIPU_API_KEY
Secret Value: your_key_here
```

### 2. Telegram Bot（必需）

```
Secret Name: TELEGRAM_BOT_TOKEN
Secret Value: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

Secret Name: TELEGRAM_CHAT_ID
Secret Value: 123456789  或  @your_channel
```

**获取方式**：
- Bot Token: 与 [@BotFather](https://t.me/BotFather) 对话创建 bot
- Chat ID: 发送消息给 [@userinfobot](https://t.me/userinfobot) 获取你的 ID

### 3. YouTube API（可选，新功能）

```
Secret Name: YOUTUBE_API_KEY
Secret Value: AIzaSyC...your_key_here
```

**获取方式**：
1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建项目
3. 启用 "YouTube Data API v3"
4. 创建 API 密钥

**不添加这个 secret 的影响**：
- YouTube 数据源会被自动跳过
- 不影响其他数据源运行
- 日志中会显示 "youtube_api_key_missing"

### 4. Reddit API（可选）

```
Secret Name: REDDIT_CLIENT_ID
Secret Value: your_client_id

Secret Name: REDDIT_CLIENT_SECRET
Secret Value: your_client_secret
```

**不添加的影响**：Reddit 数据源会被跳过

### 5. LLM Provider 选择（可选）

```
Secret Name: LLM_PROVIDER
Secret Value: anthropic  # 或 openai, google, zhipu

Secret Name: LLM_MODEL
Secret Value: claude-sonnet-4-5-20250929  # 或其他模型
```

**默认值**：如果不设置
- Provider: `google`（免费配额最高）
- Model: `gemini-2.0-flash`（速度快，成本低）

---

## ⚙️ GitHub Actions 配置说明

### 当前配置（已更新）

```yaml
# 运行频率：每 4 小时一次
schedule:
  - cron: '0 */4 * * *'  # 00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC

# 数据源开关（已启用 X 和 YouTube）
ENABLE_RSS: 'true'
ENABLE_REDDIT: 'true'
ENABLE_HACKERNEWS: 'true'
ENABLE_ARXIV: 'true'
ENABLE_BLOGS: 'true'
ENABLE_GITHUB: 'true'
ENABLE_X: 'true'           # ✨ 新增
ENABLE_YOUTUBE: 'true'     # ✨ 新增
```

### 调整运行频率

编辑 `.github/workflows/daily-brief.yml`:

```yaml
# 每天一次（每日 8am UTC = 4pm 北京时间）
schedule:
  - cron: '0 8 * * *'

# 每天两次（8am 和 8pm UTC）
schedule:
  - cron: '0 8,20 * * *'

# 每 6 小时一次
schedule:
  - cron: '0 */6 * * *'

# 每 12 小时一次（推荐用于 YouTube 配额管理）
schedule:
  - cron: '0 */12 * * *'
```

### 禁用特定数据源

如果不想使用某个数据源，在 workflow 文件中设置为 `'false'`：

```yaml
ENABLE_X: 'false'          # 禁用 X (Twitter)
ENABLE_YOUTUBE: 'false'    # 禁用 YouTube
```

---

## 🚀 启用 Actions

### 步骤 1: 配置 Secrets

在 repository 中添加所有必需的 secrets（见上文）。

### 步骤 2: 启用 Workflow

1. 进入 repository 的 **Actions** 标签
2. 如果看到提示，点击 **"I understand my workflows, go ahead and enable them"**
3. 找到 **"AI News Brief"** workflow
4. 点击 **"Enable workflow"**

### 步骤 3: 手动测试

首次运行建议手动触发：

1. 进入 Actions → AI News Brief
2. 点击 **"Run workflow"** 按钮
3. 选择 Log level（建议先用 INFO）
4. 点击 **"Run workflow"**
5. 等待运行完成（约 2-5 分钟）

### 步骤 4: 检查结果

运行完成后：
1. 查看 Telegram 是否收到消息
2. 检查 Actions 日志是否有错误
3. 下载 artifacts 查看详细日志

---

## 📊 验证 X 和 YouTube 是否生效

### 方法 1：查看 Telegram 消息

收到的报告中应该包含：
- **X 内容**：来源显示为 "X - Sam Altman"、"X - OpenAI" 等
- **YouTube 内容**：标题以 🎥 开头，来源显示为 "YouTube - Two Minute Papers" 等

### 方法 2：查看 Actions 日志

在 Actions 运行日志中搜索：

```
# X 成功抓取
"fetching_x_posts"
"x_fetched"
"x_total"

# YouTube 成功抓取
"fetching_youtube_videos"
"youtube_fetched"
"youtube_total"
```

如果看到：
```
"youtube_api_key_missing"
```
说明 `YOUTUBE_API_KEY` secret 未配置。

### 方法 3：下载 Artifacts

Actions 运行完成后：
1. 点击运行记录
2. 滚动到底部，找到 **Artifacts** 部分
3. 下载 `workflow-logs-xxx`
4. 检查日志文件中的详细信息

---

## 🔧 故障排除

### 问题 1：X (Twitter) 没有内容

**可能原因**：
- 所有 Nitter 实例临时不可用
- 最近 24 小时内没有 AI 相关推文
- 网络连接问题

**解决方案**：
1. 查看日志中的 `x_fetch_error` 信息
2. 这是正常现象，下次运行通常会恢复
3. X 使用免费的 Nitter，偶尔不可用是预期行为

**日志示例**（正常）：
```json
{
  "event": "x_total",
  "count": 15
}
```

**日志示例**（实例不可用）：
```json
{
  "event": "all_nitter_instances_failed",
  "username": "sama"
}
```

### 问题 2：YouTube 没有内容

**可能原因 A：API Key 未配置**
```json
{
  "event": "youtube_api_key_missing",
  "message": "Skipping YouTube fetch"
}
```

**解决方案**：
1. 在 GitHub Secrets 中添加 `YOUTUBE_API_KEY`
2. 重新运行 workflow

**可能原因 B：API 配额用尽**
```json
{
  "event": "youtube_api_error",
  "status": 403
}
```

**解决方案**：
1. 等待配额重置（每天午夜 Pacific Time）
2. 减少运行频率（改为每 12 小时一次）
3. 在 Google Cloud Console 请求增加配额

**可能原因 C：API 未启用**

**解决方案**：
1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 选择你的项目
3. 进入 APIs & Services → Library
4. 搜索 "YouTube Data API v3"
5. 点击 "Enable"

### 问题 3：Workflow 失败

**查看详细错误**：
1. 进入 Actions → 失败的运行
2. 点击失败的 job
3. 展开失败的 step 查看错误信息

**常见错误**：

**A. Missing API Key**
```
Error: Missing required environment variable: ANTHROPIC_API_KEY
```
**解决**：添加相应的 API key secret

**B. Invalid API Key**
```
Error: Invalid API key provided
```
**解决**：检查 secret 值是否正确复制

**C. Telegram Token Error**
```
Error: Unauthorized
```
**解决**：检查 `TELEGRAM_BOT_TOKEN` 和 `TELEGRAM_CHAT_ID`

### 问题 4：Actions 未自动运行

**可能原因**：
- Workflow 未启用
- Repository 是 fork（forks 默认禁用 scheduled workflows）
- Cron schedule 问题

**解决方案**：
1. 确认 workflow 已启用（Actions → Enable workflow）
2. 如果是 fork，手动触发一次后会启用 schedule
3. 检查 cron 语法是否正确

---

## 🎯 推荐配置

### 配置 A：完整功能（推荐）

**Secrets**：
- ✅ ANTHROPIC_API_KEY 或 GOOGLE_API_KEY
- ✅ TELEGRAM_BOT_TOKEN
- ✅ TELEGRAM_CHAT_ID
- ✅ YOUTUBE_API_KEY（新功能）
- ⚪ REDDIT_CLIENT_ID（可选）
- ⚪ REDDIT_CLIENT_SECRET（可选）

**运行频率**：每 6 小时
```yaml
schedule:
  - cron: '0 */6 * * *'
```

**数据源**：全部启用
```yaml
ENABLE_X: 'true'
ENABLE_YOUTUBE: 'true'
# 其他全部 true
```

### 配置 B：节省 YouTube 配额

**运行频率**：每 12 小时
```yaml
schedule:
  - cron: '0 0,12 * * *'
```

**预期配额使用**：
- 每次运行：~100 units
- 每日运行 2 次：~200 units
- 每日配额：10,000 units
- 剩余配额：充足

### 配置 C：无 YouTube API

如果不想申请 YouTube API key：

**不添加 secret**：
- ❌ YOUTUBE_API_KEY

**Workflow 配置**：
```yaml
ENABLE_YOUTUBE: 'false'  # 显式禁用
```

其他功能（包括 X）正常工作。

---

## 📈 监控和维护

### 每日检查

Actions 会在每日 00:00 UTC 发送健康检查消息到 Telegram：
```
✅ AI News Brief daily health check passed at 2026-01-29.
```

### 失败通知

如果 workflow 失败，会立即发送通知：
```
⚠️ AI News Brief workflow failed at 2026-01-29 10:30 UTC.
Check GitHub Actions for details: [链接]
```

### Artifacts 保留

- **dedup-history**: 30 天（去重历史）
- **workflow-logs**: 7 天（详细日志）

定期下载 artifacts 进行分析或备份。

### 配额监控

**YouTube API**：
- 访问 [Google Cloud Console](https://console.cloud.google.com/)
- APIs & Services → Dashboard
- 查看 YouTube Data API v3 使用情况

---

## 🔐 安全最佳实践

1. **永远不要在代码中硬编码 API keys**
   - ✅ 使用 GitHub Secrets
   - ❌ 不要提交 `.env` 文件

2. **最小权限原则**
   - Telegram Bot 只需要发送消息权限
   - YouTube API Key 可以限制为只能访问 YouTube Data API v3

3. **定期轮换密钥**
   - 每 3-6 个月更换一次 API keys
   - 更新 GitHub Secrets

4. **监控异常使用**
   - 检查 API 配额使用情况
   - 注意失败通知

---

## 📚 相关文档

- [X & YouTube 配置指南](./X_YOUTUBE_SETUP.md)
- [主 README](../README.md)
- [变更日志](../CHANGELOG.md)

---

## ❓ 常见问题

### Q1: 可以完全不用 YouTube API 吗？
**A**: 可以。不配置 `YOUTUBE_API_KEY`，或设置 `ENABLE_YOUTUBE: 'false'`，其他功能正常。

### Q2: X (Twitter) 需要 API key 吗？
**A**: 不需要。X fetcher 使用 Nitter，完全免费，无需配置。

### Q3: 推荐哪个 LLM provider？
**A**:
- **性能最佳**: Anthropic Claude Sonnet 4.5
- **成本最低**: Google Gemini 2.0 Flash（默认）
- **平衡选择**: OpenAI GPT-4o

### Q4: 为什么有时候收不到某些内容？
**A**:
- X: Nitter 实例偶尔不可用（正常现象）
- YouTube: 可能配额用尽或 API 限流
- 其他源: 网络波动或源站问题
- 正常情况下，多数时间可以获取到内容

### Q5: 可以只用 X 和 YouTube，不用其他源吗？
**A**: 可以。在 workflow 中设置：
```yaml
ENABLE_RSS: 'false'
ENABLE_REDDIT: 'false'
ENABLE_HACKERNEWS: 'false'
ENABLE_ARXIV: 'false'
ENABLE_BLOGS: 'false'
ENABLE_GITHUB: 'false'
ENABLE_X: 'true'
ENABLE_YOUTUBE: 'true'
```

---

## 🎉 快速启动检查清单

- [ ] 添加 LLM API key secret（Anthropic/OpenAI/Google/Zhipu 任选一）
- [ ] 添加 Telegram Bot Token 和 Chat ID secrets
- [ ] （可选）添加 YouTube API key secret
- [ ] 启用 GitHub Actions workflow
- [ ] 手动触发第一次运行
- [ ] 检查 Telegram 是否收到消息
- [ ] 查看 Actions 日志确认 X 和 YouTube 是否生效
- [ ] 调整 cron schedule（如果需要）

完成后，你的 AI News Brief 将每 4 小时自动运行一次，包含 X 和 YouTube 的最新内容！🚀
