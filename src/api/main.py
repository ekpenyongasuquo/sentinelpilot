"""
SentinelPilot — Autonomous SOC Agent
Splunk Agentic Ops Hackathon 2026
FastAPI Backend — Splunk MCP Server + Splunk AI Assistant + Groq AI
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import httpx
import json
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="SentinelPilot API",
    description="Autonomous SOC Agent — Splunk MCP + Splunk AI Assistant + Groq AI",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Config ─────────────────────────────────────────────────────────────────────
SPLUNK_MCP_URL = os.getenv("SPLUNK_MCP_URL", "https://localhost:8089/services/mcp")
SPLUNK_TOKEN   = os.getenv("SPLUNK_TOKEN", "")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL     = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_URL       = "https://api.groq.com/openai/v1/chat/completions"

# ── Request Models ─────────────────────────────────────────────────────────────
class InvestigationRequest(BaseModel):
    time_range: Optional[str] = "-24h"
    index:      Optional[str] = "security"
    max_alerts: Optional[int] = 20

# ── MCP Session ────────────────────────────────────────────────────────────────
async def mcp_session(tool_name: str, arguments: dict) -> dict:
    """
    Full MCP session in one persistent connection:
    1. initialize (protocolVersion 2025-06-18)
    2. notifications/initialized
    3. tools/call
    Returns result dict.
    """
    headers = {
        "Authorization": f"Bearer {SPLUNK_TOKEN}",
        "Content-Type":  "application/json",
        "Accept":        "application/json, text/event-stream"
    }

    async with httpx.AsyncClient(verify=False, timeout=60.0) as client:

        # Step 1 — Initialize
        await client.post(SPLUNK_MCP_URL, json={
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "SentinelPilot", "version": "1.0.0"}
            }
        }, headers=headers)

        # Step 2 — Notification
        await client.post(SPLUNK_MCP_URL, json={
            "jsonrpc": "2.0",
            "method":  "notifications/initialized",
            "params":  {}
        }, headers=headers)

        # Step 3 — Tool call
        r = await client.post(SPLUNK_MCP_URL, json={
            "jsonrpc": "2.0", "id": 2,
            "method":  "tools/call",
            "params":  {"name": tool_name, "arguments": arguments}
        }, headers=headers)
        r.raise_for_status()

        data = r.json()

        # MCP level error
        if "error" in data:
            raise Exception(f"MCP error: {data['error']}")

        result = data.get("result", {})

        # Tool level error (isError flag)
        if result.get("isError"):
            content  = result.get("content", [{}])
            err_text = content[0].get("text", "Unknown tool error") if content else "Unknown"
            raise Exception(f"Tool error: {err_text}")

        # Extract result from content[0].text
        content = result.get("content", [])
        if content and content[0].get("type") == "text":
            try:
                return json.loads(content[0]["text"])
            except Exception:
                return {"raw": content[0]["text"]}

        return result.get("structuredContent", {})


# ── Fetch Alerts ───────────────────────────────────────────────────────────────
async def fetch_alerts(time_range: str, index: str, max_alerts: int):
    """
    Fetch security events from Splunk via MCP.

    Strategy:
    1. Try saia_generate_spl (Splunk AI Assistant / Hosted Models)
       to generate optimized SPL from natural language.
    2. If unavailable, fall back to standard SPL automatically.
    3. Execute SPL via splunk_run_query.

    When Splunk AI Assistant cloud activation completes,
    Step 1 succeeds automatically — zero code changes needed.
    """

    generated_spl = ""
    spl_source    = "fallback"

    # Step 1 — Try Splunk AI Assistant (Hosted Models)
    try:
        print("[SAIA] Attempting saia_generate_spl (Splunk Hosted Models)...")
        saia_result = await mcp_session("saia_generate_spl", {
            "prompt": (
                f"Search the {index} index for security threats, "
                f"failed logins, malware, suspicious processes, "
                f"lateral movement, data exfiltration, or anomalous "
                f"activity in the last {time_range}. "
                f"Return _time, source, sourcetype, host, and _raw. "
                f"Limit to {max_alerts} results sorted by time descending."
            )
        })

        # Extract SPL from various possible response keys
        raw = saia_result.get("raw", "")
        if raw and "index=" in raw:
            generated_spl = raw.strip()
            spl_source    = "splunk_ai_assistant"
        else:
            generated_spl = (
                saia_result.get("spl", "") or
                saia_result.get("query", "") or
                saia_result.get("search", "")
            )
            if generated_spl:
                spl_source = "splunk_ai_assistant"
            else:
                raise Exception("Empty SPL from saia_generate_spl")

        print(f"[SAIA] SPL generated: {generated_spl[:100]}")

    except Exception as e:
        print(f"[SAIA] Unavailable: {e}")
        print("[SAIA] Using fallback SPL...")

    # Step 2 — Fallback SPL
    if not generated_spl:
        generated_spl = (
            f"index={index} earliest={time_range} "
            f"| head {max_alerts} "
            f"| table _time, source, sourcetype, host, _raw"
        )
        spl_source = "fallback_spl"

    # Step 3 — Execute via splunk_run_query
    print(f"[MCP] Executing SPL (source: {spl_source})...")
    result = await mcp_session("splunk_run_query", {
        "query":         generated_spl,
        "earliest_time": time_range,
        "latest_time":   "now"
    })

    alerts = result.get("results", [])
    print(f"[MCP] Retrieved {len(alerts)} events")
    return alerts, generated_spl, spl_source


# ── Groq AI Correlation ────────────────────────────────────────────────────────
async def correlate_with_groq(alerts: list, spl_query: str) -> dict:
    """Correlate alerts with Groq AI and generate incident report."""

    system_prompt = """You are an expert SOC analyst AI.
Analyze Splunk security log data for threats, attack patterns, and anomalies.
Respond ONLY with valid JSON — no explanation, no markdown, no code fences.

Schema:
{
  "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
  "title": "Short descriptive incident title",
  "summary": "2-3 sentence plain English summary",
  "affected_systems": ["host1", "host2"],
  "attack_pattern": "MITRE ATT&CK technique name and ID",
  "recommended_actions": ["Action 1", "Action 2", "Action 3"],
  "confidence_score": 0.85
}"""

    user_message = (
        f"Analyze these {len(alerts)} Splunk security events "
        f"and generate a structured incident report.\n\n"
        f"EVENTS:\n{json.dumps(alerts[:10], indent=2)}\n\n"
        f"SPL QUERY:\n{spl_query}\n\n"
        f"Respond with JSON only."
    )

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type":  "application/json"
    }
    payload = {
        "model":   GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message}
        ],
        "temperature":     0.1,
        "max_tokens":      1000,
        "response_format": {"type": "json_object"}
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(GROQ_URL, json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()

    raw   = data["choices"][0]["message"]["content"]
    clean = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(clean)


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "name":         "SentinelPilot",
        "status":       "operational",
        "description":  "Autonomous SOC Agent — Splunk MCP + Splunk AI Assistant + Groq AI",
        "version":      "1.0.0",
        "token_loaded": bool(SPLUNK_TOKEN),
        "mcp_url":      SPLUNK_MCP_URL
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/splunk/test")
async def test_splunk_connection():
    """Test Splunk MCP Server connection."""
    try:
        headers = {
            "Authorization": f"Bearer {SPLUNK_TOKEN}",
            "Content-Type":  "application/json",
            "Accept":        "application/json, text/event-stream"
        }
        payload = {
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "SentinelPilot", "version": "1.0.0"}
            }
        }
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            r = await client.post(SPLUNK_MCP_URL, json=payload, headers=headers)
            return {
                "status":       "connected" if r.status_code == 200 else "error",
                "http_code":    r.status_code,
                "mcp_response": r.json()
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/splunk/tools")
async def list_tools():
    """List all available MCP tools."""
    try:
        headers = {
            "Authorization": f"Bearer {SPLUNK_TOKEN}",
            "Content-Type":  "application/json",
            "Accept":        "application/json, text/event-stream"
        }
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            await client.post(SPLUNK_MCP_URL, headers=headers, json={
                "jsonrpc": "2.0", "id": 1, "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "SentinelPilot", "version": "1.0.0"}
                }
            })
            await client.post(SPLUNK_MCP_URL, headers=headers, json={
                "jsonrpc": "2.0",
                "method":  "notifications/initialized",
                "params":  {}
            })
            r = await client.post(SPLUNK_MCP_URL, headers=headers, json={
                "jsonrpc": "2.0", "id": 2,
                "method":  "tools/list",
                "params":  {}
            })
            data  = r.json()
            tools = data.get("result", {}).get("tools", [])
            names = [t.get("name") for t in tools]
            return {
                "total":           len(tools),
                "tools":           names,
                "saia_available":  "saia_generate_spl" in names,
                "saia_tools":      [n for n in names if n.startswith("saia_")]
            }
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/splunk/indexes")
async def list_indexes():
    """List available Splunk indexes."""
    try:
        result = await mcp_session("splunk_get_indexes", {})
        return {"indexes": result}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/splunk/info")
async def splunk_info():
    """Get Splunk instance information."""
    try:
        result = await mcp_session("splunk_get_info", {})
        return result
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.post("/investigate")
async def run_investigation(request: InvestigationRequest):
    """
    Main endpoint — Full autonomous SOC investigation cycle:
    1. Generate SPL via Splunk AI Assistant (saia_generate_spl)
       OR fallback to standard SPL automatically
    2. Execute SPL via splunk_run_query (Splunk MCP Server)
    3. Correlate events with Groq AI
    4. Return structured incident report with MITRE ATT&CK
    """

    # Step 1 & 2 — Fetch from Splunk
    try:
        alerts, spl_query, spl_source = await fetch_alerts(
            request.time_range,
            request.index,
            request.max_alerts
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Splunk MCP error: {str(e)}")

    # No events found
    if not alerts:
        return {
            "incident_id":         f"INC-{uuid.uuid4().hex[:8].upper()}",
            "severity":            "INFO",
            "title":               "No events found",
            "summary":             (
                f"No events found in index={request.index} "
                f"for time range {request.time_range}."
            ),
            "affected_systems":    [],
            "attack_pattern":      "None",
            "recommended_actions": [
                "Verify index name is correct",
                "Try a wider time range",
                "Run load_sample_data.py to load test data"
            ],
            "splunk_query":   spl_query,
            "spl_source":     spl_source,
            "confidence_score": 1.0,
            "raw_alerts":     [],
            "total_events":   0
        }

    # Step 3 — Correlate with Groq
    try:
        analysis = await correlate_with_groq(alerts, spl_query)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Groq error: {str(e)}")

    # Step 4 — Return report
    return {
        "incident_id":         f"INC-{uuid.uuid4().hex[:8].upper()}",
        "severity":            analysis.get("severity", "HIGH"),
        "title":               analysis.get("title", "Security Incident Detected"),
        "summary":             analysis.get("summary", ""),
        "affected_systems":    analysis.get("affected_systems", []),
        "attack_pattern":      analysis.get("attack_pattern", "Unknown"),
        "recommended_actions": analysis.get("recommended_actions", []),
        "splunk_query":        spl_query,
        "spl_source":          spl_source,
        "confidence_score":    analysis.get("confidence_score", 0.5),
        "raw_alerts":          alerts,
        "total_events":        len(alerts)
    }