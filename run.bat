@echo off
echo Запуск системы-помощника учителя музыки...
if not exist venv (
    echo Создание виртуального окружения...
    python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt
python app.py
pause
