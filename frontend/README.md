# New frontend shell

This is a new React/TypeScript/Vite presentation client. It consumes the
versioned `presentation-v1` API and intentionally contains no damage formulas,
Effect matching, or legacy application state.

Development:

```text
uvicorn web.api:app --reload
cd frontend
npm install
npm run dev
```

Vite proxies `/api` to the local FastAPI server. Character images are owned by
the new frontend under `frontend/public/characters`. In a built deployment
FastAPI serves `frontend/dist` from the same origin.
