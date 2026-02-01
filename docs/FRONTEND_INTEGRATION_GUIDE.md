# Frontend Integration Guide

**Status**: Backend Complete ✅ | Ready for Frontend Consumption

---

## 🎯 What Frontend Needs to Know

### Base URLs
```javascript
const API_BASE = 'http://localhost:8000/api';
const WS_BASE = 'ws://localhost:8000/ws';
```

### Quick Start: Chat Interface

#### Option 1: REST API
```javascript
// Create session
const sessionId = await fetch(`${API_BASE}/chat/session`, {
  method: 'POST'
}).then(r => r.json()).then(d => d.session_id);

// Send message
const response = await fetch(`${API_BASE}/chat`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: sessionId,
    message: "What does this contract say about termination?",
    contract_id: "contract-123" // optional
  })
});

const data = await response.json();
console.log(data.message);      // Agent response
console.log(data.agent);        // Agent name
console.log(data.citations);    // References/citations
```

#### Option 2: WebSocket (Real-time)
```javascript
const ws = new WebSocket(`${WS_BASE}/chat`);

ws.onopen = () => {
  ws.send(JSON.stringify({
    session_id: "session-123",
    message: "What are the risks in this contract?",
    contract_id: "contract-123"
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'ack') {
    console.log('Processing...');
  }
  if (data.type === 'response') {
    console.log('Agent:', data.agent);
    console.log('Message:', data.message);
    console.log('Tools used:', data.tools_used);
  }
  if (data.type === 'error') {
    console.error('Error:', data.error);
  }
};
```

---

## 📋 Common Frontend Tasks

### 1. Upload Contract
```javascript
const formData = new FormData();
formData.append('file', pdfFile);
formData.append('name', 'Service Agreement');
formData.append('contract_type', 'Service Agreement');
formData.append('parties', JSON.stringify(['Company A', 'Company B']));
formData.append('notes', 'Important vendor contract');

const response = await fetch(`${API_BASE}/contracts/upload`, {
  method: 'POST',
  body: formData
});

const data = await response.json();
const contractId = data.contract_id;
```

### 2. Get Contract List
```javascript
const response = await fetch(
  `${API_BASE}/contracts?status=analyzed&contract_type=Service%20Agreement`
);
const { contracts } = await response.json();

contracts.forEach(contract => {
  console.log(contract.name);      // Contract name
  console.log(contract.type);      // Contract type
  console.log(contract.parties);   // Involved parties
  console.log(contract.uploaded_at); // Timestamp
  console.log(contract.status);    // Current analysis status
});
```

### 3. Get Contract Details & Analysis
```javascript
const response = await fetch(`${API_BASE}/contracts/{contract_id}`);
const { contract } = await response.json();

console.log(contract.name);
console.log(contract.type);
console.log(contract.parties);
console.log(contract.notes);
console.log(contract.file_url);

// Get extracted clauses
const clausesResponse = await fetch(
  `${API_BASE}/contracts/{contract_id}/clauses`
);
const { clauses } = await clausesResponse.json();
```

### 4. Run Workflow
```javascript
const response = await fetch(`${API_BASE}/workflow/run`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: "session-123",
    workflow_name: "contract_review", // or "compliance_audit", "risk_analysis"
    contract_id: "contract-123"
  })
});

const { results, messages } = await response.json();

messages.forEach(msg => {
  console.log(`${msg.agent}: ${msg.content}`);
});
```

### 5. Workflow Progress (WebSocket)
```javascript
const ws = new WebSocket(`${WS_BASE}/workflow`);

ws.onopen = () => {
  ws.send(JSON.stringify({
    session_id: "session-123",
    workflow_name: "contract_review",
    contract_id: "contract-123"
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'start') {
    console.log(`Starting workflow: ${data.workflow}`);
  }
  
  if (data.type === 'progress') {
    console.log(`Running ${data.agent} (${data.step}/${data.total})`);
    updateProgressBar(data.step, data.total);
  }
  
  if (data.type === 'agent_complete') {
    console.log(`${data.agent} completed:`);
    console.log(data.message); // Agent response
  }
  
  if (data.type === 'complete') {
    console.log('Workflow finished');
    data.results.forEach(r => {
      console.log(`${r.agent_id}: ${r.message}`);
    });
  }
};
```

### 6. Get Compliance Frameworks
```javascript
const response = await fetch(`${API_BASE}/compliance/frameworks`);
const { frameworks } = await response.json();

frameworks.forEach(fw => {
  console.log(`${fw.name}: ${fw.requirement_count} requirements`);
});
// Output:
// GDPR: 8 requirements
// HIPAA: 6 requirements
// CCPA: 5 requirements
// SOX: 4 requirements
```

### 7. Check Compliance
```javascript
const response = await fetch(
  `${API_BASE}/compliance/check/{contract_id}?framework=GDPR`
);
const { compliance } = await response.json();

console.log(compliance.status);        // "compliant", "partial", "non_compliant"
console.log(compliance.score);         // 0-100
console.log(compliance.findings);      // Array of issues
console.log(compliance.recommendations); // Array of fixes
```

### 8. Risk Assessment
```javascript
const response = await fetch(`${API_BASE}/risk/assess/{contract_id}`);
const { risk_assessment } = await response.json();

console.log(risk_assessment.overall_score); // 0-100
console.log(risk_assessment.level);        // "LOW", "MEDIUM", "HIGH", "CRITICAL"
console.log(risk_assessment.risks);        // Array of identified risks
console.log(risk_assessment.recommendations); // Mitigation steps
```

### 9. List Generated Documents
```javascript
const response = await fetch(
  `${API_BASE}/documents?contract_id={contract_id}`
);
const { documents } = await response.json();

documents.forEach(doc => {
  console.log(doc.title);        // Document title
  console.log(doc.type);         // "memo", "summary", "report"
  console.log(doc.created_at);   // Timestamp
  console.log(doc.file_path);    // For download URL
});
```

### 10. Download Document
```javascript
const response = await fetch(
  `${API_BASE}/documents/{document_id}/download`
);
const { download_url, filename } = await response.json();

// Create download link
const a = document.createElement('a');
a.href = download_url;
a.download = filename;
a.click();
```

---

## 🔧 Response Format Reference

### Chat Response
```json
{
  "success": true,
  "message": "The contract does not explicitly state a termination clause...",
  "agent": "Contract Parser",
  "agent_id": "CONTRACT_PARSER_AGENT",
  "citations": [
    {
      "text": "relevant text from contract",
      "page": 1,
      "section": "5.1"
    }
  ],
  "tools_used": ["extract_contract_text", "get_contract"],
  "session_id": "session-123"
}
```

### Contract List Response
```json
{
  "success": true,
  "contracts": [
    {
      "id": "contract-123",
      "name": "Service Agreement",
      "type": "Service Agreement",
      "parties": ["Company A", "Company B"],
      "filename": "service_agreement_2025.pdf",
      "file_url": "https://storage.googleapis.com/...",
      "uploaded_at": "2025-02-01T10:30:00Z",
      "status": "analyzed"
    }
  ],
  "count": 1
}
```

### Workflow Response
```json
{
  "success": true,
  "workflow": "contract_review",
  "contract_id": "contract-123",
  "results": {
    "CONTRACT_PARSER_AGENT": {
      "message": "Parsed contract...",
      "citations": [...],
      "tools_used": [...]
    },
    "COMPLIANCE_CHECKER_AGENT": {
      "message": "Compliance check...",
      "citations": [...],
      "tools_used": [...]
    },
    "RISK_ASSESSMENT_AGENT": {
      "message": "Risk assessment...",
      "citations": [...],
      "tools_used": [...]
    },
    "LEGAL_MEMO_AGENT": {
      "message": "Generated memo...",
      "citations": [...],
      "tools_used": [...]
    }
  },
  "messages": [
    {
      "agent": "Contract Parser",
      "content": "Parsed contract..."
    },
    ...
  ]
}
```

---

## 📊 Agent Selection (Automatic)

Frontend doesn't need to select agents - the backend does it automatically based on the query:

```javascript
// These queries trigger different agents automatically:

"What does the contract say?" 
  → CONTRACT_PARSER_AGENT

"Is this GDPR compliant?"
  → COMPLIANCE_CHECKER_AGENT

"What are the risks?"
  → RISK_ASSESSMENT_AGENT

"Generate a summary"
  → LEGAL_MEMO_AGENT

"What does 'force majeure' mean?"
  → LEGAL_RESEARCH_AGENT

"How can I help you?"
  → ASSISTANT_AGENT
```

---

## 🎨 Suggested Frontend Components

### Chat Interface
- Message input field
- Message history display
- Agent indicator badge
- Citation popup on hover
- Loading indicator during processing
- WebSocket status indicator

### Contract Management
- File upload drop zone
- Contract list with filters
- Contract detail card
- Analysis results panel
- Document download button
- Clause viewer

### Workflow Interface
- Workflow template selector
- Progress indicator
- Agent execution timeline
- Results summary panel
- Export functionality

### Analysis Results
- Compliance score gauge
- Risk score gauge
- Findings list with severity
- Recommendations panel
- Audit trail/history

---

## ⚡ Performance Tips

### For Chat
- Use WebSocket for real-time responses
- Implement message pagination for history
- Cache agent responses for repeated queries
- Show loading states during processing

### For Contracts
- Lazy load contract list
- Paginate large document lists
- Cache Firestore results locally
- Pre-process PDFs during upload

### For Workflows
- Use WebSocket for progress updates
- Show agent execution timeline
- Cache workflow templates
- Stream results as agents complete

---

## 🔐 Security Considerations

### API Key Protection
```javascript
// ❌ DON'T - expose API keys in frontend
const apiKey = "secret-key-123";

// ✅ DO - use backend proxy or environment variables
const response = await fetch('/api/chat', {...});
```

### CORS Headers
- Backend already configured for all origins
- Production: configure specific origins
- WebSocket connections don't use CORS

### Data Validation
- Backend validates all inputs
- Frontend can add extra validation for UX
- Sanitize file uploads before processing

---

## 🚀 Deployment Checklist

### Before Frontend Integration
- ✅ Backend running and tested
- ✅ Environment variables configured
- ✅ Google Cloud credentials set up
- ✅ Firestore database initialized
- ✅ Cloud Storage bucket created
- ✅ API endpoints responding

### Frontend Setup
- [ ] Update API_BASE URL for environment
- [ ] Update WS_BASE URL for environment
- [ ] Add environment variables to .env.local
- [ ] Test with Postman first
- [ ] Implement error handling
- [ ] Add loading states
- [ ] Test with sample contracts

### Production Ready
- [ ] SSL/TLS certificates
- [ ] Cloud Run deployment
- [ ] Frontend build optimization
- [ ] Database backups configured
- [ ] Error logging/monitoring
- [ ] Rate limiting enabled

---

## 📞 Troubleshooting

### API Not Responding
```javascript
// Check health endpoint
fetch('http://localhost:8000/api/health')
  .then(r => r.json())
  .then(d => console.log(d))
  // Should return { "status": "healthy" }
```

### WebSocket Connection Failed
```javascript
// Check browser console for CORS errors
// Verify backend is running on correct port
// Check firewall rules
ws://localhost:8000/ws/chat
```

### File Upload Failing
```javascript
// Check file size (must be PDF)
// Verify content-type headers
// Check Cloud Storage permissions
// Verify bucket name in .env
```

### Agent Not Responding
```javascript
// Check Gemini API key in .env
// Verify internet connection
// Check Firestore connectivity
// Review server logs: tail -f server.log
```

---

## 🔗 Useful Resources

- API Documentation: http://localhost:8000/docs
- Firestore Console: https://console.firebase.google.com
- Google Cloud Console: https://console.cloud.google.com
- Gemini API Docs: https://ai.google.dev
- Backend Test Suite: `python test_backend.py`

---

**Ready for Frontend Integration!** 🚀

All 31 endpoints are operational and tested. Frontend can begin integration immediately.
