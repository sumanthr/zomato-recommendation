# Phase 5 Resources (React Frontend)

- Frontend app: `src/phases/phase_5/frontend/`
- API base URL env: `VITE_API_BASE_URL` (default `http://127.0.0.1:8001` for local dev)

Run:

```bash
cd src/phases/phase_5/frontend
npm install
npm run dev
```

## Vercel deployment

Set these project settings in Vercel:
- Root Directory: `src/phases/phase_5/frontend`
- Framework Preset: `Vite`
- Build Command: `npm run build`
- Output Directory: `dist`

Environment variable:
- `VITE_API_BASE_URL=https://<your-fastapi-backend-domain>`

Important:
- Do not point `VITE_API_BASE_URL` to Streamlit app URL. The frontend expects JSON API endpoints (`/localities`, `/dataset-summary`, `/recommendations`) from FastAPI.
