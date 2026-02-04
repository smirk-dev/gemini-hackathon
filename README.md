<div align="center">

# 🏛️ LegalMind

### **AI-Powered Legal Intelligence Platform**
#### *Transforming Contract Analysis & Legal Research with Advanced AI*

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128%2B-green?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15.3-black?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org/)
[![Gemini](https://img.shields.io/badge/Gemini-2.0%20Flash-orange?style=flat-square&logo=google&logoColor=white)](https://ai.google.dev/)
[![Firestore](https://img.shields.io/badge/Firestore-Native-orange?style=flat-square&logo=google-cloud&logoColor=white)](https://firebase.google.com/docs/firestore)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue?style=flat-square)](LICENSE.md)

<br/>

[🚀 Quick Start](#-quick-start) • [🌍 Deployment](#-deployment) • [📚 Features](#-core-features) • [🏗️ Architecture](#️-architecture) • [📖 Docs](#-documentation) • [💻 Demo](#-use-cases)

</div>

---

## 🌟 **Overview**

**LegalMind** is a cutting-edge, Google Cloud-native platform that revolutionizes legal contract analysis and research. Powered by **Google's Gemini 2.0 Flash** AI model, it orchestrates **6 specialized legal agents** with **14+ intelligent tools** to provide comprehensive contract intelligence, compliance verification, risk assessment, and automated legal documentation.

Perfect for legal teams, compliance officers, contract managers, and enterprises seeking AI-powered legal analysis at scale.

---

## ✨ **Core Features**

<table>
<tr>
<td width="50%">

### 📋 **Smart Contract Analysis**
- Automated clause extraction
- Risk scoring & assessment
- Structured data extraction
- Obligation mapping

### 📚 **Legal Research**
- Precedent analysis
- Legal framework research
- Regulatory tracking
- Citation management

### ✅ **Compliance Verification**
- GDPR compliance checking
- HIPAA requirements validation
- CCPA obligations assessment
- SOX compliance verification

</td>
<td width="50%">

### 🎯 **Risk Management**
- Contract risk scoring
- Liability identification
- Red flag detection
- Exposure analysis

### 📄 **Document Generation**
- Legal memo creation
- Compliance reports
- Executive summaries
- Multi-format export

### 🧠 **Transparent AI**
- Thinking logs & reasoning
- Decision transparency
- Step-by-step analysis
- Full audit trails

</td>
</tr>
</table>

---

## 🏗️ **Architecture**

### **Multi-Agent System** 🤖

```
Query Classifier
      ↓
┌─────────────────────────────────────┐
│         Agent Router                │
├─────────────────────────────────────┤
│  CONTRACT_PARSER → Contract Tools   │
│  LEGAL_RESEARCH → Research Tools    │
│  COMPLIANCE_CHECKER → Compliance    │
│  RISK_ASSESSMENT → Risk Tools       │
│  LEGAL_MEMO → Document Tools        │
│  ASSISTANT → General Q&A            │
└─────────────────────────────────────┘
      ↓
  Tool Execution
      ↓
  Response Generation
      ↓
    User
```

### **Tech Stack** 🛠️

<table>
<tr>
<th>Layer</th>
<th>Technology</th>
<th>Purpose</th>
</tr>
<tr>
<td><strong>Frontend</strong></td>
<td>Next.js 15 • React 18 • TypeScript • Tailwind CSS</td>
<td>Modern UI with real-time updates</td>
</tr>
<tr>
<td><strong>Backend</strong></td>
<td>FastAPI • Python 3.11 • Uvicorn</td>
<td>High-performance async API</td>
</tr>
<tr>
<td><strong>AI/ML</strong></td>
<td>Google Gemini 2.0 Flash</td>
<td>Advanced reasoning & function calling</td>
</tr>
<tr>
<td><strong>Database</strong></td>
<td>Google Cloud Firestore</td>
<td>Scalable document database (99.999% SLA)</td>
</tr>
<tr>
<td><strong>Storage</strong></td>
<td>Google Cloud Storage</td>
<td>Secure PDF & document management</td>
</tr>
<tr>
<td><strong>Infrastructure</strong></td>
<td>Google Cloud Platform</td>
<td>Serverless, auto-scaling deployment</td>
</tr>
</table>

---

## 📊 **System Capabilities**

| Component | Count | Details |
|-----------|-------|---------|
| **Legal Agents** | 6 | Specialized AI agents for different legal tasks |
| **Tools** | 14+ | Contract, compliance, risk, document, clause tools |
| **API Endpoints** | 31 | 29 REST + 2 WebSocket for real-time communication |
| **Collections** | 6 | Sessions, messages, contracts, clauses, logs, docs |
| **Lines of Code** | 9,000+ | ~6,000 backend + ~3,000 frontend |
| **Test Coverage** | 97% | 34/35 tests passing |

---

## 🚀 **Quick Start**

### **Prerequisites**

```bash
✓ Python 3.11+
✓ Node.js 18+
✓ Google Gemini API Key
✓ Google Cloud Project with Firestore
```

### **Installation**

#### **Step 1: Clone & Navigate**
```bash
git clone https://github.com/smirk-dev/gemini-hackathon.git
cd gemini-hackathon
```

#### **Step 2: Configure Environment**
```bash
# Create backend/.env.local with your secrets
GEMINI_API_KEY=your_api_key_here
GOOGLE_CLOUD_PROJECT=legalmind-486106
APP_ENV=development
DEBUG=true
```

#### **Step 3: Start Services**

**Option A: Automated (Windows)**
```bash
start-legalmind.bat
```

**Option B: Manual (All Platforms)**
```bash
# Terminal 1: Backend
cd backend
python main_new.py

# Terminal 2: Frontend
cd frontend
npm install
npm run dev
```

### **Access the Platform**

| Service | URL |
|---------|-----|
| **Web App** | http://localhost:3000 |
| **API** | http://localhost:8000 |
| **API Docs** | http://localhost:8000/docs |

---

## 🌍 **Deployment**

Deploy LegalMind to **Google Cloud Platform** in minutes:

### **Quick Deploy (5 minutes)**
```bash
# 1. Run setup script to configure GCP
./setup-gcp.ps1          # Windows
# or
./setup-gcp.sh           # macOS/Linux

# 2. Add GitHub secrets (from script output)
# - GCP_PROJECT_ID
# - WIF_PROVIDER
# - WIF_SERVICE_ACCOUNT
# - FIREBASE_SERVICE_ACCOUNT

# 3. Push to main branch
git push origin main

# GitHub Actions automatically deploys:
# - Backend → Cloud Run
# - Frontend → Firebase Hosting
```

### **Architecture**
- **Frontend**: Firebase Hosting (CDN + auto-scaling)
- **Backend**: Google Cloud Run (serverless, auto-scaling)
- **Database**: Firestore (99.999% SLA)
- **Storage**: Cloud Storage (for PDFs & documents)

### **Estimated Costs**
- Cloud Run: ~$0.40 per million requests
- Firebase Hosting: Free tier (10 GB/month)
- Firestore: Free tier (25k reads + writes/day)
- **Total**: $5-15/month for moderate usage

📖 **Full Deployment Guides:**
- [Quick Deploy Guide](QUICK_DEPLOY.md) - 5-minute setup
- [Complete Deployment Guide](DEPLOYMENT_GUIDE.md) - Advanced configuration

---

## 🎯 **Use Cases**

### **For Legal Teams**
- 📋 Automate contract review process
- ⚡ Accelerate due diligence
- 🎯 Standardize analysis procedures
- 💾 Maintain searchable archives

### **For Compliance Officers**
- ✅ Verify regulatory compliance automatically
- 🔍 Track compliance evolution
- 📊 Generate compliance reports
- 🚨 Flag potential violations early

### **For Contract Managers**
- 📝 Extract and structure contract data
- 🏷️ Identify key obligations
- 🔑 Track important dates and milestones
- 💰 Calculate financial exposure

### **For Enterprises**
- 🚀 Scale legal operations
- 📈 Improve efficiency by 10x
- 💡 Reduce manual work
- 🎓 Train teams on best practices

---

## 📚 **Documentation**

### **Getting Started**
- 📖 [QUICK_START.md](QUICK_START.md) - Executive summary & quick reference
- ⚙️ [ENV_SETUP.md](ENV_SETUP.md) - Environment configuration guide
- 🗄️ [FIRESTORE_SETUP.md](FIRESTORE_SETUP.md) - Database setup instructions

### **Technical Guides**
- 🏗️ [COMPLETE_SETUP.md](COMPLETE_SETUP.md) - Full technical documentation
- 📊 [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md) - Current project status
- 🔄 [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) - Technical roadmap
- 🎨 [docs/FRONTEND_CHANGES.md](docs/FRONTEND_CHANGES.md) - UI/UX updates
- 📝 [docs/CODE_TRANSFORMATION_GUIDE.md](docs/CODE_TRANSFORMATION_GUIDE.md) - Architecture guide

### **System Status**
- 📊 [STATUS.txt](STATUS.txt) - System overview & ASCII diagram

---

## 🔌 **API Endpoints**

### **Chat API**
```
POST   /api/chat              Send message to legal agents
GET    /api/chat/sessions     List all chat sessions
POST   /api/chat/session      Create new session
WS     /ws/chat/{session_id}  Real-time WebSocket chat
```

### **Contract API**
```
POST   /api/contracts/upload           Upload contract PDF
GET    /api/contracts                  List all contracts
GET    /api/contracts/{id}             Get contract details
GET    /api/contracts/{id}/clauses     Extract clauses
GET    /api/contracts/{id}/download    Download contract
```

### **Compliance & Risk API**
```
GET    /api/compliance/frameworks      List frameworks
GET    /api/compliance/check/{id}      Check compliance
GET    /api/risk/assess/{id}           Assess risks
```

### **System API**
```
GET    /api/health            System health check
GET    /api/agents            List agents
GET    /api/agents/{id}       Get agent details
```

**Full Documentation**: Visit http://localhost:8000/docs for interactive Swagger UI

---

## 🧪 **Testing**

### **Run Backend Tests**
```bash
cd backend
python test_backend.py
```

**Expected Results:** 34/35 tests passing (97%)

### **Health Check**
```bash
curl http://localhost:8000/api/health
```

---

## 📁 **Project Structure**

```
gemini-hackathon/
├── 📂 backend/                          # FastAPI Server
│   ├── services/                        # Google Cloud integrations
│   │   ├── gemini_service.py           # Gemini API wrapper
│   │   ├── firestore_service.py        # Database service
│   │   └── storage_service.py          # Cloud Storage service
│   ├── agents/                          # Legal AI agents
│   │   ├── agent_definitions_new.py    # 6 specialized agents
│   │   └── agent_strategies_new.py     # Query routing logic
│   ├── tools/                           # 14+ legal tools
│   │   ├── contract_tools.py           # Contract analysis
│   │   ├── compliance_tools.py         # Compliance checking
│   │   ├── risk_tools.py               # Risk assessment
│   │   ├── clause_tools.py             # Clause extraction
│   │   ├── document_tools.py           # Document generation
│   │   └── logging_tools.py            # Thinking logs
│   ├── api/                             # REST API
│   │   ├── endpoints_new.py            # 31 endpoints
│   │   └── app_new.py                  # FastAPI setup
│   ├── managers/                        # Business logic
│   │   └── chatbot_manager_new.py      # Session orchestration
│   ├── config/                          # Configuration
│   │   └── settings.py                 # Environment settings
│   ├── main_new.py                     # Entry point
│   ├── .env.local                      # Secrets (gitignored)
│   ├── .env.example                    # Config template
│   └── firestore.rules                 # Security rules
│
├── 📂 frontend/                         # Next.js Application
│   ├── app/
│   │   ├── page.tsx                    # Landing page
│   │   ├── chat/                       # Chat interface
│   │   ├── contracts/                  # Contract management
│   │   ├── dashboard/                  # Analytics dashboard
│   │   ├── reports/                    # Documents & reports
│   │   ├── thinking-logs/              # Agent reasoning
│   │   └── api/                        # API proxy routes
│   ├── components/                      # Reusable UI components
│   ├── lib/                             # Utilities & helpers
│   └── app/globals.css                 # Theme (legal blue)
│
├── 📂 docs/                             # Documentation
│   ├── PROJECT_STATUS.md
│   ├── IMPLEMENTATION_PLAN.md
│   ├── FRONTEND_CHANGES.md
│   └── CODE_TRANSFORMATION_GUIDE.md
│
├── 🚀 start-legalmind.bat              # Quick start script
├── 🔐 .env.local                       # Your secrets
├── 📖 README.md                        # This file
├── ⚡ QUICK_START.md                   # Quick reference
├── ✅ COMPLETE_SETUP.md                # Full guide
├── 🗄️ FIRESTORE_SETUP.md               # Database setup
├── 📊 STATUS.txt                       # System overview
└── 📜 LICENSE.md                       # Apache-2.0
```

---

## 🔐 **Security**

### **Current Setup (Development)**
- ✅ `.env.local` contains API keys (never committed)
- ✅ Firestore security rules deployed
- ✅ CORS configured for local development
- ✅ Debug logging enabled

### **Production Checklist**
- [ ] Update Firestore rules with authentication
- [ ] Create service account for Google Cloud
- [ ] Enable Cloud Run deployment
- [ ] Configure custom domain
- [ ] Set up monitoring & alerting
- [ ] Enable production logging

See [COMPLETE_SETUP.md](COMPLETE_SETUP.md) for detailed production deployment.

---

## 📈 **Performance Metrics**

| Metric | Value |
|--------|-------|
| Backend Startup | < 3 seconds |
| Frontend Build | 12.7 seconds |
| API Response Time | < 100ms (local) |
| Chat Response Time | 2-5 seconds |
| Test Coverage | 97% |
| Firestore SLA | 99.999% |

---

## 🤝 **Contributing**

Contributions are welcome! Please feel free to submit issues or pull requests.

```bash
# Fork the repository
git clone https://github.com/your-username/gemini-hackathon.git

# Create feature branch
git checkout -b feature/amazing-feature

# Commit changes
git commit -m 'Add amazing feature'

# Push to branch
git push origin feature/amazing-feature

# Open Pull Request
```

---

## 📞 **Support & Resources**

### **Cloud Platforms**
- 🔗 [Firebase Console](https://console.firebase.google.com/project/legalmind-486106)
- 🔗 [Google Cloud Console](https://console.cloud.google.com/project/legalmind-486106)
- 🔗 [Gemini API Docs](https://ai.google.dev/docs)

### **Frameworks & Libraries**
- 🔗 [FastAPI Documentation](https://fastapi.tiangolo.com/)
- 🔗 [Next.js Documentation](https://nextjs.org/docs)
- 🔗 [Firebase Documentation](https://firebase.google.com/docs)

### **Getting Help**
- 📖 Read [COMPLETE_SETUP.md](COMPLETE_SETUP.md) for detailed guide
- 💬 Check [STATUS.txt](STATUS.txt) for system overview
- 📝 Review [docs/](docs/) directory for technical details

---

## 📄 **License**

This project is licensed under the **Apache License 2.0** - see [LICENSE.md](LICENSE.md) for details.

```
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0
```

---

## 🙏 **Acknowledgments**

Built with ❤️ using:
- **Google Cloud Platform** for infrastructure
- **Google Gemini 2.0 Flash** for AI capabilities
- **FastAPI** for backend framework
- **Next.js** for frontend framework
- **Firestore** for database
- **Open source community** for amazing tools

---

<div align="center">

### 🌟 **Ready to Transform Legal Analysis?** 🌟

#### Start with [QUICK_START.md](QUICK_START.md) or run:
```bash
start-legalmind.bat
```

#### Then visit: **http://localhost:3000**

<br/>

*Built with AI for the modern legal world*

**[⬆ back to top](#-legalmind)**

</div>
