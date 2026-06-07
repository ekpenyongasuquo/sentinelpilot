# SentinelPilot — Architecture Diagram

> **Autonomous SOC Agent · Splunk MCP Server + Splunk AI Assistant + Groq AI**  
> Splunk Agentic Ops Hackathon 2026 — Security Track

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE LAYER                             │
│                                                                         │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │              SentinelPilot Dashboard (dashboard.html)            │  │
│   │   • Investigation controls  • Real-time agent activity log       │  │
│   │   • Incident report cards   • MITRE ATT&CK visualization        │  │
│   │   • Confidence scoring      • Raw events table                   │  │
│   └────────────────────────────┬─────────────────────────────────────┘  │
└────────────────────────────────┼────────────────────────────────────────┘
                                 │ HTTP REST (POST /investigate)
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        AGENT ORCHESTRATION LAYER                        │
│                                                                         │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │              FastAPI Backend (src/api/main.py)                   │  │
│   │                                                                  │  │
│   │   Investigation Cycle:                                           │  │
│   │   1. Open MCP session (initialize + notifications/initialized)   │  │
│   │   2. Call saia_generate_spl → generate optimized SPL            │  │
│   │   3. Call splunk_run_query → fetch security events              │  │
│   │   4. Send events to Groq AI → correlate + classify              │  │
│   │   5. Return structured incident report                          │  │
│   └────┬─────────────────────────┬────────────────────────┬─────────┘  │
└────────┼─────────────────────────┼────────────────────────┼────────────┘
         │                         │                        │
         │ JSON-RPC 2.0            │ JSON-RPC 2.0           │ HTTPS
         │ Bearer Token Auth       │ Bearer Token Auth      │ REST API
         ▼                         ▼                        ▼
┌─────────────────┐   ┌────────────────────────┐   ┌──────────────────┐
│  SPLUNK MCP     │   │  SPLUNK AI ASSISTANT   │   │   GROQ AI API    │
│  SERVER 1.2.0   │   │  (Hosted Models)       │   │                  │
│                 │   │                        │   │  llama-3.3-70b   │
│  Tools Used:    │   │  Tools Used:           │   │  -versatile      │
│                 │   │                        │   │                  │
│  splunk_        │   │  saia_generate_spl     │   │  • Alert         │
│  run_query      │   │  → Natural language    │   │    correlation   │
│                 │   │    to SPL generation   │   │  • MITRE ATT&CK  │
│  splunk_        │   │                        │   │    classification│
│  get_indexes    │   │  saia_explain_spl      │   │  • Incident      │
│                 │   │  → SPL explanation     │   │    report        │
│  splunk_        │   │                        │   │    generation    │
│  get_info       │   │  saia_optimize_spl     │   │  • Confidence    │
│                 │   │  → Query optimization  │   │    scoring       │
│  splunk_get_    │   │                        │   │                  │
│  knowledge_     │   │  saia_ask_splunk_      │   └────────┬─────────┘
│  objects        │   │  question              │            │
│                 │   │  → Data Q&A            │            │
└────────┬────────┘   └────────────┬───────────┘            │
         │                         │                        │
         │ SPL Query               │ Cloud Connected        │ Structured
         │ Execution               │ via Activation Token   │ JSON Report
         ▼                         ▼                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                    │
│                                                                         │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │              Splunk Enterprise 10.2.3                            │  │
│   │              Developer License (10GB, 6 months)                  │  │
│   │                                                                  │  │
│   │   Indexes:                                                       │  │
│   │   • security  — Windows Events, Linux Syslog, Network Streams   │  │
│   │   • _internal — Splunk platform operational logs                 │  │
│   │                                                                  │  │
│   │   Event Types:                                                   │  │
│   │   • WinEventLog:Security  (EventCodes 4624,4625,4663,4672,4688) │  │
│   │   • linux_secure          (SSH login attempts)                   │  │
│   │   • stream:tcp/http/dns   (Network traffic anomalies)           │  │
│   │   • symantec:ep:security  (Antivirus/malware detections)        │  │
│   └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Summary

```
User clicks Investigate
        │
        ▼
FastAPI opens MCP session (initialize handshake)
        │
        ├──► saia_generate_spl (Splunk AI Assistant)
        │         Natural language → optimized SPL
        │         Fallback: standard SPL if unavailable
        │
        ├──► splunk_run_query (Splunk MCP Server)
        │         Execute SPL → retrieve security events
        │
        ├──► Groq AI (llama-3.3-70b-versatile)
        │         Correlate events → MITRE ATT&CK classification
        │         Generate structured incident report
        │
        └──► Return to Dashboard
                  Render incident card with severity,
                  affected systems, recommended actions,
                  confidence score, raw events table
```

---

## Component Summary

| Component | Technology | Purpose |
|---|---|---|
| Dashboard | HTML/CSS/JavaScript | SOC analyst interface |
| Backend | Python FastAPI + uvicorn | Agent orchestration |
| MCP Client | httpx + JSON-RPC 2.0 | Splunk connectivity |
| SPL Generation | saia_generate_spl (Splunk AI) | Natural language to SPL |
| Data Query | splunk_run_query (Splunk MCP) | Security event retrieval |
| AI Correlation | Groq llama-3.3-70b | Threat analysis + reporting |
| Data Platform | Splunk Enterprise 10.2.3 | Security data indexing |
| Deployment | Render.com | Cloud hosting |

---

## Security Architecture

- **MCP Authentication**: Encrypted bearer token generated inside Splunk MCP Server app
- **REST Authentication**: Separate Splunk API token for data ingestion
- **SSL**: Self-signed certificate on localhost (verify=False for development)
- **No credentials in code**: All secrets loaded from `.env` file (excluded from repo via `.gitignore`)

---

*SentinelPilot v1.0 · Ekpenyong Mfon · Splunk Agentic Ops Hackathon 2026*
