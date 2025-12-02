cd %~dp0
winget install --id Python.Python.3.11
py -3.11 -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements.txt