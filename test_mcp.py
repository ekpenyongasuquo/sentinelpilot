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

        # Initialize
        await client.post(URL, headers=headers, json={
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "SentinelPilot", "version": "1.0.0"}
            }
        })

        # Notification
        await client.post(URL, headers=headers, json={
            "jsonrpc": "2.0",
            "method":  "notifications/initialized",
            "params":  {}
        })

        # Call splunk_run_query
        r = await client.post(URL, headers=headers, json={
            "jsonrpc": "2.0", "id": 2,
            "method":  "tools/call",
            "params":  {
                "name": "splunk_run_query",
                "arguments": {
                    "query":         "index=main | head 5",
                    "earliest_time": "-24h",
                    "latest_time":   "now"
                }
            }
        })
        print("Status:", r.status_code)
        print("Response:", r.text[:1000])

asyncio.run(test())