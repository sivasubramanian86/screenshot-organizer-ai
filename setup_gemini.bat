@echo off
echo ========================================
echo Setup for Google Gemini (FREE)
echo ========================================
echo.

echo [1/3] Installing Gemini dependencies...
pip install -r requirements_gemini.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo ✓ Dependencies installed
echo.

echo [2/3] Configuring environment...
copy config\.env.gemini config\.env
echo ✓ Config file created
echo.

echo [3/3] Setup complete!
echo.
echo ========================================
echo Next Steps:
echo ========================================
echo 1. Get FREE API key: https://makersuite.google.com/app/apikey
echo 2. Edit config\.env and add your GEMINI_API_KEY
echo 3. Run: python src\main.py
echo.
echo Cost: $0 (FREE tier: 1500 requests/day)
echo ========================================
pause
