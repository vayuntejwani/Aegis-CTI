from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

from model_stub import CATEGORY_RISK, SEVERITY_WEIGHTS, predict_stub_category_and_severity, predict_stub_severity
from nlp_processing import extract_iocs, extractive_summary, simple_keywords


def asset_criticality_value(v: str) -> float:
    mapping = {
        "Low": 0.2,
        "Medium": 0.45,
        "High": 0.7,
        "Critical": 0.95,
    }
    return mapping.get(v, 0.45)


def recency_value(days_since: int, half_life_days: int = 7) -> float:
    # exponential decay into [0,1]
    import math

    return math.exp(-math.log(2) * (max(0, days_since) / half_life_days))


def priority_tier(score: float) -> str:
    if score >= 80:
        return "P1 - Immediate"
    if score >= 60:
        return "P2 - Urgent"
    if score >= 35:
        return "P3 - Scheduled"
    return "P4 - Routine"


def score_priority(
    predicted_severity: str,
    predicted_category: str,
    severity_confidence: float,
    category_risk: float | None,
    asset_criticality: str,
    days_since: int,
    *,
    w1: float,
    w2: float,
    w3: float,
    w4: float,
) -> float:
    severity_base = SEVERITY_WEIGHTS.get(predicted_severity, 0.45)
    severity_component = severity_base * float(severity_confidence)

    if category_risk is None:
        category_risk = CATEGORY_RISK.get(predicted_category, 0.6)

    ac = asset_criticality_value(asset_criticality)
    rec = recency_value(days_since)

    # ensure all components are within [0,1]
    total = w1 * severity_component + w2 * category_risk + w3 * ac + w4 * rec
    score = 100.0 * total
    if score < 0:
        score = 0
    if score > 100:
        score = 100
    return score


def analyze_report(title: str, description: str) -> Dict[str, Any]:
    text = f"{title or ''}. {description or ''}".strip()

    category, cat_conf = predict_stub_category_and_severity(text)
    severity, sev_conf = predict_stub_severity(text)

    # Risk is explainable lookup
    risk = CATEGORY_RISK.get(category, 0.6)

    keywords = simple_keywords(text, top_k=30)
    iocs = extract_iocs(text)
    summary = extractive_summary(text, max_sentences=2)

    return {
        "text_len": len(text),
        "category": category,
        "category_confidence": cat_conf,
        "severity": severity,
        "severity_confidence": sev_conf,
        "category_risk": risk,
        "keywords": keywords,
        "iocs": iocs,
        "summary": summary,
    }

