# 🛡️ Aegis CTI - Cyber Threat Intelligence Portal

**Aegis CTI** is an AI-powered Cyber Threat Intelligence (CTI) triage platform and Defense Sensor Asset Registry designed for real-time tactical prioritization, automated NLP indicator extraction, and interactive threat analytics.

---

## ⚡ Features

- 🎯 **Automated Priority Scoring (0–100)**: Multi-factor explainable risk formula combining severity, asset criticality, threat category, and recency decay into SLA tiers (**P1 Immediate** to **P4 Routine**).
- 🧠 **NLP & IoC Extraction**: Automated parsing of Indicators of Compromise (CVEs, IPv4, hashes, domain names) from raw threat bulletins.
- 📊 **Interactive Analytics Dashboard**: Sleek dark-mode visualizations with dynamic **Year** and **Duration** time-series scrubbers.
- 🛰️ **Sensor Asset Registry**: Live registration and real-time alert feed for satellite, radar, UAV, and ground intelligence sensors.
- 🔒 **User Authentication & Role Management**: Multi-user access control for Analysts and Commanders.
- ⚡ **Offline & Lightweight**: Built on Python, Flask, SQLite, Chart.js, and Streamlit — runs entirely offline without external API dependencies.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install flask flask-cors streamlit pandas plotly
```

### 2. Launch Servers
Double-click `start_servers.bat` or run:
```bash
python server.py
```
Then access the portal at **`http://localhost:5001`**.

---

## 📁 Repository Structure

```
├── index.html              # Main Aegis CTI Portal UI
├── server.py               # Flask REST API Server
├── start_servers.bat       # One-click launcher for Flask & Streamlit
├── cti_database.db         # Persistent SQLite database
└── streamlit/
    ├── app.py              # Aegis CTI Analytics Dashboard
    ├── db_manager.py       # SQLite CRUD Operations & Schema
    ├── nlp_processing.py   # Keyword & IoC Extraction Pipeline
    └── pipeline.py         # Priority Scoring & Risk Engine
```
