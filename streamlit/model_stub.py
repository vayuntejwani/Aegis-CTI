import re
import math


CATEGORY_RISK = {
    "Zero-Day Exploit": 0.95,
    "Ransomware": 0.9,
    "Terrorism / Insurgency": 0.95,
    "Nation-State Attack": 0.95,
    "Sabotage": 0.85,
    "Network Intrusion": 0.85,
    "Insider Threat": 0.8,
    "Data Breach": 0.75,
    "Malware": 0.7,
    "DDoS": 0.65,
    "Phishing": 0.55,
}

SEVERITY_WEIGHTS = {
    "Low": 0.2,
    "Medium": 0.45,
    "High": 0.7,
    "Critical": 0.95,
}

# ---------------------------------------------------------------------------
# Scoring-based severity: each keyword group has a weight; all matches are
# accumulated into a single score that maps to {Low, Medium, High, Critical}.
# ---------------------------------------------------------------------------

# Each group: (weight_multiplier, set of keywords/phrases)
_SEVERITY_GROUPS = {
    "Critical": (
        3.0,
        {
            "terrorism", "terrorist", "terror", "bomb", "blast", "explosion",
            "explosive", "ied", "wmd", "weapon of mass destruction",
            "nuclear", "biological", "chemical", "radiological",
            "sabotage", "infiltration", "insurgent", "insurgency",
            "cross-border", "surgical strike", "tactical strike",
            "active shooter", "mass casualty", "armed assault",
            "nation-state attack", "state-sponsored", "hostile nation",
            "warhead", "missile strike", "artillery", "airstrike",
            "zero-day", "zero day", "cve", "cascading", "critical",
            "payload delivery", "active exploitation", "weaponized",
            "imminent threat", "imminent attack",
        },
    ),
    "High": (
        2.0,
        {
            "attack", "attacker", "attacking", "targeted",
            "ransomware", "ransom", "encrypt", "lockbit",
            "unauthorized", "domain controller", "intrusion",
            "lateral movement", "credential compromise", "backdoor",
            "espionage", "exfiltration", "exfiltrate", "data breach",
            "trojan", "botnet", "advanced persistent", "apt",
            "drone", "missile", "radar", "telemetry",
            "supply chain", "compromise", "breach", "breached",
            "perimeter", "hostile", "enemy", "militant",
            "convoy", "ambush", "border incursion",
            "command and control", "c2", "c&c",
            "exploit", "exploitation", "payload",
            "scada", "guidance system",
        },
    ),
    "Medium": (
        1.0,
        {
            "phishing", "malware", "ddos", "flood", "traffic spike",
            "suspicious", "anomalous", "observed", "detected",
            "scanning", "reconnaissance", "vulnerability", "spam",
            "spoofing", "credential", "macro", "email campaign",
            "macro enabled", "unusual", "probing", "enumeration",
            "port scan", "brute force", "bruteforce",
            "sensor", "surveillance", "recon",
            "fingerprinting", "osint",
        },
    ),
}


def _compute_severity_score(text: str) -> float:
    """Score in [0, 1] — higher means more severe.

    Each matched keyword contributes its group's weight to a cumulative score.
    The score is squashed via tanh so outputs stay bounded in [0, 0.95].
    """
    t = (text or "").lower()
    if not t:
        return 0.0

    raw_score = 0.0

    for level, (weight, keywords) in _SEVERITY_GROUPS.items():
        # Every distinct match adds weight/10 to the raw score.
        # This way matching 2 critical terms (~0.6) already pushes toward High.
        for kw in keywords:
            if kw in t:
                raw_score += weight / 10.0

    # Give a small length bonus for longer, more detailed reports
    length_bonus = min(len(t) / 2000, 0.10)

    # Squash via tanh so score converges but doesn't exceed 0.95
    score = math.tanh(raw_score) * 0.95
    score += length_bonus
    return min(score, 1.0)


import os
import joblib

_SEVERITY_MODEL = None
_MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models', 'severity_model.joblib')

if os.path.exists(_MODEL_PATH):
    try:
        _SEVERITY_MODEL = joblib.load(_MODEL_PATH)
    except Exception as e:
        pass


def predict_stub_severity(text: str):
    """Scoring-based severity prediction with proportional confidence."""
    global _SEVERITY_MODEL
    
    if _SEVERITY_MODEL is not None and text:
        try:
            pred = _SEVERITY_MODEL.predict([text])[0]
            probs = _SEVERITY_MODEL.predict_proba([text])[0]
            confidence = max(probs)
            return pred, min(confidence + 0.1, 0.99)
        except Exception:
            pass
            
    score = _compute_severity_score(text)

    if score >= 0.70:
        return "Critical", min(0.85 + (score - 0.70) * 0.5, 0.97)
    elif score >= 0.45:
        return "High", min(0.70 + (score - 0.45) * 0.8, 0.92)
    elif score >= 0.20:
        return "Medium", min(0.55 + (score - 0.20) * 0.6, 0.85)
    else:
        return "Low", max(0.35 + score * 0.6, 0.45)


# ---------------------------------------------------------------------------
# Category prediction — also scoring-based to handle overlapping terms
# ---------------------------------------------------------------------------

# Each category has a set of cue words/phrases and a base confidence
_CATEGORY_CUES = {
    "Terrorism / Insurgency": (0.90, {
        "terrorism", "terrorist", "terror", "bomb", "blast", "explosion",
        "explosive", "ied", "wmd", "weapon of mass destruction", "insurgent",
        "insurgency", "militant", "infiltration", "cross-border",
        "surgical strike", "mass casualty", "active shooter",
        "radical", "extremist", "jihad", "jihadist",
    }),
    "Nation-State Attack": (0.88, {
        "nation-state", "state-sponsored", "hostile nation", "enemy state",
        "military grade", "weaponized", "warhead", "missile strike",
        "airstrike", "artillery", "tactical nuke", "sabotage",
        "strategic asset", "advanced persistent", "apt41", "apt35",
        "chasing panda", "state actor", "foreign adversary",
        "satellite telemetry", "guidance system", "drone strike",
    }),
    "Sabotage": (0.85, {
        "sabotage", "saboteur", "scada", "critical infrastructure",
        "grid controller", "power grid", "telemetry sabotage",
        "infrastructure attack", "damage", "destroy", "disable",
        "critical system", "physical damage", "industrial control",
    }),
    "Zero-Day Exploit": (0.80, {
        "cve", "zero-day", "zero day", "0-day", "exploit",
        "vulnerability disclosure", "unpatched", "unknown vulnerability",
    }),
    "Ransomware": (0.82, {
        "ransomware", "ransom", "encrypt", "lockbit", "decryptor",
        "ransom note", "bitcoin", "cryptocurrency",
    }),
    "Network Intrusion": (0.76, {
        "domain controller", "unauthorized", "credential",
        "lateral movement", "intrusion", "backdoor", "c2",
        "command and control", "compromised host", "breach",
        "perimeter breach", "persistence",
    }),
    "Data Breach": (0.72, {
        "data breach", "exfiltrate", "exfiltration", "leak",
        "data leak", "database dump", "pii", "personally identifiable",
        "stolen data", "credentials dump",
    }),
    "DDoS": (0.78, {
        "ddos", "flood", "traffic spike", "amplification",
        "botnet", "syn flood", "udp flood", "volumetric",
    }),
    "Phishing": (0.66, {
        "phishing", "spear phishing", "macro", "email campaign",
        "malicious email", "phish", "spoofed", "social engineering",
        "credential harvesting", "login page",
    }),
    "Insider Threat": (0.70, {
        "insider", "employee", "privilege misuse", "internal threat",
        "disgruntled", "data theft", "internal access",
    }),
    "Malware": (0.70, {
        "malware", "trojan", "botnet", "worm", "dropper", "payload",
        "pegasus", "rootkit", "wiper", "banking trojan", "backdoor",
        "keylogger", "infostealer",
    }),
}


def predict_stub_category_and_severity(text: str):
    """Scoring-based category prediction. All categories scored; highest wins."""
    t = (text or "").lower()
    if not t:
        return "Phishing", 0.55

    best_cat = "Phishing"
    best_score = 0.0
    best_conf = 0.55

    for category, (base_conf, cues) in _CATEGORY_CUES.items():
        matched = sum(1 for cue in cues if cue in t)
        if matched == 0:
            continue
        # Score = proportion of cues matched * base confidence
        ratio = matched / max(len(cues) * 0.15, 1)  # saturates at ~15% cues matched
        score = ratio * base_conf
        # Bonus for exact phrase match
        if category.lower().replace(" / ", " ") in t:
            score *= 1.2

        if score > best_score:
            best_score = score
            best_cat = category
            best_conf = min(base_conf + ratio * 0.15, 0.96)

    return best_cat, best_conf

