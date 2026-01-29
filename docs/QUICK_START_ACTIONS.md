# 🚀 GitHub Actions 快速启动（X & YouTube）

## 2 分钟完成配置

### ✅ 步骤 1：添加 GitHub Secrets

进入你的 repository：**Settings → Secrets and variables → Actions → New repository secret**

#### 必需（选一个 LLM）：

```
# 选项 A: Google Gemini（推荐，免费配额高）
Name: GOOGLE_API_KEY
Value: 你的_API_key

# 选项 B: Anthropic Claude（质量最高）
Name: ANTHROPIC_API_KEY
Value: sk-ant-你的_key
```

#### 必需（Telegram）：

```
Name: TELEGRAM_BOT_TOKEN
Value: 123456:ABC-DEF...

Name: TELEGRAM_CHAT_ID
Value: 你的_chat_id
```

#### 可选（YouTube，新功能）：

```
Name: YOUTUBE_API_KEY
Value: AIzaSyC...你的_key
```

💡 **不添加 YouTube key 的影响**：YouTube 数据源会自动跳过，其他功能正常（包括 X/Twitter）

---

### ✅ 步骤 2：启用 Workflow

1. 进入 **Actions** 标签
2. 找到 **"AI News Brief"**
3. 点击 **"Enable workflow"**
4. 点击 **"Run workflow"** 手动测试

---

### ✅ 步骤 3：验证

运行完成后（2-5 分钟）：

1. **Telegram** 检查是否收到消息
2. **查看内容**：
   - ✅ X 推文：来源显示 "X - Sam Altman" 等
   - ✅ YouTube 视频：标题以 🎥 开头
3. **查看日志**：搜索 `x_fetched` 和 `youtube_fetched`

---

## 🎯 已启用的功能

GitHub Actions 配置**已经更新**，包含：

```yaml
ENABLE_X: 'true'           # ✨ X (Twitter) - 无需 API key
ENABLE_YOUTUBE: 'true'     # ✨ YouTube - 需要 API key
ENABLE_RSS: 'true'
ENABLE_REDDIT: 'true'
ENABLE_HACKERNEWS: 'true'
ENABLE_ARXIV: 'true'
ENABLE_BLOGS: 'true'
ENABLE_GITHUB: 'true'
```

运行频率：**每 4 小时一次**

---

## ❓ 常见问题

### Q: X (Twitter) 需要 API key 吗？
**A**: ❌ 不需要！X 使用免费的 Nitter 服务，开箱即用。

### Q: YouTube 是必须的吗？
**A**: ❌ 不是。不配置 `YOUTUBE_API_KEY` 也能运行，只是没有 YouTube 内容。

### Q: 如何获取 YouTube API key？
**A**:
1. [Google Cloud Console](https://console.cloud.google.com/)
2. 创建项目 → 启用 "YouTube Data API v3"
3. 创建 API 密钥

### Q: 配额会用完吗？
**A**: YouTube 每日 10,000 units，每次运行约 100 units，每 4 小时运行一次 = 每天 600 units，配额充足。

### Q: 如何禁用某个数据源？
**A**: 编辑 `.github/workflows/daily-brief.yml`，设置为 `'false'`：
```yaml
ENABLE_X: 'false'          # 禁用 X
ENABLE_YOUTUBE: 'false'    # 禁用 YouTube
```

---

## 🔍 故障排除

### X 没内容：
- 🟢 **正常**：Nitter 实例偶尔不可用，下次运行会恢复
- 📝 查看日志：`all_nitter_instances_failed`

### YouTube 没内容：
- ⚠️ **检查**：`YOUTUBE_API_KEY` secret 是否添加
- 📝 查看日志：`youtube_api_key_missing`
- 🔧 **解决**：添加 secret 后重新运行

### Workflow 失败：
- 📋 查看 Actions 日志中的错误信息
- 🔑 检查所有必需的 secrets 是否正确配置

---

## 📚 详细文档

- [完整 GitHub Actions 配置指南](./GITHUB_ACTIONS_SETUP.md) - 详细的故障排除和配置
- [X & YouTube 设置指南](./X_YOUTUBE_SETUP.md) - 功能说明和最佳实践

---

## ✨ 就这么简单！

配置好后，系统会：
- ⏰ 每 4 小时自动运行
- 📱 发送精选 AI 资讯到 Telegram
- 🐦 包含 X 上的最新讨论（无需配置）
- 🎥 包含 YouTube 视频（如果配置了 API key）
- 📊 包含其他 6 个数据源的内容

**享受自动化的 AI 资讯日报！** 🎉
