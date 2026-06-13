# SentinelPilot 🛡️

> **Autonomous SOC Agent powered by Splunk MCP Server + Splunk AI Assistant + Groq AI**  
> Splunk Agentic Ops Hackathon 2026 — Security Track

SentinelPilot is an AI agent that autonomously investigates security alerts in Splunk — correlating logs, generating human-readable incident reports, and triaging threats without a human writing a single SPL query.

**Think of it as a Level-1 SOC analyst that never sleeps.**

---

## 🎯 Problem

Security Operations Centers are overwhelmed. Analysts spend up to **40% of their time** on alert triage — manually querying Splunk, correlating events, and writing incident summaries. Most alerts are noise. But finding the real threats inside that noise takes hours that organizations don't have.

**Mean Time to Respond (MTTR) is too long. SentinelPilot fixes that.**

---

## ✅ Solution

SentinelPilot connects to Splunk via the **Splunk MCP Server**, uses **Splunk AI Assistant** to generate optimized SPL queries from natural language, fetches security events automatically, uses **Groq AI** to reason across multiple events and identify attack chains, and produces structured incident briefs — all autonomously.

### What it does:
- 🔎 **Auto-Alert Triage** — Fetches security events from Splunk using MCP tools
- 🤖 **Splunk AI Assistant** — Uses `saia_generate_spl` (Splunk Hosted Models) to generate optimized SPL from natural language
- 🧠 **AI Correlation** — Reasons across multiple alerts to detect attack patterns and MITRE ATT&CK techniques
- 📋 **Incident Reports** — Generates structured briefs: severity, affected systems, recommended actions, confidence score
- 🖥️ **Tactical Dashboard** — Real-time SOC interface showing the agent working step by step

---

## 🏗️ Architecture

See [`architecture_diagram.md`](./architecture_diagram.md) and [`architecture_diagram.png`](./architecture_diagram.png) at the root of this repository.

```
User Dashboard (dashboard.html)
        │
        ▼ HTTP REST
FastAPI Backend (src/api/main.py)
        │
        ├──► Splunk MCP Server (JSON-RPC 2.0)
        │         saia_generate_spl  → Splunk AI Assistant (Hosted Models)
        │         splunk_run_query   → Fetch security events
        │         splunk_get_indexes → Discover data sources
        │         splunk_get_info    → Instance metadata
        │
        ├──► Groq AI API
        │         llama-3.3-70b-versatile
        │         Alert correlation + MITRE ATT&CK classification
        │         Structured incident report generation
        │
        └──► Splunk Enterprise 10.2.3
                  security index — Windows Events, Network, AV logs
                  _internal index — Platform operational logs
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Splunk Enterprise 10.x (free trial or Developer License)
- Splunk MCP Server installed (Splunkbase App ID: 7931)
- Splunk AI Assistant installed (Splunkbase)
- Groq API key (free at console.groq.com)

### 1. Clone the repository
```bash
git clone https://github.com/ekpenyongasuquo/sentinelpilot.git
cd sentinelpilot
```

### 2. Set up Python environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac
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
SPLUNK_TOKEN=your_splunk_mcp_encrypted_token
SPLUNK_MCP_URL=https://localhost:8089/services/mcp
SPLUNK_REST_TOKEN=your_splunk_rest_api_token
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
APP_PORT=8001
```

### 4. Configure Splunk MCP Server
- In Splunk Web go to **Apps → Splunk MCP Server**
- Enable Token Authentication: **Settings → Tokens → Enable**
- Create `mcp_user` role: **Settings → Roles → New Role**
  - Add capabilities: `mcp_tool_admin`, `mcp_tool_execute`
- Assign `mcp_user` role to your admin user
- Generate MCP Encrypted Token from inside the MCP Server app
- Copy token to `SPLUNK_TOKEN` in your `.env` file

### 5. Load sample security data
```bash
python load_sample_data.py
```

### 6. Run the backend
```bash
uvicorn src.api.main:app --reload --port 8001
```

### 7. Open the dashboard
Open `dashboard.html` in your browser.

---

## 📁 Project Structure

```
sentinelpilot/
├── src/
│   └── api/
│       └── main.py                # FastAPI backend — agent orchestration
├── docs/
│   ├── DEMO_SCRIPT.md             # Demo video script
│   └── DEVPOST_SUBMISSION.md      # Full Devpost submission text
├── architecture_diagram.md        # Architecture diagram (Markdown)
├── architecture_diagram.png       # Architecture diagram (PNG)
├── dashboard.html                 # Tactical SOC dashboard
├── load_sample_data.py            # Sample security data loader
├── test_mcp.py                    # MCP connection test script
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variables template
├── LICENSE                        # MIT License
└── README.md
```

---

## 🔌 Splunk MCP Tools Used

| Tool | Type | Purpose |
|------|------|---------|
| `saia_generate_spl` | Splunk AI Assistant | Generate optimized SPL from natural language |
| `saia_explain_spl` | Splunk AI Assistant | Explain SPL queries |
| `saia_optimize_spl` | Splunk AI Assistant | Optimize SPL performance |
| `saia_ask_splunk_question` | Splunk AI Assistant | Answer questions about Splunk data |
| `splunk_run_query` | Splunk MCP Server | Execute SPL to fetch security events |
| `splunk_get_indexes` | Splunk MCP Server | Discover available data sources |
| `splunk_get_info` | Splunk MCP Server | Retrieve Splunk instance metadata |
| `splunk_get_knowledge_objects` | Splunk MCP Server | Access saved searches |

---

## 🧠 AI Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| SPL Generation | Splunk AI Assistant (`saia_generate_spl`) | Natural language to optimized SPL |
| Alert Correlation | Groq `llama-3.3-70b-versatile` | Identify attack chains |
| Incident Summarization | Groq `llama-3.3-70b-versatile` | Plain English summaries |
| Threat Classification | Groq `llama-3.3-70b-versatile` | MITRE ATT&CK mapping |

---

## 📊 Example Incident Report Output

```json
{
  "incident_id": "INC-DFA1E8BB",
  "severity": "CRITICAL",
  "title": "Ransomware and Lateral Movement Detected",
  "summary": "Multiple failed login attempts, mass file encryption, and unusual privilege assignments detected. A Trojan was quarantined and DNS tunneling with data exfiltration to Russia observed.",
  "affected_systems": ["DESKTOP-MIM6KVQ", "SERVER-DB-01"],
  "attack_pattern": "T1486 - Data Encrypted for Impact, T1021 - Remote Services",
  "recommended_actions": [
    "Isolate affected systems immediately",
    "Run full antivirus scan on all systems",
    "Change all passwords and enable MFA",
    "Block external IP 185.220.101.47 at firewall"
  ],
  "splunk_query": "index=security earliest=-24h | head 10 | table _time, source, sourcetype, host, _raw",
  "spl_source": "splunk_ai_assistant",
  "confidence_score": 0.95,
  "total_events": 10
}
```

---

## 🏆 Hackathon Tracks

**Primary Track:** Security  
**Special Awards Targeted:**
- Best Use of Splunk MCP Server ($1,000)
- Best Use of Splunk Hosted Models ($1,000)

---

## 📄 License

MIT License — see [LICENSE](./LICENSE) for details.

---

## 👤 Author

**Ekpenyong Mfon**  
GitHub: [@ekpenyongasuquo](https://github.com/ekpenyongasuquo)  
Devpost: [ekpenyongasuquo](https://devpost.com/ekpenyongasuquo)
