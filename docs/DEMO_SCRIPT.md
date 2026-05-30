# SENTINELPILOT — DEMO VIDEO SCRIPT
# Duration: ~90 seconds
# Optimized for ElevenLabs TTS
# Record screen with OBS while this plays as voiceover

# ─────────────────────────────────────────────
# SCREEN ACTION GUIDE (what to show on screen)
# ─────────────────────────────────────────────
# 0:00–0:15 → Show dashboard.html homepage (empty state)
# 0:15–0:30 → Show Splunk Enterprise with security index data
# 0:30–0:45 → Click Investigate button — show radar sweep animation
# 0:45–1:10 → Show incident report appearing — scroll through it slowly
# 1:10–1:30 → Show GitHub repo — scroll through README
# ─────────────────────────────────────────────


# ══════════════════════════════════════════════
# SCRIPT — PASTE THIS INTO ELEVENLABS
# ══════════════════════════════════════════════

Security teams today are overwhelmed.
Analysts spend hours writing queries, correlating alerts, and investigating threats manually.
Meanwhile, real attacks go undetected.

SentinelPilot changes that.

SentinelPilot is an autonomous SOC agent that connects directly to Splunk
using the Splunk MCP Server.
It fetches security alerts automatically, reasons across multiple events using AI,
and generates a complete incident report — in seconds.
No manual queries. No human triage. Just answers.

Watch it work.

With one click, SentinelPilot connects to Splunk,
pulls the latest security events from the index,
and sends them to Groq AI for deep correlation analysis.

Within seconds, it identifies the attack pattern.
Ransomware activity. Lateral movement. Data exfiltration to Russia.
Six MITRE ATT&CK techniques — all detected automatically.

The incident report shows exactly what happened,
which systems are affected,
and the recommended response actions — ready for the analyst to act on immediately.

This is what agentic operations looks like.
Not a chatbot. Not a dashboard. An agent that investigates while you sleep.

SentinelPilot is built on Splunk MCP Server, Splunk Hosted Models,
and Groq AI — fully open source, deployed and ready today.

This is SentinelPilot. The future of autonomous security operations.


# ══════════════════════════════════════════════
# ELEVENLABS SETTINGS
# ══════════════════════════════════════════════
# Voice:      Adam or Antoni (male, clear, authoritative)
# Stability:  65%
# Clarity:    80%
# Style:      0%
# ══════════════════════════════════════════════


# ══════════════════════════════════════════════
# OBS RECORDING CHECKLIST
# ══════════════════════════════════════════════
# Before recording:
# [ ] uvicorn running on port 8001
# [ ] dashboard.html open in Chrome — full screen
# [ ] Splunk open in second tab
# [ ] GitHub repo open in third tab
# [ ] OBS set to 1920x1080, MP4
# [ ] Close all notification popups
# [ ] Set Windows to Do Not Disturb
# [ ] Hide taskbar (right-click taskbar → taskbar settings → auto-hide)
#
# Recording order:
# [ ] Start OBS recording FIRST
# [ ] Wait 3 seconds before doing anything
# [ ] Follow screen action guide above
# [ ] Go slowly — pause 2-3 seconds on each key moment
# [ ] Stop recording only after waiting 3 seconds at the end
#
# After recording:
# [ ] Generate ElevenLabs voiceover from script above
# [ ] Import both into CapCut
# [ ] Sync voiceover to screen actions
# [ ] Add auto-captions in CapCut
# [ ] Export at 1080p 30fps
# [ ] Upload to YouTube as Unlisted
# [ ] Copy YouTube link for Devpost submission
# ══════════════════════════════════════════════