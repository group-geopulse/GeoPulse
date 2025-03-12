REM filepath: c:\Users\vindh\Desktop\grpproject\GeoPulse\backend\upload_data.bat
@echo off
cd /d "C:\Users\vindh\Desktop\grpproject\GeoPulse\backend"
python upload_price.py >> upload_data.log 2>&1
python upload_news.py >> upload_data.log 2>&1