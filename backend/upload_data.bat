REM filepath: c:\Users\vindh\Desktop\grpproject\GeoPulse\backend\upload_data.bat
@echo off
cd /d "C:\Users\vindh\Desktop\grpproject\GeoPulse\backend"

REM Activate the virtual environment
call venv\Scripts\activate.bat

REM Run the Python scripts
python upload_price_local.py >> upload_data.log 2>&1
python upload_news_local.py >> upload_data.log 2>&1

REM Deactivate the virtual environment
deactivate