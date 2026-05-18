@echo off
REM RxAccess AI - Automated Setup Script for Windows

echo ========================================
echo RxAccess AI - Automated Setup
echo ========================================
echo.

REM Check Python
echo Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found
    echo Please install Python 3.10 or higher
    pause
    exit /b 1
)
python --version
echo Python OK
echo.

REM Check Tesseract
echo Checking Tesseract OCR...
tesseract --version >nul 2>&1
if errorlevel 1 (
    echo Warning: Tesseract not found
    echo Please install from: https://github.com/UB-Mannheim/tesseract/wiki
    echo.
    set /p continue="Continue anyway? (y/n): "
    if /i not "%continue%"=="y" exit /b 1
) else (
    tesseract --version
    echo Tesseract OK
)
echo.

REM Create virtual environment
echo Creating virtual environment...
if exist venv (
    echo Virtual environment already exists
) else (
    python -m venv venv
    echo Virtual environment created
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo Virtual environment activated
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1
echo Pip upgraded
echo.

REM Install dependencies
echo Installing dependencies...
echo This may take a few minutes...
pip install -r requirements.txt >nul 2>&1
echo Dependencies installed
echo.

REM Create .env file
echo Setting up environment...
if exist .env (
    echo .env file already exists
) else (
    copy .env.example .env >nul
    echo Created .env file
)
echo.

REM Initialize system
echo Initializing system...
python scripts\init_system.py
echo System initialized
echo.

REM Train model
echo Training adherence model...
python scripts\train_adherence_model.py
echo Model trained
echo.

REM Generate synthetic data
echo Generating synthetic prescriptions...
python scripts\generate_synthetic_data.py
echo Synthetic data generated
echo.

REM Final message
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo RxAccess AI is ready to use!
echo.
echo To start the application:
echo   1. Activate virtual environment: venv\Scripts\activate
echo   2. Run: streamlit run streamlit_app\app.py
echo   3. Open browser at: http://localhost:8501
echo.
echo Or use Docker:
echo   docker-compose up --build
echo.
echo Documentation:
echo   - README.md - Full documentation
echo   - QUICKSTART.md - Quick start guide
echo   - PROJECT_SUMMARY.md - Project overview
echo.
echo Remember: This is a prototype for demonstration only!
echo.
pause
