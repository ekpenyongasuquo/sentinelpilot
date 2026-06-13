"""
SentinelPilot — MCP Test Script
Tests Splunk AI Assistant saia_generate_spl tool
"""

import asyncio
import httpx
from dotenv import load_dotenv
import os, json

load_dotenv()
TOKEN = os.getenv("SPLUNK_TOKEN")
URL   = os.getenv("SPLUNK_MCP_URL")

async def test():
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type":  "application/json",
        "Accept":        "application/json, text/event-stream"
    }

    async with httpx.AsyncClient(verify=False, timeout=60.0) as client:

        # Step 1 — Initialize
        await client.post(URL, headers=headers, json={
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "SentinelPilot", "version": "1.0.0"}
            }
        })

        # Step 2 — Notification
        await client.post(URL, headers=headers, json={
            "jsonrpc": "2.0",
            "method":  "notifications/initialized",
            "params":  {}
        })

        # Step 3 — Call saia_generate_spl
        print("Testing saia_generate_spl...")
        r = await client.post(URL, headers=headers, json={
            "jsonrpc": "2.0", "id": 2,
            "method":  "tools/call",
            "params":  {
                "name": "saia_generate_spl",
                "arguments": {
                    "prompt": "Find failed login attempts in the security index in the last 24 hours"
                }
            }
        })
        print("Status:", r.status_code)
        print("Response:", r.text[:500])

asyncio.run(test())