@echo off
chcp 65001 >nul
echo ====================================================================
echo 🛠️  AI News Brief - 一键安装
echo ====================================================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：找不到 Python！
    echo.
    echo 请先安装 Python 3.11 或更高版本：
    echo   https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo ✅ Python 已安装
python --version
echo.

REM 创建虚拟环境
if exist "venv\" (
    echo ⚠️  虚拟环境已存在，跳过创建
) else (
    echo 📦 创建虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ 创建虚拟环境失败！
        pause
        exit /b 1
    )
    echo ✅ 虚拟环境创建成功
)
echo.

REM 激活虚拟环境
echo ⚙️  激活虚拟环境...
call venv\Scripts\activate.bat
echo.

REM 升级 pip
echo 📦 升级 pip...
python -m pip install --upgrade pip
echo.

REM 安装依赖
echo 📦 安装依赖包（这可能需要几分钟）...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ❌ 依赖安装失败！
    echo.
    pause
    exit /b 1
)
echo.
echo ✅ 依赖安装成功
echo.

REM 创建 .env 文件
if exist ".env" (
    echo ⚠️  .env 文件已存在，跳过创建
) else (
    echo 📝 创建 .env 配置文件...
    copy .env.example .env >nul
    echo ✅ .env 文件已创建
    echo.
    echo ⚠️  重要：请编辑 .env 文件并填入你的 API keys：
    echo   1. Google API Key: https://aistudio.google.com/app/apikey
    echo   2. Telegram Bot Token: 搜索 @BotFather
    echo   3. Telegram Chat ID: 搜索 @userinfobot
    echo.
)

REM 完成
echo ====================================================================
echo ✅ 安装完成！
echo ====================================================================
echo.
echo 下一步：
echo   1. 编辑 .env 文件填入 API keys
echo      notepad .env
echo.
echo   2. 运行测试
echo      test.bat
echo.
echo   3. 运行程序
echo      run.bat
echo.
echo 📚 详细文档：
echo   - WINDOWS_SETUP.md （Windows 设置指南）
echo   - README.md （完整文档）
echo   - docs\LLM_PROVIDERS.md （LLM 配置指南）
echo.
pause
