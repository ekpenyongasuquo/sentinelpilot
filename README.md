# SentinelPilot 🛡️

> **Autonomous SOC Agent powered by Splunk MCP + Claude AI**  
> Splunk Agentic Ops Hackathon 2026 — Security Track

SentinelPilot is an AI agent that autonomously investigates security alerts in Splunk — correlating logs, enriching threat context, generating human-readable incident reports, and triaging threats without a human writing a single SPL query.

**Think of it as a Level-1 SOC analyst that never sleeps.**

---

## 🎯 Problem

Security Operations Centers are overwhelmed. Analysts spend up to **40% of their time** on alert triage — manually querying Splunk, correlating events, and writing incident summaries. Most alerts are noise. But finding the real threats inside that noise takes hours that organizations don't have.

**Mean Time to Respond (MTTR) is too long. SentinelPilot fixes that.**

---

## ✅ Solution

SentinelPilot connects to Splunk via the **Splunk MCP Server**, pulls high-severity alerts automatically, uses **Claude AI** to reason across multiple events to identify attack chains, enriches findings with threat intelligence, and produces structured incident briefs — all autonomously.

### What it does:
- 🔎 **Auto-Alert Triage** — Polls Splunk for high-severity alerts using MCP tools
- 🧠 **LLM Correlation** — Reasons across multiple alerts to detect attack patterns
- 📋 **Incident Reports** — Generates structured briefs: what happened, affected systems, recommended actions
- 🤖 **Splunk Hosted Models** — Uses Splunk's native AI models for SPL generation
- 🔗 **Action Loop** — Optionally opens tickets in Jira/ServiceNow to close the response loop

---

## 🏗️ Architecture

See [`architecture-diagram.png`](./architecture-diagram.png) in the root of this repository.

```
User Dashboard (React)
        │
        ▼
FastAPI Backend (Python)
        │
        ├──► Splunk MCP Server ──► Splunk Enterprise
        │         (splunk_run_search, saia_generate_spl)
        │
        ├──► Claude API (claude-sonnet-4)
        │         (Alert correlation + report generation)
        │
        └──► Splunk Hosted Models
                  (SPL auto-generation)
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Splunk Enterprise (free trial or Developer License)
- Splunk MCP Server installed (Splunkbase App ID: 7931)
- Anthropic API key
- Node.js 18+ (for dashboard)

### 1. Clone the repository
```bash
git clone https://github.com/ekpenyongasuquo/sentinelpilot.git
cd sentinelpilot
```

### 2. Set up Python environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 3. Configure environment variables
```bash
cp .env.example .env
```
Edit `.env` with your credentials:
```env
SPLUNK_HOST=localhost
SPLUNK_PORT=8089
SPLUNK_TOKEN=your_splunk_bearer_token
ANTHROPIC_API_KEY=your_anthropic_api_key
SPLUNK_MCP_URL=http://localhost:8888/mcp
```

### 4. Configure Splunk MCP Server
- In Splunk Web, go to **Apps → Splunk MCP Server → Configuration**
- Enable the MCP Server
- Create a service account with the `mcp_user` role
- Copy the bearer token to your `.env` file

### 5. Run the backend
```bash
uvicorn src.api.main:app --reload --port 8000
```

### 6. Run the dashboard
```bash
cd src/dashboard
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## 📁 Project Structure

```
sentinelpilot/
├── src/
│   ├── agent/
│   │   ├── sentinel_agent.py      # Core agent loop
│   │   ├── splunk_mcp_client.py   # MCP Server connection
│   │   ├── alert_correlator.py    # LLM correlation logic
│   │   └── report_generator.py    # Incident report builder
│   ├── api/
│   │   ├── main.py                # FastAPI app entry point
│   │   ├── routes/
│   │   │   ├── alerts.py          # Alert endpoints
│   │   │   ├── investigations.py  # Investigation endpoints
│   │   │   └── reports.py         # Report endpoints
│   │   └── models.py              # Pydantic data models
│   └── dashboard/                 # React frontend
│       ├── src/
│       │   ├── App.jsx
│       │   ├── components/
│       │   └── pages/
│       └── package.json
├── tests/
├── docs/
├── architecture-diagram.png       # Required by hackathon rules
├── requirements.txt
├── .env.example
├── LICENSE                        # MIT License
└── README.md
```

---

## 🔌 Splunk MCP Tools Used

| Tool | Purpose |
|------|---------|
| `splunk_run_search` | Execute SPL queries to fetch alerts |
| `saia_generate_spl` | Auto-generate SPL using Splunk Hosted Models |
| `get_knowledge_objects` | Retrieve correlation rules and saved searches |
| `list_indexes` | Discover available data sources |

---

## 🧠 AI Components

| Component | Technology |
|-----------|-----------|
| Alert Correlation | Claude claude-sonnet-4 via Anthropic API |
| SPL Generation | Splunk AI Assistant (Hosted Models) |
| Incident Summarization | Claude claude-sonnet-4 |
| Threat Classification | Claude claude-sonnet-4 |

---

## 📊 Example Incident Report Output

```json
{
  "incident_id": "INC-2026-0042",
  "severity": "HIGH",
  "title": "Possible Lateral Movement — Credential Stuffing Pattern Detected",
  "summary": "Multiple failed login attempts from 3 external IPs targeting
               the same internal service account across 4 hosts over 2 hours.",
  "affected_systems": ["host-srv-01", "host-srv-04", "host-db-02"],
  "attack_pattern": "T1110.003 - Password Spraying",
  "recommended_actions": [
    "Isolate host-srv-01 immediately",
    "Reset credentials for affected service account",
    "Block source IPs at perimeter firewall"
  ],
  "splunk_query": "index=security sourcetype=WinEventLog EventCode=4625 ...",
  "confidence_score": 0.91
}
```

---

## 🏆 Hackathon Track

**Primary:** Security  
**Special Awards Targeted:**
- Best Use of Splunk MCP Server
- Best Use of Splunk Hosted Models

---

## 📄 License

MIT License — see [LICENSE](./LICENSE) for details.

---

## 👤 Author

**Ekpenyong Asuquo**  
GitHub: [@ekpenyongasuquo](https://github.com/ekpenyongasuquo)  
Hugging Face: [emfon](https://huggingface.co/emfon)
