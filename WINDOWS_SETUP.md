# 🪟 Windows 环境设置指南

## 📋 前置要求

- ✅ Python 3.11 或更高版本
- ✅ Git（可选）
- ✅ 文本编辑器（VS Code、Notepad++ 等）

---

## 🚀 快速开始（5 分钟）

### 步骤 1: 打开 PowerShell 或 命令提示符

**方式 1 - PowerShell**（推荐）:
```powershell
# 在项目目录右键 → "在终端中打开"
# 或者手动导航
cd E:\07.agents\02.AINewsBrief
```

**方式 2 - 命令提示符 (cmd)**:
```cmd
cd E:\07.agents\02.AINewsBrief
```

### 步骤 2: 创建虚拟环境

```powershell
# 创建虚拟环境
python -m venv venv
```

如果 `python` 命令不存在，尝试：
```powershell
python3 -m venv venv
# 或者
py -m venv venv
```

### 步骤 3: 激活虚拟环境

**PowerShell**:
```powershell
.\venv\Scripts\Activate.ps1
```

**如果遇到权限错误**，以管理员身份运行 PowerShell 并执行：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
然后重新激活：
```powershell
.\venv\Scripts\Activate.ps1
```

**命令提示符 (cmd)**:
```cmd
venv\Scripts\activate.bat
```

**激活成功标志**：提示符前会显示 `(venv)`：
```
(venv) PS E:\07.agents\02.AINewsBrief>
```

### 步骤 4: 安装依赖

```powershell
# 升级 pip
python -m pip install --upgrade pip

# 安装所有依赖
pip install -r requirements.txt
```

### 步骤 5: 配置环境变量

**方式 1 - 使用记事本**:
```powershell
# 复制模板
copy .env.example .env

# 用记事本打开
notepad .env
```

**方式 2 - 使用 VS Code**:
```powershell
code .env
```

**编辑 `.env` 文件**（推荐使用免费的 Google Gemini）:
```env
# LLM 配置（免费测试）
LLM_PROVIDER=google
GOOGLE_API_KEY=你的_Google_API_Key
LLM_MODEL=gemini-2.0-flash-exp

# Telegram 配置
TELEGRAM_BOT_TOKEN=你的_Bot_Token
TELEGRAM_CHAT_ID=你的_Chat_ID

# 可选：Reddit（留空即可跳过）
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
```

### 步骤 6: 运行测试

```powershell
python scripts\test_setup.py
```

**成功输出示例**:
```
============================================================
AI News Brief - Environment Setup Test
============================================================
🔍 Testing configuration...
  ✓ Config loaded
  ✓ LLM Model: gemini-2.0-flash-exp
  ✓ All required API keys present

🔍 Testing fetchers...
  ✓ RSS: Fetched 15 articles

🔍 Testing Telegram...
  ✓ Connected to bot: @YourBot
  ✓ Test message sent

🔍 Testing LLM API...
  ✓ Analysis completed

============================================================
Summary
============================================================
✅ All tests passed! Your environment is ready.
```

### 步骤 7: 运行完整工作流

```powershell
python -m src.agent
```

---

## 📝 常用命令（Windows）

### 激活/退出虚拟环境

```powershell
# 激活虚拟环境（每次打开新终端都需要）
.\venv\Scripts\Activate.ps1      # PowerShell
# 或
venv\Scripts\activate.bat          # cmd

# 退出虚拟环境
deactivate
```

### 运行项目

```powershell
# 1. 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 2. 测试配置
python scripts\test_setup.py

# 3. 运行一次完整流程
python -m src.agent
```

### 查看生成的报告

```powershell
# 查看报告目录
dir reports

# 用记事本打开最新报告
notepad reports\ai-news-brief-2026-01-24.md
```

---

## 🔑 获取 API Keys

### 1. Google API Key（免费，推荐）

1. 访问 https://aistudio.google.com/app/apikey
2. 登录 Google 账号
3. 点击 "Create API key"
4. 复制 key（格式：`AIza...`）

**免费额度**：
- 每天 1500 次请求
- 足够运行 AI News Brief

### 2. Telegram Bot Token

1. 打开 Telegram，搜索 `@BotFather`
2. 发送 `/newbot`
3. 按提示输入 bot 名称和用户名
4. 复制 token（格式：`123456:ABC-DEF...`）
5. 找到你的 bot 并发送 `/start`

### 3. Telegram Chat ID

1. 打开 Telegram，搜索 `@userinfobot`
2. 向它发送任意消息
3. 它会返回你的 chat ID（一串数字）

---

## 🐛 常见问题

### 问题 1: PowerShell 脚本执行权限错误

**错误信息**:
```
无法加载文件 ...\Activate.ps1，因为在此系统上禁止运行脚本
```

**解决方案**:
```powershell
# 以管理员身份运行 PowerShell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 问题 2: python 命令不存在

**错误信息**:
```
'python' 不是内部或外部命令
```

**解决方案**:
尝试以下命令之一：
```powershell
python3 -m venv venv
# 或
py -m venv venv
```

### 问题 3: 找不到 pip

**解决方案**:
```powershell
python -m ensurepip --upgrade
python -m pip install --upgrade pip
```

### 问题 4: 安装依赖时出错

**解决方案**:
```powershell
# 清除缓存重新安装
pip cache purge
pip install -r requirements.txt
```

### 问题 5: 中文乱码

**解决方案**:
在 PowerShell 执行：
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

或在脚本开头添加：
```powershell
chcp 65001
```

---

## 📁 Windows 批处理脚本

为方便使用，可以创建批处理脚本：

### `run.bat`（一键运行）

创建文件 `run.bat`：
```batch
@echo off
echo 🤖 AI News Brief - Starting...
echo.

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 运行程序
python -m src.agent

REM 暂停以查看输出
pause
```

**使用方法**：双击 `run.bat` 文件即可运行

### `test.bat`（测试配置）

创建文件 `test.bat`：
```batch
@echo off
echo 🔍 AI News Brief - Testing Configuration...
echo.

call venv\Scripts\activate.bat
python scripts\test_setup.py

pause
```

---

## 🎯 完整设置流程总结

```powershell
# 1. 打开 PowerShell，导航到项目目录
cd E:\07.agents\02.AINewsBrief

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 4. 安装依赖
pip install -r requirements.txt

# 5. 配置环境变量
copy .env.example .env
notepad .env
# 填入：GOOGLE_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

# 6. 测试配置
python scripts\test_setup.py

# 7. 运行程序
python -m src.agent
```

---

## 📊 目录结构（Windows 路径）

```
E:\07.agents\02.AINewsBrief\
├── venv\                        虚拟环境
├── src\                         源代码
│   ├── agent.py                主程序
│   ├── config.py               配置
│   ├── graph\                  工作流
│   ├── tools\                  工具
│   └── ...
├── reports\                     生成的报告
├── .env                        环境变量（需要创建）
├── requirements.txt            依赖列表
└── README.md                   文档
```

---

## 🚀 推荐工具

### VS Code（推荐）

1. 安装 VS Code: https://code.visualstudio.com/
2. 安装 Python 扩展
3. 打开项目文件夹
4. 在 VS Code 终端中运行命令

### Windows Terminal（推荐）

1. 从 Microsoft Store 安装 Windows Terminal
2. 更好的终端体验
3. 支持多标签页

---

## 📚 下一步

1. ✅ 完成上述设置
2. ✅ 配置 `.env` 文件
3. ✅ 运行测试验证
4. ✅ 运行一次完整流程
5. 🚀 部署到 GitHub Actions（可选）

---

## 💡 提示

- **每次使用前**记得激活虚拟环境
- **第一次运行**可能需要几分钟下载和分析文章
- **生成的报告**保存在 `reports\` 目录
- **遇到问题**查看本文档的"常见问题"部分

---

需要帮助？查看 [README.md](README.md) 或 [docs\LLM_PROVIDERS.md](docs\LLM_PROVIDERS.md)

祝使用愉快！🎉
