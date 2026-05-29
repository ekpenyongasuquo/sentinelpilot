"""
SentinelPilot — Autonomous SOC Agent
Splunk Agentic Ops Hackathon 2026
FastAPI Backend using Groq AI + Splunk MCP Server
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
    description="Autonomous SOC Agent — Splunk MCP + Groq AI",
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

# Confirmed tool names from Splunk MCP Server 1.2.0
# splunk_get_info, splunk_get_indexes, splunk_get_index_info
# splunk_get_user_list, splunk_get_user_info, splunk_run_query
# splunk_get_metadata, splunk_get_kv_store_collections
# splunk_get_knowledge_objects, splunk_run_saved_search

# ── Request Models ─────────────────────────────────────────────────────────────
class InvestigationRequest(BaseModel):
    time_range: Optional[str] = "-24h"
    index:      Optional[str] = "_internal"
    max_alerts: Optional[int] = 20

# ── MCP Session ────────────────────────────────────────────────────────────────
async def mcp_session(tool_name: str, arguments: dict) -> dict:
    """
    Full MCP session in one persistent connection:
    1. initialize
    2. notifications/initialized
    3. tools/call
    Returns the result dict.
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
        if "error" in data:
            raise HTTPException(status_code=500, detail=f"MCP error: {data['error']}")

        # Extract result — content[0].text is JSON string
        result = data.get("result", {})
        content = result.get("content", [])
        if content and content[0].get("type") == "text":
            try:
                return json.loads(content[0]["text"])
            except Exception:
                return {}
        return result.get("structuredContent", {})


# ── Fetch Alerts ───────────────────────────────────────────────────────────────
async def fetch_alerts(time_range: str, index: str, max_alerts: int):
    """Fetch events from Splunk via splunk_run_query."""

    spl = (
        f"index={index} earliest={time_range} "
        f"| head {max_alerts} "
        f"| table _time, source, sourcetype, host, _raw"
    )

    result = await mcp_session("splunk_run_query", {
        "query":         spl,
        "earliest_time": time_range,
        "latest_time":   "now"
    })

    alerts = result.get("results", [])
    return alerts, spl


# ── Groq AI Correlation ────────────────────────────────────────────────────────
async def correlate_with_groq(alerts: list, spl_query: str) -> dict:
    """Correlate alerts with Groq AI and generate incident report."""

    system_prompt = """You are an expert SOC analyst AI.
Analyze Splunk log data for security threats, anomalies, and patterns.
Respond ONLY with valid JSON — no explanation, no markdown, no code fences.

Schema:
{
  "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
  "title": "Short incident title",
  "summary": "2-3 sentence plain English summary",
  "affected_systems": ["host1", "host2"],
  "attack_pattern": "MITRE ATT&CK technique or General Anomaly",
  "recommended_actions": ["Action 1", "Action 2", "Action 3"],
  "confidence_score": 0.85
}"""

    user_message = (
        f"Analyze these {len(alerts)} Splunk events and generate a security incident report.\n\n"
        f"EVENTS SAMPLE:\n{json.dumps(alerts[:10], indent=2)}\n\n"
        f"SPL QUERY:\n{spl_query}\n\n"
        f"Respond with JSON only."
    )

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type":  "application/json"
    }
    payload = {
        "model": GROQ_MODEL,
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

    raw = data["choices"][0]["message"]["content"]
    clean = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(clean)


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "name":         "SentinelPilot",
        "status":       "operational",
        "description":  "Autonomous SOC Agent — Splunk MCP + Groq AI",
        "version":      "1.0.0",
        "token_loaded": bool(SPLUNK_TOKEN),
        "mcp_url":      SPLUNK_MCP_URL
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/splunk/test")
async def test_splunk_connection():
    """Test Splunk MCP connection."""
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
    """Get Splunk instance info."""
    try:
        result = await mcp_session("splunk_get_info", {})
        return result
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.post("/investigate")
async def run_investigation(request: InvestigationRequest):
    """
    Main endpoint — full autonomous investigation cycle:
    1. Fetch events from Splunk via MCP
    2. Correlate and analyze with Groq AI
    3. Return structured incident report
    """

    # Step 1 — Fetch from Splunk
    try:
        alerts, spl_query = await fetch_alerts(
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
            "summary":             f"No events found in index={request.index} for {request.time_range}.",
            "affected_systems":    [],
            "attack_pattern":      "None",
            "recommended_actions": ["Continue monitoring", "Check index name", "Verify data ingestion"],
            "splunk_query":        spl_query,
            "confidence_score":    1.0,
            "raw_alerts":          [],
            "total_events":        0
        }

    # Step 2 — Correlate with Groq
    try:
        analysis = await correlate_with_groq(alerts, spl_query)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Groq error: {str(e)}")

    # Step 3 — Return report
    return {
        "incident_id":         f"INC-{uuid.uuid4().hex[:8].upper()}",
        "severity":            analysis.get("severity", "HIGH"),
        "title":               analysis.get("title", "Security Incident Detected"),
        "summary":             analysis.get("summary", ""),
        "affected_systems":    analysis.get("affected_systems", []),
        "attack_pattern":      analysis.get("attack_pattern", "Unknown"),
        "recommended_actions": analysis.get("recommended_actions", []),
        "splunk_query":        spl_query,
        "confidence_score":    analysis.get("confidence_score", 0.5),
        "raw_alerts":          alerts,
        "total_events":        len(alerts)
    }