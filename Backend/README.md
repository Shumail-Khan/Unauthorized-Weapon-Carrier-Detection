python -m venv .venv
.venv/Scripts/activate

pip install -r requirements.txt

cd Backend
uvicorn app.main:app --reload --reload-dir app --reload-dir .
