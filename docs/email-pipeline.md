# Email Pipeline

← [Back to README](../README.md)



## Overview

This page documents the full email ingestion and event extraction pipeline.

## Email Pipeline Flow

```
1. IMAP Connection       → Connect to university mail server
2. Email Download        → Fetch latest emails (configurable limit)
3. HTML Parsing          → Convert HTML emails to plain text
4. Filtering             → Keep only "Rundmail" type emails
5. LLM Extraction        → Gemini extracts structured event data
6. Deduplication         → LLM compares with existing events
7. Database Insert       → Store new events in SQLite
8. WebSocket Broadcast   → Frontend receives updated event list
```
