# Phase 7 Resources (Deployment + Hardening)

- Sample data bootstrap for local reliability:
  - `src/phases/phase_7/bootstrap_sample_data.py`
- Containerization:
  - `src/phases/phase_7/deploy/Dockerfile.backend`
  - `src/phases/phase_7/deploy/docker-compose.yml`
- FastAPI deployment config:
  - `render.yaml`
- Streamlit backend deployment:
  - `streamlit_app.py`
  - `src/phases/phase_7/deploy/streamlit_backend_app.py`

Run sample bootstrap:

```bash
python -m src.phases.phase_7.bootstrap_sample_data
```

Run Streamlit backend:

```bash
streamlit run streamlit_app.py
```

Run FastAPI backend (for Vercel frontend):

```bash
uvicorn src.phases.phase_4.api:app --reload --host 0.0.0.0 --port 8001
```

Production note:
- Vercel frontend should call FastAPI backend URL, not the Streamlit app URL.
