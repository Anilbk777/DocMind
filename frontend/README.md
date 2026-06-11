# DocMind — Frontend

This folder contains the web UI for DocMind. It provides a search interface, document viewer, and a query playground to interact with your indexed documents.

Setup
1. Install dependencies:
   npm install

2. Environment:
   - Copy `.env.example` to `.env` and provide the backend URL, e.g.:
     VITE_BACKEND_URL=http://localhost:8000

3. Start dev server:
   npm run dev

Build
- Build production assets:
  npm run build

Testing & linting
- Run available tests and linters:
  npm test
  npm run lint

Notes
- The frontend expects the backend API to expose routes under `/api/*`. Adjust VITE_BACKEND_URL as needed.
- If you add new API endpoints in the backend, update the frontend services to match.
