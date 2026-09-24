# Creator Support Frontend

React + TypeScript + Vite chat UI for the customer-support intent classifier.

The assistant classifies each user message via the backend `/predict` endpoint and replies with a guided answer based on the predicted intent (access, technical issues, content usage, schedule, etc.).

## Setup

```bash
npm install
```

Create `.env` (already matching `.env.example`):

```text
VITE_API_URL=http://127.0.0.1:8000
```

## Run

Start the backend inference API first, then:

```bash
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

## Features

- modern course-support chat layout
- quick prompts for common course questions
- intent badge on assistant replies
- bilingual replies (Ukrainian / English by user language)
- conversation reset
- CORS-compatible API calls to FastAPI `/predict`
