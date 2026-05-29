"""
SentinelPilot — Sample Security Data Loader
Injects realistic security events into Splunk for demo purposes
"""

import httpx
import json
import ssl
import os
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv

load_dotenv()

SPLUNK_HOST  = os.getenv("SPLUNK_HOST", "localhost")
SPLUNK_PORT  = os.getenv("SPLUNK_PORT", "8089")
SPLUNK_TOKEN = os.getenv("SPLUNK_REST_TOKEN", "")

# Splunk HEC (HTTP Event Collector) or REST API URL
SPLUNK_REST  = f"https://{SPLUNK_HOST}:{SPLUNK_PORT}"

# ── Sample Security Events ─────────────────────────────────────────────────────
SAMPLE_EVENTS = [
    # Brute Force Attack
    {
        "sourcetype": "WinEventLog:Security",
        "index":      "security",
        "source":     "WinEventLog",
        "host":       "DESKTOP-MIM6KVQ",
        "event": {
            "EventCode":    4625,
            "EventType":    "AUDIT_FAILURE",
            "ComputerName": "DESKTOP-MIM6KVQ",
            "src_ip":       "192.168.1.105",
            "user":         "Administrator",
            "action":       "failure",
            "signature":    "An account failed to log on",
            "severity":     "high",
            "count":        47,
            "message":      "Multiple failed login attempts detected from 192.168.1.105 targeting Administrator account"
        }
    },
    # Suspicious PowerShell
    {
        "sourcetype": "WinEventLog:Security",
        "index":      "security",
        "source":     "WinEventLog",
        "host":       "DESKTOP-MIM6KVQ",
        "event": {
            "EventCode":    4688,
            "EventType":    "PROCESS_CREATION",
            "ComputerName": "DESKTOP-MIM6KVQ",
            "src_ip":       "192.168.1.105",
            "user":         "emfon",
            "process":      "powershell.exe",
            "command_line": "powershell.exe -nop -w hidden -enc JABjAGwAaQBlAG4AdA==",
            "severity":     "critical",
            "signature":    "Suspicious PowerShell execution with encoded command",
            "message":      "PowerShell launched with encoded command — possible malware execution"
        }
    },
    # Port Scan
    {
        "sourcetype": "stream:tcp",
        "index":      "security",
        "source":     "stream",
        "host":       "DESKTOP-MIM6KVQ",
        "event": {
            "src_ip":    "10.0.0.45",
            "dest_ip":   "192.168.1.1",
            "dest_port": "22,23,80,443,3389,8080,8443",
            "severity":  "high",
            "signature": "Port scan detected",
            "action":    "blocked",
            "count":     312,
            "message":   "Sequential port scan from 10.0.0.45 targeting 312 ports in 60 seconds"
        }
    },
    # Ransomware File Activity
    {
        "sourcetype": "WinEventLog:Security",
        "index":      "security",
        "source":     "WinEventLog",
        "host":       "DESKTOP-MIM6KVQ",
        "event": {
            "EventCode":    4663,
            "EventType":    "FILE_ACCESS",
            "ComputerName": "DESKTOP-MIM6KVQ",
            "user":         "emfon",
            "object_name":  "C:\\Users\\emfon\\Documents\\*.docx.encrypted",
            "severity":     "critical",
            "signature":    "Mass file encryption detected",
            "file_count":   847,
            "message":      "847 files renamed with .encrypted extension in 3 minutes — possible ransomware"
        }
    },
    # Privilege Escalation
    {
        "sourcetype": "WinEventLog:Security",
        "index":      "security",
        "source":     "WinEventLog",
        "host":       "DESKTOP-MIM6KVQ",
        "event": {
            "EventCode":    4672,
            "EventType":    "PRIVILEGE_USE",
            "ComputerName": "DESKTOP-MIM6KVQ",
            "src_ip":       "192.168.1.105",
            "user":         "emfon",
            "privileges":   "SeDebugPrivilege, SeImpersonatePrivilege",
            "severity":     "high",
            "signature":    "Sensitive privilege assigned to new logon",
            "message":      "User emfon granted SeDebugPrivilege — possible privilege escalation attempt"
        }
    },
    # Lateral Movement
    {
        "sourcetype": "WinEventLog:Security",
        "index":      "security",
        "source":     "WinEventLog",
        "host":       "DESKTOP-MIM6KVQ",
        "event": {
            "EventCode":    4624,
            "EventType":    "LOGON_SUCCESS",
            "ComputerName": "DESKTOP-MIM6KVQ",
            "src_ip":       "192.168.1.105",
            "dest_host":    "SERVER-DB-01",
            "user":         "svc_backup",
            "logon_type":   3,
            "severity":     "high",
            "signature":    "Unusual lateral movement detected",
            "message":      "Service account svc_backup logged into DB server from workstation — unusual pattern"
        }
    },
    # Data Exfiltration
    {
        "sourcetype": "stream:http",
        "index":      "security",
        "source":     "stream",
        "host":       "DESKTOP-MIM6KVQ",
        "event": {
            "src_ip":       "192.168.1.105",
            "dest_ip":      "185.220.101.47",
            "dest_port":    443,
            "bytes_out":    524288000,
            "severity":     "critical",
            "signature":    "Large data transfer to external IP",
            "dest_country": "RU",
            "message":      "500MB transferred to external IP 185.220.101.47 (Russia) over HTTPS"
        }
    },
    # DNS Tunneling
    {
        "sourcetype": "stream:dns",
        "index":      "security",
        "source":     "stream",
        "host":       "DESKTOP-MIM6KVQ",
        "event": {
            "src_ip":    "192.168.1.105",
            "query":     "aGVsbG8ud29ybGQ.evil-c2-server.com",
            "query_type": "TXT",
            "severity":  "high",
            "signature": "Possible DNS tunneling detected",
            "count":     1247,
            "message":   "1247 DNS TXT queries to suspicious domain — possible C2 communication via DNS tunneling"
        }
    },
    # Failed Admin Login
    {
        "sourcetype": "linux_secure",
        "index":      "security",
        "source":     "/var/log/secure",
        "host":       "SERVER-DB-01",
        "event": {
            "src_ip":    "10.0.0.45",
            "user":      "root",
            "action":    "failure",
            "severity":  "high",
            "signature": "Failed SSH root login attempt",
            "count":     89,
            "message":   "89 failed SSH login attempts for root from 10.0.0.45 in 5 minutes"
        }
    },
    # Malware Detection
    {
        "sourcetype": "symantec:ep:security:syslog",
        "index":      "security",
        "source":     "symantec",
        "host":       "DESKTOP-MIM6KVQ",
        "event": {
            "ComputerName": "DESKTOP-MIM6KVQ",
            "user":         "emfon",
            "file_path":    "C:\\Users\\emfon\\Downloads\\invoice_2026.exe",
            "virus_name":   "Trojan.GenericKD.71234567",
            "action":       "Quarantined",
            "severity":     "critical",
            "signature":    "Malware detected and quarantined",
            "message":      "Trojan detected in Downloads folder — file quarantined by antivirus"
        }
    }
]


def create_security_index():
    """Create the security index in Splunk if it doesn't exist"""
    headers = {
        "Authorization": f"Bearer {SPLUNK_TOKEN}",
        "Content-Type":  "application/x-www-form-urlencoded"
    }
    data = "name=security&datatype=event"

    try:
        r = httpx.post(
            f"{SPLUNK_REST}/services/data/indexes",
            content=data,
            headers=headers,
            verify=False,
            timeout=15.0
        )
        if r.status_code in [201, 409]:  # 409 = already exists
            print(f"✅ Security index ready (status: {r.status_code})")
            return True
        else:
            print(f"⚠️  Index creation: {r.status_code} — {r.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Index creation error: {e}")
        return False


def inject_event(event_data: dict, index: str = "security") -> bool:
    """Inject a single event into Splunk via REST API"""
    headers = {
        "Authorization": f"Bearer {SPLUNK_TOKEN}",
        "Content-Type":  "application/json"
    }

    # Format event as JSON string
    event_str = json.dumps(event_data["event"])

    # Use Splunk receivers/simple endpoint
    params = {
        "index":      index,
        "sourcetype": event_data.get("sourcetype", "json"),
        "source":     event_data.get("source", "sentinelpilot_demo"),
        "host":       event_data.get("host", "DESKTOP-MIM6KVQ")
    }

    try:
        r = httpx.post(
            f"{SPLUNK_REST}/services/receivers/simple",
            content=event_str,
            headers=headers,
            params=params,
            verify=False,
            timeout=15.0
        )
        return r.status_code in [200, 204]
    except Exception as e:
        print(f"  Error: {e}")
        return False


def main():
    print("=" * 60)
    print("SentinelPilot — Sample Security Data Loader")
    print("=" * 60)
    print(f"Target: {SPLUNK_REST}")
    print(f"Token:  {SPLUNK_TOKEN[:20]}..." if SPLUNK_TOKEN else "NO TOKEN!")
    print()

    # Step 1 — Create security index
    print("Step 1 — Creating security index...")
    create_security_index()
    print()

    # Step 2 — Inject events
    print(f"Step 2 — Injecting {len(SAMPLE_EVENTS)} security events...")
    success = 0
    failed  = 0

    for i, event in enumerate(SAMPLE_EVENTS):
        sig = event["event"].get("signature", f"Event {i+1}")
        ok  = inject_event(event)
        if ok:
            success += 1
            print(f"  ✅ [{i+1}/{len(SAMPLE_EVENTS)}] {sig}")
        else:
            failed += 1
            print(f"  ❌ [{i+1}/{len(SAMPLE_EVENTS)}] {sig} — FAILED")

    print()
    print("=" * 60)
    print(f"Done! {success} events loaded, {failed} failed")
    print()

    if success > 0:
        print("✅ Now test SentinelPilot with:")
        print('   index=security in your /investigate request')
        print()
        print("Verify in Splunk search:")
        print("   index=security | stats count by signature")
    else:
        print("❌ No events loaded — check your SPLUNK_TOKEN in .env")

if __name__ == "__main__":
    main()