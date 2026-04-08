# Phase 5 Resources (React Frontend)

- Frontend app: `src/phases/phase_5/frontend/`
- API base URL env: `VITE_API_BASE_URL` (default `https://zomato-recommendation.streamlit.app`)

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
- `VITE_API_BASE_URL=https://zomato-recommendation.streamlit.app`
