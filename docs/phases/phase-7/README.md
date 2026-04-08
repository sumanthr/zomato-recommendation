# Phase 7 Resources (Deployment + Hardening)

- Sample data bootstrap for local reliability:
  - `src/phases/phase_7/bootstrap_sample_data.py`
- Containerization:
  - `src/phases/phase_7/deploy/Dockerfile.backend`
  - `src/phases/phase_7/deploy/docker-compose.yml`
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
