# LegalMind Backend - Project Structure

The LegalMind backend is built on a modular, Google Cloud-native architecture that enables specialized legal AI agents to collaborate via a unified orchestration layer.

```
backend/
│
├── agents/                         # Agent definitions and orchestration
│   ├── __init__.py                 # Re-exports key classes and functions
│   ├── agent_definitions_new.py    # Legal agent instructions and constants
│   ├── agent_strategies_new.py     # Routing and workflow logic
│
├── managers/                       # High-level managers
│   ├── __init__.py
│   ├── chatbot_manager_new.py      # Chat session orchestration
│
├── services/                       # Google Cloud services
│   ├── __init__.py
│   ├── gemini_service.py           # Gemini API wrapper + tool execution
│   ├── firestore_service.py        # Firestore CRUD operations
│   ├── storage_service.py          # Cloud Storage file management
│
├── tools/                          # Function-calling tools
│   ├── __init__.py
│   ├── contract_tools.py
│   ├── clause_tools.py
│   ├── compliance_tools.py
│   ├── risk_tools.py
│   ├── document_tools.py
│   └── logging_tools.py
│
├── api/                            # API layer
│   ├── __init__.py
│   ├── app_new.py                  # FastAPI app + WebSockets
│   └── endpoints_new.py            # API endpoint definitions
│
├── config/                         # Configuration
│   ├── __init__.py
│   └── settings.py                 # Environment and settings
│
├── test_backend.py                 # Comprehensive backend tests
├── main_new.py                     # Main entry point
└── README.md                       # Project documentation
```

## Core Components

### Specialized Legal Agents

1. **Contract Parser Agent** (`CONTRACT_PARSER_AGENT`)
   - Extracts parties, clauses, and obligations
   - Builds structured contract metadata

2. **Legal Research Agent** (`LEGAL_RESEARCH_AGENT`)
   - Uses Google Search Grounding for legal research
   - Provides cited legal context

3. **Compliance Checker Agent** (`COMPLIANCE_CHECKER_AGENT`)
   - Reviews GDPR, HIPAA, CCPA, SOX compliance
   - Flags gaps and provides remediation guidance

4. **Risk Assessment Agent** (`RISK_ASSESSMENT_AGENT`)
   - Scores clause and contract risks
   - Summarizes high-impact exposure

5. **Legal Memo Agent** (`LEGAL_MEMO_AGENT`)
   - Generates formal legal memos and summaries
   - Produces executive-ready outputs

6. **Assistant Agent** (`ASSISTANT_AGENT`)
   - General legal guidance and Q&A
   - Routes user requests to specialist agents

### Service Layer

- **GeminiService**: Model initialization, tool execution, citation extraction
- **FirestoreService**: Contracts, sessions, messages, thinking logs
- **StorageService**: Contract PDFs and generated reports

## Running the Backend

```bash
cd backend
python main_new.py
```

## Required Environment Variables

```
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GCS_BUCKET_NAME=legalmind-contracts
FIRESTORE_DATABASE=(default)
```
