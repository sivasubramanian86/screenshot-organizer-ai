@echo off
echo ========================================
echo Setup for AWS Bedrock
echo ========================================
echo.

echo [1/4] Installing Bedrock dependencies...
pip install -r requirements_bedrock.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo ✓ Dependencies installed
echo.

echo [2/4] Configuring AWS CLI...
aws configure
echo ✓ AWS configured
echo.

echo [3/4] Configuring environment...
copy config\.env.bedrock config\.env
echo ✓ Config file created
echo.

echo [4/4] Setup complete!
echo.
echo ========================================
echo Next Steps:
echo ========================================
echo 1. Ensure AWS Bedrock access is enabled in AWS Console
echo 2. Request Claude model access if needed
echo 3. Run: python src\main.py
echo.
echo Cost: ~$2 per 1000 screenshots (no minimum!)
echo ========================================
pause
