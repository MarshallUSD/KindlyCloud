# KindlyCloud

KindlyCloud is now organized as a simple monorepo with two top-level folders:

- `frontend/` for the client application
- `backend/` for the FastAPI backend, tests, migrations, and backend docs

## Structure

```text
KindlyCloud/
+-- frontend/
L-- backend/
```

## Backend

The current implementation lives in `backend/`.

Main backend folders:

- `backend/app/`
- `backend/tests/`
- `backend/alembic/`

Useful backend files:

- `backend/config.py`
- `backend/requirements.txt`
- `backend/pytest.ini`
- `backend/alembic.ini`
- `backend/README.md`

## Frontend

The frontend app has not been implemented in this repository yet. Its planned home is `frontend/`.

## Typical Workflow

Activate the existing virtual environment from the repository root:

```powershell
.\venv\Scripts\Activate.ps1
```

Then move into the backend project:

```powershell
cd backend
```

Run the API:

```powershell
uvicorn app.main:app --reload
```

Run tests:

```powershell
pytest -q
```
