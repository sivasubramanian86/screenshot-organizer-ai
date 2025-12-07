@echo off
echo ========================================
echo Screenshot Organizer - Setup and Test
echo ========================================
echo.

echo [1/5] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    echo Make sure Python 3.11+ is installed
    pause
    exit /b 1
)
echo ✓ Virtual environment created
echo.

echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat
echo ✓ Virtual environment activated
echo.

echo [3/5] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo ✓ Dependencies installed
echo.

echo [4/5] Creating necessary directories...
if not exist data mkdir data
if not exist logs mkdir logs
if not exist data\ocr_cache mkdir data\ocr_cache
echo ✓ Directories created
echo.

echo [5/5] Initializing database...
python -c "from src.utils.database import DatabaseManager; from pathlib import Path; db = DatabaseManager(Path('data/screenshots.db')); db.connect(); db.initialize_schema(); print('✓ Database initialized!')"
if errorlevel 1 (
    echo WARNING: Database initialization failed - you may need to configure it manually
)
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Install Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki
echo 2. Copy config\.env.example to config\.env
echo 3. Add your Claude API key to config\.env
echo 4. Run: pytest (to run tests)
echo 5. Run: python src\main.py --dry-run (to test without moving files)
echo.
echo To activate venv later: venv\Scripts\activate.bat
echo.
pause
