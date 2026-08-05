import json
import os
from datetime import datetime, timedelta

import streamlit as st

from pipeline import analyze_report, score_priority, priority_tier
from db_manager import get_all_reports

st.set_page_config(
    page_title="Aegis CTI Dashboard",
    page_icon="🛡️",
    layout="wide",
)
st.title("Aegis CTI Dashboard")

st.markdown("""
<style>
  /* Hide the sidebar top logo/collapse button decoration */
  div[data-testid="stSidebarHeader"] {
    display: none !important;
  }
  div[data-testid="stSidebarCollapseButton"] {
    display: none !important;
  }
  /* Remove top padding from sidebar content */
  section[data-testid="stSidebar"] > div:first-child {
    padding-top: 0.5rem !important;
    margin-top: 0 !important;
  }
  section[data-testid="stSidebar"] .stSidebarUserContent {
    padding-top: 0.5rem !important;
  }
  div[data-testid="stSidebarContent"] {
    padding-top: 0 !important;
  }
  .block-container {
    padding-top: 1.5rem !important;
  }
</style>
""", unsafe_allow_html=True)

def apply_custom_theme(fig):
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, title_font=dict(size=13), tickfont=dict(size=12, color="#94a3b8")),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title_font=dict(size=13), tickfont=dict(size=12, color="#94a3b8")),
        font=dict(family="Inter, sans-serif", color="#e2e8f0"),
        title=dict(font=dict(size=18, family="Outfit, sans-serif", color="#f8fafc")),
        legend=dict(font=dict(size=12, color="#94a3b8"), bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig

# ------------------------------
# Sidebar filters
# ------------------------------
with st.sidebar:
    st.header("Filters")
    
    db_reports = get_all_reports()
    # Sort chronologically to get min and max dates
    db_reports_chron = sorted(db_reports, key=lambda x: x["date"])
    for r in db_reports_chron:
        if isinstance(r["date"], str):
            r["date"] = datetime.fromisoformat(r["date"])
            
    min_date = db_reports_chron[0]["date"].date() if db_reports_chron else datetime.now().date() - timedelta(days=30)
    max_date = db_reports_chron[-1]["date"].date() if db_reports_chron else datetime.now().date()

    years = ["All Years", "2026", "2025", "2024", "2023", "2022", "2021", "2020", "2019", "2018", "2017"]
    durations = ["All Time", "Last 30 Days", "Last 6 Months", "Last 1 Year", "Last 5 Years"]

    selected_year = st.selectbox("Filter by Year", years, index=0)
    selected_duration = st.selectbox("Quick Duration", durations, index=0)

    date_range = st.date_input(
        "Custom Date Range",
        value=(min_date, max_date),
    )

    categories = sorted({r["category"] for r in db_reports})
    severities = sorted({r["severity"] for r in db_reports})

    category_sel = st.multiselect("Category", categories, default=categories)
    severity_sel = st.multiselect("Severity", severities, default=severities)

    # Tunable weights for explainable priority scoring
    st.subheader("Priority scoring weights")
    w1 = st.slider("w1 (Severity confidence)", 0.0, 1.0, 0.40, 0.01)
    w2 = st.slider("w2 (Category risk)", 0.0, 1.0, 0.25, 0.01)
    w3 = st.slider("w3 (Asset criticality)", 0.0, 1.0, 0.20, 0.01)
    w4 = st.slider("w4 (Recency)", 0.0, 1.0, 0.15, 0.01)

    # Normalize weights to sum to 1.0 for interpretability
    w_sum = max(1e-9, (w1 + w2 + w3 + w4))
    w1, w2, w3, w4 = w1 / w_sum, w2 / w_sum, w3 / w_sum, w4 / w_sum

    

# ------------------------------
# Load and score corpus
# ------------------------------
corpus = get_all_reports()
for r in corpus:
    if isinstance(r["date"], str):
        r["date"] = datetime.fromisoformat(r["date"])

# Safe unpacking & boundary evaluation for year / duration / date_range
if selected_year != "All Years":
    y = int(selected_year)
    start_date = datetime(y, 1, 1, 0, 0, 0)
    end_date = datetime(y, 12, 31, 23, 59, 59)
elif selected_duration != "All Time":
    now = datetime.now()
    end_date = now
    if selected_duration == "Last 30 Days":
        start_date = now - timedelta(days=30)
    elif selected_duration == "Last 6 Months":
        start_date = now - timedelta(days=180)
    elif selected_duration == "Last 1 Year":
        start_date = now - timedelta(days=365)
    elif selected_duration == "Last 5 Years":
        start_date = now - timedelta(days=5 * 365)
else:
    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        sd, ed = date_range
    elif isinstance(date_range, (tuple, list)) and len(date_range) == 1:
        sd, ed = date_range[0], date_range[0]
    else:
        sd, ed = date_range, date_range
    start_date = datetime.combine(sd, datetime.min.time())
    end_date = datetime.combine(ed, datetime.max.time())

# Apply filters
filtered = [
    r
    for r in corpus
    if start_date <= r["date"] <= end_date
    and r["category"] in category_sel
    and r["severity"] in severity_sel
]

# Score priority for filtered corpus (stub models still produce deterministic-ish scores)
for r in filtered:
    pred = analyze_report(r["title"], r["description"])
    r["prediction"] = pred
    score = score_priority(
        predicted_severity=r["severity"],
        predicted_category=r["category"],
        severity_confidence=pred["severity_confidence"],
        category_risk=pred["category_risk"],
        asset_criticality=r["asset_criticality"],
        days_since=(datetime.now() - r["date"]).days,
        w1=w1,
        w2=w2,
        w3=w3,
        w4=w4,
    )
    r["priority_score"] = score
    r["priority_tier"] = priority_tier(score)

# ------------------------------
# Tabs
# ------------------------------

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Threat Overview", "Critical Alerts", "Trends", "Report Explorer", "Analyze New Report"]
)

# ------------------------------
# Tab 1: Overview
# ------------------------------
with tab1:
    import pandas as pd
    import plotly.express as px

    df = pd.DataFrame(filtered)

    if df.empty:
        st.info("No data matching the selected filters.")
    else:
        st.subheader("Distributions")
        c1, c2 = st.columns(2)

        with c1:
            fig1 = px.histogram(df, y="category", title="Threat Categories", text_auto=".0")
            fig1.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(apply_custom_theme(fig1), use_container_width=True)

        with c2:
            fig2 = px.histogram(df, x="severity", title="Severity Levels", text_auto=".0",
                                category_orders={"severity": ["Low", "Medium", "High", "Critical"]},
                                color="severity",
                                color_discrete_map={"Low":"#3b82f6", "Medium":"#eab308", "High":"#f97316", "Critical":"#ef4444"})
            st.plotly_chart(apply_custom_theme(fig2), use_container_width=True)

        st.subheader("Priority tiers")
        tier_counts = df["priority_tier"].value_counts().sort_index()
        st.bar_chart(tier_counts)

        st.subheader("Top keywords")
        # Collect keywords from predictions
        kw = {}
        for r in filtered:
            for k in r["prediction"]["keywords"][:8]:
                kw[k] = kw.get(k, 0) + 1
        top_kw = sorted(kw.items(), key=lambda x: x[1], reverse=True)[:10]
        if top_kw:
            st.table(pd.DataFrame(top_kw, columns=["keyword", "mentions"]))



# ------------------------------
# Tab 2: Critical Alerts
# ------------------------------
with tab2:
    import pandas as pd

    df = pd.DataFrame(filtered)
    if df.empty:
        st.info("No data matching the selected filters.")
    else:
        df_sorted = df.sort_values("priority_score", ascending=False)
        df_out = df_sorted[[
            "report_id",
            "date",
            "category",
            "severity",
            "asset_criticality",
            "priority_score",
            "priority_tier",
            "title",
        ]]

        st.subheader("Top prioritized alerts")
        st.dataframe(df_out.head(25), use_container_width=True)

# ------------------------------
# Tab 3: Trends
# ------------------------------
with tab3:
    import pandas as pd
    import plotly.express as px

    df = pd.DataFrame(filtered)
    if not df.empty:
        df["day"] = pd.to_datetime(df["date"]).dt.date
        
        # Volume over time
        fig3 = px.histogram(df, x="day", color="category", title="Incident Volume Over Time", nbins=80,
                            color_discrete_sequence=px.colors.qualitative.Pastel)
        fig3.update_traces(marker_line_width=0)
        fig3 = apply_custom_theme(fig3)
        fig3.update_layout(
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1m", step="month", stepmode="backward"),
                        dict(count=6, label="6m", step="month", stepmode="backward"),
                        dict(count=1, label="1y", step="year", stepmode="backward"),
                        dict(step="all")
                    ]),
                    bgcolor="#1e293b",
                    activecolor="#3b82f6",
                    font=dict(color="#f8fafc")
                ),
                rangeslider=dict(visible=True, bgcolor="#0f172a"),
                type="date"
            )
        )
        st.plotly_chart(fig3, use_container_width=True)

        # Region vs severity
        fig4 = px.histogram(df, x="region", color="severity", barmode="group", title="Regional Threat Distribution",
                            category_orders={"severity": ["Low", "Medium", "High", "Critical"]},
                            color_discrete_map={"Low":"#3b82f6", "Medium":"#eab308", "High":"#f97316", "Critical":"#ef4444"})
        fig4.update_traces(marker_line_width=0)
        st.plotly_chart(apply_custom_theme(fig4), use_container_width=True)
    else:
        st.info("No data for the selected filters.")

# ------------------------------
# Tab 4: Report Explorer
# ------------------------------
with tab4:
    import pandas as pd

    df = pd.DataFrame(filtered)
    if df.empty:
        st.info("No data for the selected filters.")
    else:
        ids = df["report_id"].tolist()
        selected = st.selectbox("Select a report", ids)
        row = df[df["report_id"] == selected].iloc[0].to_dict()

        pred = row.get("prediction") or analyze_report(row.get("title", ""), row.get("description", ""))

        st.subheader("Analyst View")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Priority Score", f"{row['priority_score']:.1f}")
            st.metric("Tier", row["priority_tier"])

        with c2:
            st.write("Predicted Category")
            st.write(pred["category"])
            st.write("Predicted Severity")
            st.write(pred["severity"])



# ------------------------------
# Tab 5: Analyze New Report
# ------------------------------
with tab5:
    st.subheader("Analyze a new report (offline demo)")

    title = st.text_input("Title")
    description = st.text_area("Description", height=180)
    asset_criticality = st.selectbox(
        "Asset criticality",
        ["Low", "Medium", "High", "Critical"],
        index=2,
    )

    if st.button("Run analysis"):
        if not (title.strip() or description.strip()):
            st.warning("Enter a title or description.")
        else:
            pred = analyze_report(title, description)
            score = score_priority(
                predicted_severity=pred["severity"],
                predicted_category=pred["category"],
                severity_confidence=pred["severity_confidence"],
                category_risk=pred["category_risk"],
                asset_criticality=asset_criticality,
                days_since=0,
                w1=w1, w2=w2, w3=w3, w4=w4,
            )
            tier = priority_tier(score)

            st.success(f"Priority Score: {score:.1f} ({tier})")
            st.subheader("Summary")
            st.write(pred["summary"])
            st.subheader("IOCs")
            st.json(pred["iocs"])
            st.subheader("Keywords")
            st.write(", ".join(pred["keywords"][:20]))


