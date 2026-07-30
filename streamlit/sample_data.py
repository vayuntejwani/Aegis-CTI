from datetime import datetime, timedelta

def load_sample_reports():
    """Indian Military CTI corpus. Realistically adapted for defence sectors."""
    now = datetime.now()
    base = [
        {
            "report_id": "CTI-00001",
            "date": now - timedelta(days=2),
            "source": "DCyA-Alert",
            "title": "Ransomware compromise at Eastern Naval Command Visakhapatnam",
            "description": "LockBit-like ransomware activity detected on tactical base servers of Eastern Naval Command. Encryption logs and ransom notes observed on INS Visakhapatnam base terminals. Indicators include external C2 host 203.0.113.10 and MD5 hash 5d41402abc4b2a76b9719d911017c592. Crucial operations base communications affected.",
            "category": "Ransomware",
            "severity": "High",
            "affected_system": "INS Visakhapatnam Base Server",
            "asset_criticality": "High",
            "region": "Eastern Command",
        },
        {
            "report_id": "CTI-00002",
            "date": now - timedelta(days=9),
            "source": "MoD-OSINT",
            "title": "Phishing campaign targeting MoD Procurement officers",
            "description": "State-sponsored phishing emails targeting Ministry of Defence (MoD) weapon procurement offices. The malicious emails carry a macro-enabled document disguised as an ammunition tender. Domain name evil-procurement.example identified. URLs include http://evil-procurement.example/tenders/login . Payload MD5: e99a18c428cb38d5f260853678922e03.",
            "category": "Phishing",
            "severity": "Medium",
            "affected_system": "Defence Email Gateway",
            "asset_criticality": "Medium",
            "region": "Central Command",
        },
        {
            "report_id": "CTI-00003",
            "date": now - timedelta(days=15),
            "source": "DRDO-SOC",
            "title": "Lateral movement on DRDO satellite guidance telemetry database",
            "description": "APT41/Chasing Panda observed attempting lateral movement on DRDO missile telemetry database. Multiple failed logons followed by credential compromise from IP 198.51.100.22. CVE-2024-1234 active exploitation detected on database server. Attack targeting strategic satellite telemetry parameters.",
            "category": "Network Intrusion",
            "severity": "Critical",
            "affected_system": "Satellite Guidance Telemetry Database",
            "asset_criticality": "Critical",
            "region": "Strategic Forces Command",
        },
        {
            "report_id": "CTI-00004",
            "date": now - timedelta(days=23),
            "source": "DCyA-CERT",
            "title": "Zero-day exploit attempt on SCADA grids in Northern Command (Leh)",
            "description": "Critical indicators of zero-day exploit targeting SCADA critical power grid nodes at Leh base camp. Anomalous HTTP requests targeting server /cgi-bin folder. Outbound telemetry data leak attempt to domain telemetry-mod.example. Threat suggests potential infrastructure sabotage near the LAC.",
            "category": "Zero-Day Exploit",
            "severity": "Critical",
            "affected_system": "SCADA Grid Controller",
            "asset_criticality": "Critical",
            "region": "Northern Command",
        },
        {
            "report_id": "CTI-00005",
            "date": now - timedelta(days=6),
            "source": "IAF-AirDefence-SOC",
            "title": "DDoS assault on border radar telemetry node",
            "description": "Massive traffic flood DDoS targeting border radar data telemetry node in Western Command. Radar packet processing delays observed. Source IPs belong to a known botnet pool including 203.0.113.55 and 203.0.113.56. Related advisory highlights CVE-2023-9999 vulnerabilities in radar interfaces.",
            "category": "DDoS",
            "severity": "High",
            "affected_system": "Western Border Radar Node",
            "asset_criticality": "High",
            "region": "Western Command",
        },
    ]

    for r in base:
        r["date"] = r["date"] if isinstance(r["date"], datetime) else datetime.fromisoformat(r["date"])

    return base
