@echo off
chcp 65001 >nul
echo ====================================================================
echo 🤖 AI News Brief - Starting...
echo ====================================================================
echo.

REM 检查虚拟环境是否存在
if not exist "venv\Scripts\activate.bat" (
    echo ❌ 虚拟环境不存在！
    echo.
    echo 请先运行以下命令创建虚拟环境：
    echo   python -m venv venv
    echo   venv\Scripts\activate.bat
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM 激活虚拟环境
echo ⚙️  激活虚拟环境...
call venv\Scripts\activate.bat

REM 检查 .env 文件是否存在
if not exist ".env" (
    echo.
    echo ⚠️  警告：.env 文件不存在！
    echo.
    echo 请先配置 .env 文件：
    echo   1. copy .env.example .env
    echo   2. 编辑 .env 填入 API keys
    echo.
    pause
    exit /b 1
)

REM 运行程序
echo.
echo 🚀 运行 AI News Brief...
echo ====================================================================
echo.

python -m src.agent

REM 显示结果
echo.
echo ====================================================================
echo ✅ 完成！
echo.
echo 报告已保存到 reports\ 目录
echo.

REM 暂停以查看输出
pause
