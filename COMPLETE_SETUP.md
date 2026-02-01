# LegalMind - Complete Setup Guide

## ✅ System Status: FULLY OPERATIONAL

Your LegalMind legal contract analysis platform is now fully configured and running!

### 🚀 Live Services

| Service | URL | Status |
|---------|-----|--------|
| **Frontend (Web App)** | http://localhost:3000 | ✅ Running |
| **Backend API** | http://localhost:8000 | ✅ Running |
| **API Documentation** | http://localhost:8000/docs | ✅ Available |
| **Google Firestore** | legalmind-486106 | ✅ Connected |

---

## 📋 Project Architecture

### Technology Stack
- **Frontend**: Next.js 15 + React 18 + TypeScript + Tailwind CSS
- **Backend**: FastAPI + Python 3.11
- **AI Model**: Google Gemini 2.0 Flash with function calling
- **Database**: Google Cloud Firestore (Native mode)
- **Storage**: Google Cloud Storage
- **Theme**: Professional legal blue (`oklch(0.45 0.16 250)`)

### Backend Features
- 6 specialized legal agents (contract parsing, compliance checking, risk assessment, etc.)
- 14+ legal analysis tools (clause extraction, compliance checking, risk scoring, etc.)
- Real-time chat with WebSocket support
- Session management with Firestore
- PDF contract upload and processing
- Thinking logs for agent reasoning transparency

### Frontend Features
- Interactive chat interface with file upload
- Contract management (upload, list, detail, download)
- Dashboard with country risk heatmap
- Compliance checking interface
- Risk assessment viewer
- Document generation and export

---

## 🔑 Configuration Files

### `.env.local` (Backend Secrets)
Location: `backend/.env.local`

Contains:
- `GEMINI_API_KEY` - Your Google Generative AI API key
- `GOOGLE_CLOUD_PROJECT` - Project ID: `legalmind-486106`
- Application settings (debug mode, environment, etc.)

**Security Note**: This file is in `.gitignore` and is never committed to version control.

### Firestore Security Rules
Location: `backend/firestore.rules`

Current rules allow all reads/writes for development. For production, use the commented-out rules that require authentication.

---

## 🏃 Running the Project

### Start Backend
```bash
cd backend
python main_new.py
```
- Reads credentials from `backend/.env.local`
- Automatically loads `.env` as fallback
- Connects to Firestore project: `legalmind-486106`

### Start Frontend
```bash
cd frontend
npm run dev
```
- Available at http://localhost:3000
- Proxies API calls to backend at http://localhost:8000

### Run Both (Recommended)
Open two terminals and run both commands simultaneously.

---

## 📚 API Documentation

Interactive API docs available at: **http://localhost:8000/docs**

### Key Endpoints

**Chat**
- `GET /api/chat/sessions` - List all chat sessions
- `POST /api/chat/session` - Create new session
- `POST /api/chat` - Send message to agents
- `WebSocket /ws/chat/{session_id}` - Real-time chat

**Contracts**
- `POST /api/contracts/upload` - Upload contract PDF
- `GET /api/contracts` - List contracts
- `GET /api/contracts/{id}` - Get contract details
- `GET /api/contracts/{id}/clauses` - Extract clauses
- `GET /api/contracts/{id}/download` - Download contract

**Compliance**
- `GET /api/compliance/frameworks` - Available frameworks
- `GET /api/compliance/check/{contract_id}` - Check compliance

**Risk Assessment**
- `GET /api/risk/assess/{contract_id}` - Assess contract risks

**Agents**
- `GET /api/agents` - List available agents
- `GET /api/agents/{id}` - Get agent details

---

## 🔐 Google Cloud Setup Details

### Project Information
- **Project Name**: LegalMind
- **Project ID**: legalmind-486106
- **Project Number**: 677928716377
- **Firestore Database**: (default)
- **Edition**: Standard Edition
- **Mode**: Firestore Native
- **Location**: Multi-region (nam5 - United States)
- **Availability SLA**: 99.999%

### Firestore Collections
Automatically created and managed:
- `sessions` - Chat session storage
- `messages` - Message history
- `contracts` - Uploaded contract documents
- `clauses` - Extracted contract clauses
- `thinking_logs` - Agent reasoning process
- `documents` - Generated legal documents

### Security Rules Status
✅ **Deployed**: Allow all reads/writes for development
- Location: https://console.firebase.google.com/project/legalmind-486106/firestore/rules

---

## 🧪 Testing the System

### Test Frontend Connection
1. Visit http://localhost:3000
2. You should see the LegalMind landing page with "LM" logo (blue badge)
3. Navigation includes: Chat, Contracts, Dashboard, Reports, Thinking Logs

### Test Backend API
1. Visit http://localhost:8000/docs
2. Try the `GET /api/health` endpoint
3. Try `GET /api/chat/sessions` to list sessions

### Test Chat
1. Go to http://localhost:3000/chat
2. Type a message like "What compliance frameworks should I check for?"
3. Backend will route to appropriate agent and return response

### Test Contract Upload
1. Go to http://localhost:3000/contracts
2. Upload a PDF contract
3. See extracted information and compliance checks

---

## 📝 Firestore Rules (Current - Development)

```firestore
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if true;
    }
  }
}
```

**For Production**: Replace with authentication-based rules (see `backend/firestore.rules`)

---

## 🔄 Environment Variables Reference

From `backend/.env.example`:

```dotenv
# Gemini API
GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-2.0-flash

# Google Cloud
GOOGLE_CLOUD_PROJECT=legalmind-486106
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json (optional)

# Firestore
FIRESTORE_DATABASE=(default)

# Cloud Storage
GCS_BUCKET_NAME=legalmind-contracts
GCS_CONTRACTS_FOLDER=contracts
GCS_DOCUMENTS_FOLDER=generated-documents

# Application
APP_NAME=LegalMind
APP_ENV=development
DEBUG=true
API_HOST=0.0.0.0
API_PORT=8000

# Session Configuration
SESSION_TIMEOUT_MINUTES=60
MAX_TOKENS_PER_REQUEST=8192

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=30

# Feature Flags
ENABLE_SEARCH_GROUNDING=true
ENABLE_THINKING_LOGS=true
ENABLE_CITATIONS=true
```

---

## 📂 Project Structure

```
gemini-hackathon/
├── backend/
│   ├── services/           # Core services (Gemini, Firestore, Storage)
│   ├── agents/             # Legal agent definitions
│   ├── tools/              # Analysis tools (14+)
│   ├── api/                # REST API endpoints
│   ├── managers/           # Business logic (ChatbotManager)
│   ├── config/             # Settings management
│   ├── main_new.py         # Backend entry point
│   ├── .env.local          # Local secrets (NOT in git)
│   ├── .env.example        # Configuration template
│   └── firestore.rules     # Security rules
│
├── frontend/
│   ├── app/
│   │   ├── chat/           # Chat interface
│   │   ├── contracts/      # Contract management
│   │   ├── dashboard/      # Risk dashboard
│   │   ├── reports/        # Reports view
│   │   ├── thinking-logs/  # Agent reasoning
│   │   └── api/            # API proxy routes
│   ├── components/         # Reusable UI components
│   ├── lib/                # Utility functions
│   ├── globals.css         # Global theme (legal blue)
│   └── package.json
│
├── docs/
│   ├── README.md           # Project overview
│   ├── IMPLEMENTATION_PLAN.md
│   ├── FRONTEND_CHANGES.md
│   ├── CODE_TRANSFORMATION_GUIDE.md
│   └── PROJECT_STATUS.md
│
├── ENV_SETUP.md            # Environment configuration guide
├── FIRESTORE_SETUP.md      # Firestore setup instructions
├── deploy_firestore_rules.py
└── deploy-firestore-rules.bat
```

---

## 🚀 Next Steps

1. **Test the Chat**: Ask legal questions and see agents respond
2. **Upload Contracts**: Test contract analysis workflow
3. **Check Compliance**: Test compliance checking features
4. **View Reports**: Generate and view legal documents
5. **Monitor Thinking**: View agent reasoning process in thinking logs

---

## ⚠️ Important Notes

- **Keep `.env.local` secret**: Never commit to git or share API keys
- **Production Rules**: Update Firestore rules before production deployment
- **Rate Limits**: API has 30 requests/minute rate limit for development
- **Token Limits**: 8192 max tokens per request to Gemini
- **Session Timeout**: Sessions expire after 60 minutes of inactivity

---

## 🆘 Troubleshooting

### Backend won't start
- Check `GEMINI_API_KEY` is valid in `.env.local`
- Verify `GOOGLE_CLOUD_PROJECT=legalmind-486106` is correct
- Ensure Firestore security rules are deployed

### Frontend API calls fail (500 error)
- Check backend is running on http://localhost:8000
- Verify Firestore rules are deployed (allow read/write)
- Check browser console for specific error messages

### Firestore connection timeout
- Verify Project ID is `legalmind-486106`
- Ensure security rules are published
- Check internet connection to Google Cloud

### API documentation blank
- Visit http://localhost:8000/docs (not /swagger)
- Wait 5 seconds for OpenAPI schema to load
- Check backend logs for errors

---

## 📞 Support Resources

- **API Docs**: http://localhost:8000/docs
- **Firebase Console**: https://console.firebase.google.com/project/legalmind-486106
- **Google Cloud Console**: https://console.cloud.google.com/project/legalmind-486106
- **Gemini API Docs**: https://ai.google.dev/docs

---

**LegalMind is ready for development and testing!** 🎉

Start building amazing legal AI features.
