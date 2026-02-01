# LegalMind: AI Legal Intelligence Platform

LegalMind is a Google Cloud-native, multi-agent legal intelligence platform that helps legal teams analyze contracts, research precedent, assess compliance, and generate professional legal memos.

## Highlights

- **Contract analysis** with clause extraction and risk scoring
- **Legal research** grounded via Google Search
- **Compliance checks** for GDPR, HIPAA, CCPA, SOX
- **Transparent reasoning** with thinking logs
- **Document generation** for legal memos and summaries

## Technology Stack

**Backend**
- FastAPI + Python
- Gemini 2.0 Flash (function calling)
- Firestore (sessions, contracts, messages)
- Cloud Storage (PDFs, generated docs)

**Frontend**
- Next.js + React
- Tailwind CSS + shadcn UI

## Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud project
- Gemini API key

### Environment Setup

Create `backend/.env`:

```
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GCS_BUCKET_NAME=legalmind-contracts
FIRESTORE_DATABASE=(default)
```

### Run Backend

```
cd backend
python main_new.py
```

### Run Frontend

```
cd frontend
npm install
npm run dev
```

## Documentation

- docs/PROJECT_STATUS.md
- docs/FRONTEND_INTEGRATION_GUIDE.md
- docs/BACKEND_TEST_RESULTS.md
- docs/BACKEND_COMPLETE_SUMMARY.txt

## License

Apache-2.0. See [LICENSE.md](LICENSE.md).
