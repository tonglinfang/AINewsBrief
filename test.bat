@echo off
chcp 65001 >nul
echo ====================================================================
echo 🔍 AI News Brief - Testing Configuration
echo ====================================================================
echo.

REM 检查虚拟环境
if not exist "venv\Scripts\activate.bat" (
    echo ❌ 虚拟环境不存在！
    echo.
    echo 请先运行: python -m venv venv
    echo.
    pause
    exit /b 1
)

REM 激活虚拟环境
echo ⚙️  激活虚拟环境...
call venv\Scripts\activate.bat

REM 运行测试
echo.
echo 🧪 运行测试脚本...
echo ====================================================================
echo.

python scripts\test_setup.py

echo.
echo ====================================================================
pause
