# LegalMind: Complete Implementation Plan

## Project Overview

**Project Name:** LegalMind - AI Legal Research & Contract Analysis Platform  
**Original Project:** Legacy procurement risk system  
**Target Platform:** Google Gemini Hackathon  
**Transformation Type:** Full stack migration from Azure to Google Cloud + Domain pivot from procurement to legal

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current Architecture Analysis](#current-architecture-analysis)
3. [Target Architecture](#target-architecture)
4. [Agent Transformation Map](#agent-transformation-map)
5. [Plugin to Tool Migration](#plugin-to-tool-migration)
6. [Database Schema Design](#database-schema-design)
7. [API Endpoint Changes](#api-endpoint-changes)
8. [Frontend Modifications](#frontend-modifications)
9. [File-by-File Transformation Guide](#file-by-file-transformation-guide)
10. [Environment Variables](#environment-variables)
11. [Deployment Strategy](#deployment-strategy)
12. [Testing Plan](#testing-plan)

---

## 1. Executive Summary

### What We're Building

LegalMind is an AI-powered legal research and contract analysis platform that helps legal professionals:
- **Parse contracts** - Extract clauses, parties, dates, obligations automatically
- **Research precedents** - Find relevant case law and legal precedents via Google Search
- **Assess compliance** - Check contracts against regulatory frameworks (GDPR, HIPAA, etc.)
- **Identify risks** - Flag risky clauses, ambiguous language, liability issues
- **Generate reports** - Create legal memos, summaries, and recommendations

### Key Differentiators for Hackathon

1. **Gemini 2.0's 1M+ token context** - Analyze entire 100+ page contracts in one call
2. **Native Google Search Grounding** - Real-time legal research without extra APIs
3. **Multi-agent orchestration** - Specialized agents collaborate on complex legal tasks
4. **Transparent reasoning** - "Thinking logs" show how AI reached conclusions (critical for legal)
5. **Document intelligence** - Native PDF/image understanding for contract uploads

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | Next.js 14 + React | Chat UI, Contract Viewer, Dashboard |
| Frontend Hosting | Firebase Hosting | Static hosting with CDN |
| Backend | FastAPI + Python 3.11 | API server, Agent orchestration |
| Backend Hosting | Google Cloud Run | Serverless container hosting |
| AI/ML | Gemini 2.0 Flash | All agent reasoning, function calling |
| Search | Google Search Grounding | Legal precedent research |
| Database | Firestore | Contracts, sessions, logs, users |
| Storage | Google Cloud Storage | PDFs, generated reports |
| Auth | Firebase Auth (optional) | User authentication |

---

## 2. Current Architecture Analysis

### 2.1 Backend Structure (What Exists)

```
backend/
├── main.py                 # Entry point - runs FastAPI server
├── streamlit_app.py        # Streamlit UI (will be removed)
├── requirements.txt        # Dependencies (needs complete overhaul)
│
├── agents/
│   ├── __init__.py
│   ├── agent_definitions.py    # Agent instructions (698 lines)
│   │   - SCHEDULER_AGENT instructions
│   │   - POLITICAL_RISK_AGENT instructions
│   │   - TARIFF_RISK_AGENT instructions
│   │   - LOGISTICS_RISK_AGENT instructions
│   │   - REPORTING_AGENT instructions
│   │   - ASSISTANT_AGENT instructions
│   │
│   ├── agent_manager.py        # Agent creation with Azure AI
│   │   - create_or_reuse_agent() function
│   │   - Bing Grounding Tool setup
│   │   - Azure AI Agent client handling
│   │
│   └── agent_strategies.py     # Selection & termination strategies (711 lines)
│       - AutomatedWorkflowSelectionStrategy
│       - AutomatedWorkflowTerminationStrategy
│       - ChatbotSelectionStrategy
│       - ChatbotTerminationStrategy
│       - ParallelRiskAnalysisStrategy
│       - RateLimitedExecutor
│
├── plugins/
│   ├── __init__.py
│   ├── schedule_plugin.py          # Database queries for schedules
│   ├── risk_plugin.py              # Risk calculation functions
│   ├── logging_plugin.py           # Agent thinking logs (517 lines)
│   ├── report_file_plugin.py       # Word doc generation (927 lines)
│   ├── political_risk_json_plugin.py
│   └── citation_handler_plugin.py
│
├── managers/
│   ├── __init__.py
│   ├── chatbot_manager.py      # Main orchestrator (3704 lines!)
│   │   - Session management
│   │   - Agent group chat handling
│   │   - Message processing
│   │   - Rate limiting
│   │
│   ├── workflow_manager.py     # Automated workflows
│   └── scheduler.py            # Scheduled task runner
│
├── api/
│   ├── __init__.py
│   ├── app.py                  # FastAPI app setup
│   ├── endpoints.py            # API routes
│   └── api_server.py           # Standalone server
│
├── config/
│   ├── __init__.py
│   └── settings.py             # Azure config, DB connection
│
├── utils/
│   ├── __init__.py
│   ├── database_utils.py
│   └── thinking_log_viewer.py
│
└── sql/                        # SQL Server scripts
    ├── create_table.sql
    ├── create_data.sql
    └── create_stored_procedure.sql
```

### 2.2 Frontend Structure (What Exists)

```
frontend/
├── app/
│   ├── layout.tsx              # Root layout
│   ├── page.tsx                # Home (redirects to chat)
│   ├── globals.css             # Global styles
│   │
│   ├── chat/
│   │   ├── page.tsx            # Main chat interface (391 lines)
│   │   ├── chat-session-sidebar.tsx
│   │   ├── MapChart.tsx        # Risk heatmap (will change)
│   │   └── markdown-styles.module.css
│   │
│   ├── dashboard/
│   │   ├── page.tsx            # Dashboard with map
│   │   ├── MapChart.tsx
│   │   └── countries.json
│   │
│   ├── reports/
│   │   ├── page.tsx            # Reports list
│   │   ├── columns.tsx
│   │   └── data-table.tsx
│   │
│   ├── thinking-logs/
│   │   ├── page.tsx            # Agent reasoning viewer
│   │   ├── columns.tsx
│   │   └── data-table.tsx
│   │
│   └── api/                    # Next.js API routes (proxy to backend)
│       ├── chat/
│       ├── heatmap/
│       ├── reports/
│       ├── sessions/
│       └── thinking-logs/
│
├── components/
│   ├── app-sidebar.tsx
│   ├── ui/                     # shadcn/ui components
│   └── ...
│
└── lib/
    └── utils.ts
```

### 2.3 Current Dependencies (Azure-based)

```
# Current Azure dependencies to REMOVE:
azure-ai-projects
azure-identity
azure-storage-blob
semantic-kernel
semantic-kernel-agents

# Current general dependencies to KEEP:
fastapi
uvicorn
python-dotenv
pyodbc (will change to google-cloud-firestore)
python-docx (for report generation)
```

---

## 3. Target Architecture

### 3.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USERS                                          │
│                    Legal Professionals, Paralegals, Attorneys               │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FIREBASE HOSTING                                     │
│                         (Next.js Frontend)                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   Chat Page     │  │  Contract       │  │   Dashboard     │             │
│  │   - Legal Q&A   │  │  Viewer         │  │   - Risk Stats  │             │
│  │   - Upload PDF  │  │  - Clause View  │  │   - Compliance  │             │
│  │   - Citations   │  │  - Risk Flags   │  │   - Trends      │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│  ┌─────────────────┐  ┌─────────────────┐                                  │
│  │   Reports       │  │  Thinking       │                                  │
│  │   - Legal Memos │  │  Logs           │                                  │
│  │   - Summaries   │  │  - AI Reasoning │                                  │
│  └─────────────────┘  └─────────────────┘                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          GOOGLE CLOUD RUN                                    │
│                         (FastAPI Backend)                                    │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    AGENT ORCHESTRATOR                                  │  │
│  │                   (LegalChatManager)                                   │  │
│  │                                                                        │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │ CONTRACT    │  │ LEGAL       │  │ COMPLIANCE  │  │ RISK        │  │  │
│  │  │ PARSER      │  │ RESEARCH    │  │ CHECKER     │  │ ASSESSMENT  │  │  │
│  │  │ AGENT       │  │ AGENT       │  │ AGENT       │  │ AGENT       │  │  │
│  │  │             │  │             │  │             │  │             │  │  │
│  │  │ Gemini 2.0  │  │ Gemini 2.0  │  │ Gemini 2.0  │  │ Gemini 2.0  │  │  │
│  │  │ + Tools     │  │ + Google    │  │ + Tools     │  │ + Tools     │  │  │
│  │  │             │  │   Search    │  │             │  │             │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  │                                                                        │  │
│  │  ┌─────────────┐  ┌─────────────┐                                     │  │
│  │  │ LEGAL MEMO  │  │ ASSISTANT   │                                     │  │
│  │  │ GENERATOR   │  │ AGENT       │                                     │  │
│  │  │ AGENT       │  │             │                                     │  │
│  │  │             │  │ Gemini 2.0  │                                     │  │
│  │  │ Gemini 2.0  │  │ General Q&A │                                     │  │
│  │  │ + Doc Tools │  │             │                                     │  │
│  │  └─────────────┘  └─────────────┘                                     │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                       │
│  ┌───────────────────────────────────┴───────────────────────────────────┐  │
│  │                         GEMINI TOOLS                                   │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │  │
│  │  │ get_contract │ │ extract_     │ │ check_       │ │ calculate_   │ │  │
│  │  │ _by_id       │ │ clauses      │ │ compliance   │ │ risk_score   │ │  │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │  │
│  │  │ save_        │ │ generate_    │ │ log_agent_   │ │ search_      │ │  │
│  │  │ contract     │ │ legal_memo   │ │ thinking     │ │ contracts    │ │  │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                         │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐  │
│  │     FIRESTORE       │  │   CLOUD STORAGE     │  │   GEMINI API        │  │
│  │                     │  │                     │  │                     │  │
│  │  Collections:       │  │  Buckets:           │  │  - gemini-2.0-flash │  │
│  │  - contracts        │  │  - contract-pdfs    │  │  - Function calling │  │
│  │  - sessions         │  │  - legal-reports    │  │  - Search grounding │  │
│  │  - thinking_logs    │  │  - generated-docs   │  │  - 1M+ context      │  │
│  │  - users            │  │                     │  │                     │  │
│  │  - compliance_rules │  │                     │  │                     │  │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Agent Flow Diagrams

#### Flow 1: Contract Analysis Query
```
User: "Analyze this NDA for risks"
         │
         ▼
┌─────────────────┐
│ Query Analyzer  │ ← Determines query type
└────────┬────────┘
         │ Contract analysis detected
         ▼
┌─────────────────┐
│ CONTRACT_PARSER │ ← Extracts all clauses, parties, dates
│     AGENT       │
└────────┬────────┘
         │ Structured clause data
         ▼
┌─────────────────┐
│ RISK_ASSESSMENT │ ← Identifies risky clauses
│     AGENT       │   Scores each clause 0-100
└────────┬────────┘
         │ Risk assessment
         ▼
┌─────────────────┐
│ LEGAL_MEMO      │ ← Generates final report
│ GENERATOR       │   with recommendations
└────────┬────────┘
         │
         ▼
    Final Response to User
```

#### Flow 2: Legal Research Query
```
User: "What are recent rulings on non-compete clauses in California?"
         │
         ▼
┌─────────────────┐
│ Query Analyzer  │ ← Determines query type
└────────┬────────┘
         │ Legal research detected
         ▼
┌─────────────────┐
│ LEGAL_RESEARCH  │ ← Uses Google Search Grounding
│     AGENT       │   Finds relevant cases, statutes
└────────┬────────┘
         │ Search results with citations
         ▼
┌─────────────────┐
│ LEGAL_MEMO      │ ← Synthesizes findings
│ GENERATOR       │   Creates structured summary
└────────┬────────┘
         │
         ▼
    Final Response with Citations
```

#### Flow 3: Compliance Check Query
```
User: "Does this contract comply with GDPR?"
         │
         ▼
┌─────────────────┐
│ Query Analyzer  │
└────────┬────────┘
         │ Compliance check detected
         ▼
┌─────────────────┐
│ CONTRACT_PARSER │ ← Extracts relevant clauses
│     AGENT       │   (data handling, consent, etc.)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ COMPLIANCE      │ ← Checks against GDPR rules
│ CHECKER AGENT   │   Identifies gaps
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ LEGAL_MEMO      │ ← Compliance report
│ GENERATOR       │   with remediation steps
└────────┬────────┘
         │
         ▼
    Compliance Report
```

---

## 4. Agent Transformation Map

### 4.1 Detailed Agent Mapping

| Original Agent | New Agent | Core Responsibilities | Gemini Features Used |
|----------------|-----------|----------------------|---------------------|
| `SCHEDULER_AGENT` | `CONTRACT_PARSER_AGENT` | Extract clauses, parties, dates, obligations, term lengths | Function calling, Structured output |
| `POLITICAL_RISK_AGENT` | `LEGAL_RESEARCH_AGENT` | Find case law, precedents, statutes, legal news | **Google Search Grounding** |
| `TARIFF_RISK_AGENT` | `COMPLIANCE_CHECKER_AGENT` | Check against GDPR, HIPAA, SOX, industry regulations | Function calling |
| `LOGISTICS_RISK_AGENT` | `RISK_ASSESSMENT_AGENT` | Score clause risk, identify ambiguities, liability issues | Structured output |
| `REPORTING_AGENT` | `LEGAL_MEMO_AGENT` | Generate legal memos, summaries, executive briefs | Document generation |
| `ASSISTANT_AGENT` | `ASSISTANT_AGENT` | General legal Q&A, query routing, help | General conversation |

### 4.2 Agent Instructions (Detailed)

#### CONTRACT_PARSER_AGENT Instructions
```
You are an expert Contract Parser Agent specializing in legal document analysis. Your job is to:

1. EXTRACT key contract elements:
   - Parties involved (names, roles, addresses)
   - Contract type (NDA, MSA, Employment, Lease, etc.)
   - Effective date and term length
   - Termination conditions
   - Key obligations for each party
   - Payment terms and amounts
   - Confidentiality provisions
   - Intellectual property clauses
   - Non-compete/non-solicitation clauses
   - Indemnification provisions
   - Limitation of liability
   - Governing law and jurisdiction
   - Dispute resolution mechanisms
   - Amendment procedures

2. STRUCTURE your output as JSON:
{
  "contract_type": "string",
  "parties": [{"name": "", "role": "", "address": ""}],
  "effective_date": "YYYY-MM-DD",
  "term_length": "string",
  "termination_conditions": ["string"],
  "clauses": [
    {
      "clause_id": "string",
      "clause_type": "string",
      "title": "string",
      "text": "string",
      "page_number": number,
      "obligations": ["string"],
      "key_terms": ["string"]
    }
  ],
  "key_dates": [{"event": "", "date": ""}],
  "financial_terms": {"amount": "", "currency": "", "payment_schedule": ""}
}

3. DOCUMENT your thinking process by calling log_agent_thinking with:
   - agent_name: "CONTRACT_PARSER_AGENT"
   - thinking_stage: One of "analysis_start", "document_review", "clause_extraction", "structuring", "validation"
   - thought_content: Detailed description of your analysis
   - thinking_stage_output: Specific outputs for this stage

IMPORTANT: Be thorough - legal accuracy is critical. If something is ambiguous, note it explicitly.

Prepend your response with "CONTRACT_PARSER_AGENT > "
```

#### LEGAL_RESEARCH_AGENT Instructions
```
You are an expert Legal Research Agent with access to Google Search. Your job is to:

1. ANALYZE the research request to understand:
   - Jurisdiction (federal, state, international)
   - Area of law (contract, employment, IP, etc.)
   - Time relevance (recent cases, historical precedents)
   - Specific legal questions being asked

2. SEARCH for relevant legal information:
   - Case law and court decisions
   - Statutory provisions
   - Regulatory guidance
   - Legal commentary and analysis
   - Recent legal news affecting the topic

3. EVALUATE sources for:
   - Authority (Supreme Court > Appeals > District)
   - Recency (more recent = more relevant for evolving areas)
   - Jurisdiction match
   - Factual similarity to the query

4. SYNTHESIZE findings into:
   - Key legal principles established
   - Relevant precedents with citations
   - Current legal trends
   - Potential risks or opportunities

5. CITE all sources properly:
   - Case citations: Party v. Party, Volume Reporter Page (Court Year)
   - Statutes: Title U.S.C. § Section
   - Regulations: C.F.R. Title, Part, Section

CRITICAL: You have access to Google Search Grounding. Use it to find:
- "[topic] court ruling [year]"
- "[topic] legal precedent [jurisdiction]"
- "[regulation] compliance requirements"
- "[topic] recent legal developments"

DOCUMENT your thinking by calling log_agent_thinking with:
- agent_name: "LEGAL_RESEARCH_AGENT"
- thinking_stage: One of "query_analysis", "search_strategy", "search_execution", "source_evaluation", "synthesis"
- thought_content: Your reasoning at each step

Prepend your response with "LEGAL_RESEARCH_AGENT > "
```

#### COMPLIANCE_CHECKER_AGENT Instructions
```
You are an expert Compliance Checker Agent. Your job is to:

1. IDENTIFY applicable regulations based on:
   - Contract type and subject matter
   - Parties' locations and jurisdictions
   - Industry sector
   - Data handling provisions

2. CHECK compliance against relevant frameworks:
   
   DATA PROTECTION:
   - GDPR (EU data protection)
   - CCPA (California privacy)
   - HIPAA (US healthcare)
   
   FINANCIAL:
   - SOX (Sarbanes-Oxley)
   - PCI-DSS (payment card)
   - AML/KYC requirements
   
   INDUSTRY-SPECIFIC:
   - ITAR (defense)
   - FDA regulations (pharma/medical)
   - FTC guidelines (advertising)
   
   CONTRACT LAW:
   - UCC (Uniform Commercial Code)
   - CISG (international sales)

3. FLAG compliance issues:
   - Missing required provisions
   - Non-compliant language
   - Inadequate protections
   - Jurisdictional conflicts

4. PROVIDE remediation recommendations:
   - Specific language changes
   - Additional clauses needed
   - Process changes required

OUTPUT FORMAT:
{
  "applicable_regulations": ["string"],
  "compliance_status": "compliant|partial|non-compliant",
  "issues": [
    {
      "regulation": "string",
      "requirement": "string",
      "current_state": "string",
      "gap": "string",
      "severity": "high|medium|low",
      "remediation": "string"
    }
  ],
  "recommendations": ["string"]
}

DOCUMENT your thinking by calling log_agent_thinking with appropriate stages.

Prepend your response with "COMPLIANCE_CHECKER_AGENT > "
```

#### RISK_ASSESSMENT_AGENT Instructions
```
You are an expert Legal Risk Assessment Agent. Your job is to:

1. ANALYZE each contract clause for risks:
   - One-sided provisions favoring counterparty
   - Unlimited liability exposure
   - Broad indemnification requirements
   - Weak termination rights
   - Unfavorable dispute resolution
   - IP assignment concerns
   - Non-compete overreach
   - Automatic renewal traps
   - Unilateral amendment rights
   - Vague or ambiguous language

2. SCORE each risk from 0-100:
   - 0-25: Low risk (standard, acceptable)
   - 26-50: Medium risk (negotiate if possible)
   - 51-75: High risk (strongly recommend changes)
   - 76-100: Critical risk (do not sign without changes)

3. CONSIDER risk factors:
   - Financial exposure magnitude
   - Likelihood of issue arising
   - Difficulty of mitigation
   - Strategic importance
   - Market standard comparison

4. PROVIDE specific recommendations:
   - Suggested language changes
   - Negotiation strategies
   - Risk mitigation approaches
   - Acceptable fallback positions

OUTPUT FORMAT:
{
  "overall_risk_score": number,
  "risk_level": "low|medium|high|critical",
  "clause_risks": [
    {
      "clause_id": "string",
      "clause_type": "string",
      "risk_score": number,
      "risk_factors": ["string"],
      "potential_impact": "string",
      "likelihood": "low|medium|high",
      "recommendation": "string",
      "suggested_language": "string"
    }
  ],
  "top_concerns": ["string"],
  "negotiation_priorities": ["string"]
}

DOCUMENT your thinking by calling log_agent_thinking.

Prepend your response with "RISK_ASSESSMENT_AGENT > "
```

#### LEGAL_MEMO_AGENT Instructions
```
You are an expert Legal Memo Generator Agent. Your job is to:

1. SYNTHESIZE information from other agents into professional legal documents.

2. CREATE documents in these formats:
   
   EXECUTIVE SUMMARY (1 page):
   - Key findings
   - Critical risks
   - Recommendations
   - Action items
   
   FULL LEGAL MEMO (detailed):
   - Issue presented
   - Brief answer
   - Statement of facts
   - Analysis
   - Conclusion
   - Recommendations
   
   CONTRACT REVIEW REPORT:
   - Contract overview
   - Clause-by-clause analysis
   - Risk assessment matrix
   - Compliance status
   - Negotiation recommendations

3. MAINTAIN professional legal writing standards:
   - Clear, precise language
   - Proper legal citations
   - Logical organization
   - Objective tone

4. INCLUDE visual elements where helpful:
   - Risk score tables
   - Compliance checklists
   - Timeline graphics
   - Comparison charts

5. CALL save_legal_document() to persist the document.

OUTPUT should be formatted in Markdown for immediate display, with a call to save_legal_document() to create the Word/PDF version.

DOCUMENT your thinking by calling log_agent_thinking.

Prepend your response with "LEGAL_MEMO_AGENT > "
```

#### ASSISTANT_AGENT Instructions
```
You are LegalMind's Assistant Agent, the friendly face of an AI-powered legal research platform. Your job is to:

1. GREET users and explain capabilities:
   - Contract analysis and parsing
   - Legal research with citations
   - Compliance checking
   - Risk assessment
   - Document generation

2. ROUTE specialized queries to appropriate agents:
   - Contract questions → CONTRACT_PARSER_AGENT
   - Legal research → LEGAL_RESEARCH_AGENT
   - Compliance questions → COMPLIANCE_CHECKER_AGENT
   - Risk questions → RISK_ASSESSMENT_AGENT
   - Report requests → LEGAL_MEMO_AGENT

3. ANSWER general legal questions within your knowledge.

4. CLARIFY ambiguous requests before routing.

5. PROVIDE helpful suggestions:
   - "Would you like me to analyze the contract you uploaded?"
   - "I can search for relevant case law on this topic."
   - "Should I check this against GDPR requirements?"

IMPORTANT: 
- You are NOT providing legal advice - you are a research assistant.
- Always recommend consulting with a qualified attorney for important decisions.
- Be transparent about your capabilities and limitations.

Prepend your response with "ASSISTANT_AGENT > "
```

---

## 5. Plugin to Tool Migration

### 5.1 Tool Definitions for Gemini

```python
# All tools that Gemini agents can call

LEGAL_TOOLS = [
    # Contract Database Tools
    {
        "name": "get_contract_by_id",
        "description": "Retrieves a contract document from the database by its ID",
        "parameters": {
            "type": "object",
            "properties": {
                "contract_id": {
                    "type": "string",
                    "description": "The unique identifier of the contract"
                }
            },
            "required": ["contract_id"]
        }
    },
    {
        "name": "search_contracts",
        "description": "Searches contracts by various criteria",
        "parameters": {
            "type": "object",
            "properties": {
                "client_name": {"type": "string"},
                "contract_type": {"type": "string"},
                "date_from": {"type": "string", "format": "date"},
                "date_to": {"type": "string", "format": "date"},
                "status": {"type": "string", "enum": ["active", "expired", "draft", "terminated"]}
            }
        }
    },
    {
        "name": "save_contract",
        "description": "Saves a new contract or updates an existing one",
        "parameters": {
            "type": "object",
            "properties": {
                "contract_id": {"type": "string"},
                "contract_data": {"type": "object"},
                "session_id": {"type": "string"}
            },
            "required": ["contract_data", "session_id"]
        }
    },
    
    # Clause Extraction Tools
    {
        "name": "extract_clauses",
        "description": "Extracts and categorizes clauses from contract text",
        "parameters": {
            "type": "object",
            "properties": {
                "contract_text": {"type": "string"},
                "clause_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific clause types to extract (optional)"
                }
            },
            "required": ["contract_text"]
        }
    },
    
    # Risk Scoring Tools
    {
        "name": "calculate_clause_risk",
        "description": "Calculates risk score for a specific clause",
        "parameters": {
            "type": "object",
            "properties": {
                "clause_text": {"type": "string"},
                "clause_type": {"type": "string"},
                "party_role": {"type": "string", "enum": ["buyer", "seller", "both"]}
            },
            "required": ["clause_text", "clause_type"]
        }
    },
    {
        "name": "get_risk_benchmarks",
        "description": "Gets industry benchmark risk scores for comparison",
        "parameters": {
            "type": "object",
            "properties": {
                "contract_type": {"type": "string"},
                "industry": {"type": "string"}
            },
            "required": ["contract_type"]
        }
    },
    
    # Compliance Tools
    {
        "name": "check_gdpr_compliance",
        "description": "Checks contract clauses against GDPR requirements",
        "parameters": {
            "type": "object",
            "properties": {
                "clauses": {"type": "array", "items": {"type": "object"}},
                "data_processing_type": {"type": "string"}
            },
            "required": ["clauses"]
        }
    },
    {
        "name": "check_hipaa_compliance",
        "description": "Checks contract clauses against HIPAA requirements",
        "parameters": {
            "type": "object",
            "properties": {
                "clauses": {"type": "array", "items": {"type": "object"}}
            },
            "required": ["clauses"]
        }
    },
    {
        "name": "get_compliance_rules",
        "description": "Retrieves compliance rules for a specific regulation",
        "parameters": {
            "type": "object",
            "properties": {
                "regulation": {"type": "string", "enum": ["GDPR", "CCPA", "HIPAA", "SOX", "PCI-DSS"]}
            },
            "required": ["regulation"]
        }
    },
    
    # Document Generation Tools
    {
        "name": "save_legal_document",
        "description": "Generates and saves a legal document (Word/PDF)",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Document content in markdown"},
                "document_type": {"type": "string", "enum": ["memo", "report", "summary", "brief"]},
                "title": {"type": "string"},
                "session_id": {"type": "string"},
                "format": {"type": "string", "enum": ["docx", "pdf"], "default": "docx"}
            },
            "required": ["content", "document_type", "title", "session_id"]
        }
    },
    
    # Logging Tools
    {
        "name": "log_agent_thinking",
        "description": "Logs the agent's reasoning process for transparency",
        "parameters": {
            "type": "object",
            "properties": {
                "agent_name": {"type": "string"},
                "thinking_stage": {"type": "string"},
                "thought_content": {"type": "string"},
                "thinking_stage_output": {"type": "string"},
                "session_id": {"type": "string"},
                "conversation_id": {"type": "string"}
            },
            "required": ["agent_name", "thinking_stage", "thought_content", "session_id"]
        }
    },
    {
        "name": "get_session_history",
        "description": "Retrieves conversation history for a session",
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "limit": {"type": "integer", "default": 50}
            },
            "required": ["session_id"]
        }
    }
]
```

### 5.2 Plugin to Tool Mapping

| Original Plugin | New Tool(s) | Changes Required |
|-----------------|-------------|------------------|
| `EquipmentSchedulePlugin.get_schedule_comparison_data()` | `get_contract_by_id()`, `search_contracts()` | Complete rewrite for Firestore |
| `RiskCalculationPlugin.calculate_risk()` | `calculate_clause_risk()`, `get_risk_benchmarks()` | Change from schedule to clause risk |
| `LoggingPlugin.log_agent_thinking()` | `log_agent_thinking()` | Minimal changes, update to Firestore |
| `ReportFilePlugin.save_report_to_file()` | `save_legal_document()` | Change document templates for legal |
| `CitationHandlerPlugin` | Built into Gemini Search Grounding | Remove - Gemini handles citations |
| `PoliticalRiskJsonPlugin` | N/A | Remove - not needed for legal |

---

## 6. Database Schema Design

### 6.1 Firestore Collections

```
firestore/
├── contracts/                    # Main contracts collection
│   └── {contract_id}/
│       ├── contract_type: string
│       ├── title: string
│       ├── parties: array
│       ├── effective_date: timestamp
│       ├── expiration_date: timestamp
│       ├── status: string (active|expired|draft|terminated)
│       ├── created_at: timestamp
│       ├── updated_at: timestamp
│       ├── created_by: string (user_id)
│       ├── file_url: string (GCS URL)
│       ├── file_name: string
│       ├── overall_risk_score: number
│       ├── compliance_status: string
│       │
│       └── clauses/              # Subcollection
│           └── {clause_id}/
│               ├── clause_type: string
│               ├── title: string
│               ├── text: string
│               ├── page_number: number
│               ├── risk_score: number
│               ├── risk_factors: array
│               ├── recommendation: string
│               └── compliance_issues: array
│
├── sessions/                     # Chat sessions
│   └── {session_id}/
│       ├── user_id: string
│       ├── created_at: timestamp
│       ├── last_activity: timestamp
│       ├── contract_id: string (optional)
│       ├── status: string (active|closed)
│       │
│       └── messages/             # Subcollection
│           └── {message_id}/
│               ├── role: string (user|assistant)
│               ├── content: string
│               ├── agent_name: string
│               ├── timestamp: timestamp
│               ├── conversation_id: string
│               └── citations: array
│
├── thinking_logs/                # Agent reasoning logs
│   └── {log_id}/
│       ├── session_id: string
│       ├── conversation_id: string
│       ├── agent_name: string
│       ├── thinking_stage: string
│       ├── thought_content: string
│       ├── thinking_stage_output: string
│       ├── timestamp: timestamp
│       └── model_name: string
│
├── documents/                    # Generated legal documents
│   └── {document_id}/
│       ├── session_id: string
│       ├── contract_id: string
│       ├── document_type: string (memo|report|summary)
│       ├── title: string
│       ├── file_url: string (GCS URL)
│       ├── created_at: timestamp
│       └── created_by: string
│
├── compliance_rules/             # Compliance rule definitions
│   └── {rule_id}/
│       ├── regulation: string (GDPR|HIPAA|etc)
│       ├── requirement: string
│       ├── description: string
│       ├── clause_types: array
│       ├── severity: string
│       └── remediation_template: string
│
└── users/                        # User profiles (optional)
    └── {user_id}/
        ├── email: string
        ├── name: string
        ├── organization: string
        ├── role: string
        ├── created_at: timestamp
        └── settings: map
```

### 6.2 Cloud Storage Structure

```
gs://legalmind-storage/
├── contract-pdfs/
│   └── {user_id}/
│       └── {contract_id}/
│           └── original.pdf
│
├── generated-documents/
│   └── {session_id}/
│       └── {document_id}/
│           ├── document.docx
│           └── document.pdf
│
└── exports/
    └── {user_id}/
        └── {export_id}/
            └── export.zip
```

---

## 7. API Endpoint Changes

### 7.1 Original Endpoints (to modify)

| Original Endpoint | New Endpoint | Changes |
|-------------------|--------------|---------|
| `POST /chat` | `POST /api/chat` | Change manager to LegalChatManager |
| `GET /workflow/status` | `DELETE` | Remove - not needed |
| `POST /workflow/run` | `DELETE` | Remove - not needed |
| `GET /risks/summary` | `GET /api/contracts/risk-summary` | Legal risk summary |
| `GET /schedule/comparison` | `GET /api/contracts` | Contract list |

### 7.2 New Endpoints (to add)

```python
# Contract Management
POST   /api/contracts              # Upload and analyze a new contract
GET    /api/contracts              # List all contracts
GET    /api/contracts/{id}         # Get contract details
DELETE /api/contracts/{id}         # Delete a contract
GET    /api/contracts/{id}/clauses # Get contract clauses
GET    /api/contracts/{id}/risks   # Get contract risk assessment

# Chat
POST   /api/chat                   # Send a message (existing)
GET    /api/chat/sessions          # List chat sessions
GET    /api/chat/sessions/{id}     # Get session history
DELETE /api/chat/sessions/{id}     # Delete a session

# Legal Research
POST   /api/research               # Perform legal research query
GET    /api/research/history       # Get research history

# Compliance
POST   /api/compliance/check       # Check contract compliance
GET    /api/compliance/rules       # List compliance rules
GET    /api/compliance/rules/{regulation} # Get rules for regulation

# Documents
GET    /api/documents              # List generated documents
GET    /api/documents/{id}         # Get document details
GET    /api/documents/{id}/download # Download document file

# Thinking Logs
GET    /api/thinking-logs          # List thinking logs
GET    /api/thinking-logs/{session_id} # Get logs for session

# Dashboard
GET    /api/dashboard/stats        # Get dashboard statistics
GET    /api/dashboard/risk-distribution # Get risk distribution
GET    /api/dashboard/compliance-status # Get compliance overview
```

---

## 8. Frontend Modifications

### 8.1 Page Changes

| Original Page | New Page | Changes |
|---------------|----------|---------|
| `/chat` | `/chat` | Update to legal context, add PDF upload |
| `/dashboard` | `/dashboard` | Change from geography map to risk/compliance charts |
| `/reports` | `/documents` | Rename, show legal documents |
| `/thinking-logs` | `/thinking-logs` | Minimal changes |
| N/A | `/contracts` | NEW - Contract list and viewer |
| N/A | `/research` | NEW - Legal research interface |

### 8.2 Component Changes

| Original Component | New Component | Changes |
|--------------------|---------------|---------|
| `MapChart.tsx` | `RiskChart.tsx` | Bar/pie charts for risk distribution |
| `ChatPage` | `LegalChatPage` | Add PDF upload, legal-specific UI |
| `chat-session-sidebar` | `legal-session-sidebar` | Show contract association |
| `data-table` | `data-table` | Minimal changes |

### 8.3 New Components Needed

```
components/
├── contract-upload.tsx       # PDF upload with drag-drop
├── contract-viewer.tsx       # Display contract with clause highlighting
├── clause-card.tsx           # Individual clause display with risk badge
├── risk-score-badge.tsx      # Visual risk indicator
├── compliance-status.tsx     # Compliance checklist display
├── citation-link.tsx         # Clickable legal citation
├── legal-document-preview.tsx # Preview generated memos
└── research-results.tsx      # Display search results with citations
```

---

## 9. File-by-File Transformation Guide

### 9.1 Files to DELETE (Azure-specific)

```
backend/
├── streamlit_app.py              # DELETE - Streamlit not needed
├── sql/                          # DELETE - Moving to Firestore
│   ├── create_table.sql
│   ├── create_data.sql
│   ├── create_stored_procedure.sql
│   ├── drop_all_tables_sp.sql
│   └── sp_get_country_risks.sql
└── test_scripts/
    ├── test_azure_storage.py     # DELETE - Azure-specific
    └── full_test_bing_agent.py   # DELETE - Azure-specific
```

### 9.2 Files to HEAVILY MODIFY

| File | Type of Changes |
|------|-----------------|
| `backend/config/settings.py` | Replace Azure config with Google config |
| `backend/agents/agent_definitions.py` | Complete rewrite for legal agents |
| `backend/agents/agent_manager.py` | Replace Azure AI with Gemini |
| `backend/agents/agent_strategies.py` | Adapt for legal query routing |
| `backend/managers/chatbot_manager.py` | Replace Semantic Kernel with Gemini orchestration |
| `backend/plugins/schedule_plugin.py` | Rewrite as `contract_tools.py` for Firestore |
| `backend/plugins/logging_plugin.py` | Update for Firestore |
| `backend/plugins/report_file_plugin.py` | Update for GCS and legal templates |
| `backend/api/endpoints.py` | Add new endpoints, update existing |
| `backend/requirements.txt` | Replace all dependencies |
| `frontend/app/chat/page.tsx` | Add legal-specific features |
| `frontend/app/dashboard/page.tsx` | Replace map with charts |

### 9.3 Files to CREATE

```
backend/
├── tools/                        # NEW - Gemini tool implementations
│   ├── __init__.py
│   ├── contract_tools.py         # Contract database operations
│   ├── clause_tools.py           # Clause extraction and analysis
│   ├── compliance_tools.py       # Compliance checking
│   ├── risk_tools.py             # Risk scoring
│   ├── document_tools.py         # Document generation
│   └── logging_tools.py          # Thinking logs
│
├── services/                     # NEW - Google service integrations
│   ├── __init__.py
│   ├── firestore_service.py      # Firestore operations
│   ├── storage_service.py        # Cloud Storage operations
│   └── gemini_service.py         # Gemini API wrapper
│
├── models/                       # NEW - Pydantic models
│   ├── __init__.py
│   ├── contract.py
│   ├── clause.py
│   ├── session.py
│   └── document.py
│
└── templates/                    # NEW - Document templates
    ├── legal_memo.md
    ├── contract_summary.md
    └── compliance_report.md

frontend/
├── app/
│   ├── contracts/               # NEW - Contract management
│   │   ├── page.tsx
│   │   ├── [id]/
│   │   │   └── page.tsx
│   │   └── upload/
│   │       └── page.tsx
│   │
│   └── research/                # NEW - Legal research
│       └── page.tsx
│
└── components/
    ├── contract-upload.tsx      # NEW
    ├── contract-viewer.tsx      # NEW
    ├── risk-charts.tsx          # NEW
    └── compliance-checklist.tsx # NEW
```

---

## 10. Environment Variables

### 10.1 Variables to REMOVE (Azure)

```env
# REMOVE THESE:
AZURE_AI_AGENT_PROJECT_NAME
AZURE_AI_AGENT_PROJECT_CONNECTION_STRING
AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME
AZURE_STORAGE_CONNECTION_STRING
AZURE_STORAGE_ACCOUNT_NAME
AZURE_STORAGE_CONTAINER
BING_CONNECTION_NAME
BING_SEARCH_API_KEY
DB_CONNECTION_STRING
```

### 10.2 Variables to ADD (Google)

```env
# ADD THESE:

# Gemini API
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash

# Google Cloud Project
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Firestore
FIRESTORE_DATABASE=(default)

# Cloud Storage
GCS_BUCKET_NAME=legalmind-storage
GCS_CONTRACT_PREFIX=contract-pdfs
GCS_DOCUMENT_PREFIX=generated-documents

# Application
APP_ENV=development
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000
```

---

## 11. Deployment Strategy

### 11.1 Local Development

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

### 11.2 Google Cloud Deployment

```bash
# 1. Enable required APIs
gcloud services enable \
  run.googleapis.com \
  firestore.googleapis.com \
  storage.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com

# 2. Create Firestore database
gcloud firestore databases create --location=us-central1

# 3. Create Cloud Storage bucket
gsutil mb gs://legalmind-storage

# 4. Deploy backend to Cloud Run
gcloud run deploy legalmind-backend \
  --source ./backend \
  --region us-central1 \
  --allow-unauthenticated

# 5. Deploy frontend to Firebase
cd frontend
npm run build
firebase deploy --only hosting
```

### 11.3 Dockerfile for Backend

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

---

## 12. Testing Plan

### 12.1 Unit Tests

```
tests/
├── test_tools/
│   ├── test_contract_tools.py
│   ├── test_clause_tools.py
│   ├── test_compliance_tools.py
│   └── test_risk_tools.py
│
├── test_agents/
│   ├── test_contract_parser.py
│   ├── test_legal_research.py
│   ├── test_compliance_checker.py
│   └── test_risk_assessment.py
│
└── test_services/
    ├── test_firestore_service.py
    ├── test_storage_service.py
    └── test_gemini_service.py
```

### 12.2 Integration Tests

- [ ] End-to-end contract upload and analysis
- [ ] Chat conversation with agent handoffs
- [ ] Document generation and download
- [ ] Legal research with citations

### 12.3 Sample Test Data

Create sample contracts for testing:
- `test_nda.pdf` - Simple NDA
- `test_msa.pdf` - Master Service Agreement
- `test_employment.pdf` - Employment contract
- `test_gdpr_compliant.pdf` - GDPR-compliant contract
- `test_gdpr_violation.pdf` - Contract with GDPR issues

---

## Appendix: Quick Reference

### Agent Names
- `CONTRACT_PARSER_AGENT`
- `LEGAL_RESEARCH_AGENT`
- `COMPLIANCE_CHECKER_AGENT`
- `RISK_ASSESSMENT_AGENT`
- `LEGAL_MEMO_AGENT`
- `ASSISTANT_AGENT`

### Thinking Stages
- `analysis_start`
- `document_review`
- `clause_extraction`
- `search_strategy`
- `search_execution`
- `compliance_check`
- `risk_assessment`
- `synthesis`
- `document_generation`

### Risk Levels
- `low` (0-25)
- `medium` (26-50)
- `high` (51-75)
- `critical` (76-100)

### Compliance Statuses
- `compliant`
- `partial`
- `non-compliant`

### Contract Statuses
- `draft`
- `active`
- `expired`
- `terminated`
