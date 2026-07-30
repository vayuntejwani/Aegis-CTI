import re
from typing import Dict, List


IOC_PATTERNS = {
    "ipv4": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "domain": re.compile(r"\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"),
    "cve": re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.IGNORECASE),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    # Very simple hash regexes (demo). build_report.js expects images only; this is for UI.
    "hash_md5": re.compile(r"\b[a-fA-F0-9]{32}\b"),
    "hash_sha1": re.compile(r"\b[a-fA-F0-9]{40}\b"),
    "hash_sha256": re.compile(r"\b[a-fA-F0-9]{64}\b"),
    "port": re.compile(r"\b(?:(?:port)\s*)?(\d{2,5})\b", re.IGNORECASE),
}


def extract_iocs(text: str) -> Dict[str, List[str]]:
    text = text or ""

    out: Dict[str, List[str]] = {}
    for key, pat in IOC_PATTERNS.items():
        vals = pat.findall(text)
        # port regex captures groups sometimes
        if key == "port":
            vals = [v for v in vals if v]
        # de-dup while preserving order
        seen = set()
        uniq = []
        for v in vals:
            v = str(v)
            if v not in seen:
                seen.add(v)
                uniq.append(v)
        if uniq:
            out[key] = uniq[:20]

    return out


def simple_keywords(text: str, top_k: int = 20) -> List[str]:
    """Enhanced cybersecurity and Indian military keyword extractor."""
    text = (text or "").lower()
    # Find all words (3+ chars)
    tokens = re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", text)
    
    # Generic stopwords to exclude
    stop = {
        "the","and","for","with","from","into","that","this","was","were","are","is","in","on","of","to","as","by","an","at","it","be","or","we","our","their",
        "observed", "detected", "multiple", "found", "include", "appears", "using", "reported", "activity", "systems", "advisory", "security", "threat", "alert",
        "system", "compromise", "compromised", "accessed", "access", "unauthorized", "unauth", "indicators", "target", "targeting", "targeted", "technique",
        "present", "presently", "technique", "techniques", "include", "includes", "including", "address", "addresses", "addressing", "email", "emails",
        "file", "files", "details", "detailed", "view", "open", "close", "show", "shows", "shown", "click", "button", "open", "opened", "opening",
        "host", "hosts", "network", "networks", "server", "servers", "client", "clients", "connection", "connections", "traffic", "spike", "spikes",
        "contains", "vulnerability", "allow", "unauthenticated", "remote", "code", "execution", "mitigations", "accordance", "instructions", "compliance",
        "prioritizing", "guidance", "vendor", "update", "patch", "product", "software", "cisa", "bod", "requirements", "triage", "forensics", "stakeholders",
        "responsible", "evaluating", "asset", "internet", "exposure", "adherence", "patching", "guidelines", "discontinue", "cloud", "services", "unavailable",
        "applicable", "ensuring", "mitigation", "advised", "campaign", "operated", "primary", "located", "sector", "immediate", "historical", "intel",
        "cve", "which", "could", "has", "been", "have", "not", "but", "can", "may", "who", "what", "where", "when", "why", "how", "all", "any", "both", "each",
        "few", "more", "most", "other", "some", "such", "nor", "too", "very", "will", "just", "don", "should", "now", "via", "its", "use", "has",
        "an", "attacker", "attacks", "impact", "successful", "exploitation", "exploited", "exploit", "exploiting", "allows", "allowing", "allowed", "cause",
        "causing", "caused", "issue", "issues", "problem", "problems", "error", "errors", "bug", "bugs", "flaw", "flaws", "defect", "defects", "fault",
        "faults", "failure", "failures", "fails", "failing", "failed", "crash", "crashes", "crashing", "crashed", "denial", "service", "dos", "ddos",
        "privilege", "escalation", "escalate", "escalating", "escalated", "privileges", "rights", "permissions", "bypass", "bypasses", "bypassing", "bypassed",
        "authentication", "auth", "authenticate", "authenticating", "authenticated", "authorization", "authorize", "authorizing", "authorized", "login",
        "logins", "logon", "logons", "password", "passwords", "credential", "credentials", "token", "tokens", "key", "keys", "certificate", "certificates"
    }
    
    # Vocabulary to boost
    boosted_vocab = {
        # Military terms
        "drdo", "dcya", "iaf", "army", "navy", "mod", "lac", "loc", "visakhapatnam", "udhampur", "jammu", 
        "leh", "srinagar", "border", "radar", "satellite", "telemetry", "guidance", "missile", "hq", 
        "eastern", "western", "northern", "southern", "central", "tri-services", "command", "tactical", "operational",
        # Cyber / Threat terms
        "apt35", "apt41", "chasing", "ransomware", "malware", "espionage", "sabotage", "scada", 
        "intrusion", "exfiltration", "exfiltrate", "leak", "cve", "zero-day", "payload", "backdoor", "trojan",
        "rootkit", "firewall", "credential", "brute-force", "botnet", "ddos", "spoofing", "wiper", "pegasus", "lateral",
        # HIGH-IMPACT TERRORISM / ATTACK / SABOTAGE terms (added for improved severity prediction)
        "terrorism", "terror", "attacker", "attacking", "targeted",
        "explosion", "explosive", "bomb", "blast", "ied", "wmd", "weapon",
        "nuclear", "biological", "chemical", "radiological",
        "insurgent", "insurgency", "militant", "infiltration",
        "cross-border", "surgical", "strategic", "airstrike",
        "nation-state", "state-sponsored", "hostile", "enemy",
        "warhead", "artillery", "convoy", "ambush", "perimeter",
        "mass casualty", "active shooter", "armed assault",
        "sabotage", "saboteur", "critical infrastructure",
        "imminent", "cascading", "compromise", "breach", "breached",
    }
    
    super_boosted = {"terrorist", "drone", "attack", "cyber", "phishing"}
    
    freq = {}
    for t in tokens:
        if t in stop:
            continue
        # base score is frequency
        freq[t] = freq.get(t, 0) + 1
        
    # Apply boosts to military/security terms
    for t in freq:
        if t in super_boosted:
            freq[t] *= 100000  # absolute priority
        elif t in boosted_vocab:
            freq[t] *= 15  # major boost to bubble them to the top!
            
    ranked = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
    return [w for w, _ in ranked[:top_k]]


def extractive_summary(text: str, max_sentences: int = 2) -> str:
    """Very small TextRank-like demo: pick first N sentences with length."""
    text = (text or "").strip()
    if not text:
        return ""
    sents = re.split(r"(?<=[.!?])\s+", text)
    sents = [s.strip() for s in sents if s.strip()]
    sents = sorted(sents, key=lambda s: (len(s),), reverse=True)
    picked = sorted(sents[:max_sentences], key=lambda s: sents.index(s))
    return " ".join(picked)

