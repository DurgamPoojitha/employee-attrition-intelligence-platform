import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
import json

# ── Page Configuration ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Workforce Attrition Intelligence Platform",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Dark gradient background */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        min-height: 100vh;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(255,255,255,0.05);
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255,255,255,0.1);
    }
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stSlider label,
    [data-testid="stSidebar"] .stNumberInput label {
        color: #94a3b8 !important;
        font-size: 0.8rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Main content */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    /* Header */
    .hero-header {
        background: linear-gradient(135deg, rgba(99,102,241,0.3) 0%, rgba(168,85,247,0.3) 100%);
        border: 1px solid rgba(99,102,241,0.4);
        border-radius: 20px;
        padding: 2.5rem;
        margin-bottom: 2rem;
        text-align: center;
        backdrop-filter: blur(10px);
    }
    .hero-header h1 {
        color: #f1f5f9;
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 0 30px rgba(168,85,247,0.5);
    }
    .hero-header p {
        color: #94a3b8;
        margin: 0.5rem 0 0 0;
        font-size: 1rem;
    }

    /* KPI Cards */
    .kpi-card {
        background: rgba(255,255,255,0.07);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        backdrop-filter: blur(10px);
        transition: transform 0.2s ease;
        height: 100%;
    }
    .kpi-card:hover {
        transform: translateY(-3px);
    }
    .kpi-label {
        color: #94a3b8;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.5rem;
    }
    .kpi-value {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }
    .kpi-sub {
        font-size: 0.8rem;
        color: #64748b;
    }

    /* Risk badges */
    .risk-critical { color: #ef4444; }
    .risk-high     { color: #f97316; }
    .risk-medium   { color: #eab308; }
    .risk-low      { color: #22c55e; }

    /* Recommendation card */
    .rec-card {
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
        border-left: 4px solid;
        backdrop-filter: blur(8px);
    }
    .rec-high {
        background: rgba(239,68,68,0.1);
        border-color: #ef4444;
    }
    .rec-medium {
        background: rgba(234,179,8,0.1);
        border-color: #eab308;
    }
    .rec-low {
        background: rgba(34,197,94,0.1);
        border-color: #22c55e;
    }
    .rec-title {
        font-weight: 600;
        font-size: 0.95rem;
        color: #f1f5f9;
        margin-bottom: 0.3rem;
    }
    .rec-detail {
        font-size: 0.82rem;
        color: #94a3b8;
        margin-bottom: 0.3rem;
    }
    .rec-impact {
        font-size: 0.78rem;
        font-weight: 500;
    }
    .impact-high   { color: #f87171; }
    .impact-medium { color: #fbbf24; }
    .impact-low    { color: #4ade80; }

    /* Section headers */
    .section-header {
        color: #e2e8f0;
        font-size: 1.1rem;
        font-weight: 600;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* Plot container */
    .plot-container {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 1.5rem;
        backdrop-filter: blur(10px);
    }

    /* Override Streamlit defaults */
    h1, h2, h3 { color: #f1f5f9 !important; }
    p { color: #cbd5e1; }
    .stMarkdown p { color: #cbd5e1; }
    div[data-testid="metric-container"] {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 1rem;
    }
    div[data-testid="metric-container"] label {
        color: #94a3b8 !important;
    }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        color: #f1f5f9 !important;
    }
    .stButton > button {
        background: linear-gradient(135deg, #6366f1, #a855f7);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2.5rem;
        font-weight: 600;
        font-size: 1rem;
        cursor: pointer;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(99,102,241,0.4);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(99,102,241,0.6);
    }
    .stSlider [data-testid="stTickBar"] { color: #94a3b8; }

    /* Sidebar category header */
    .sidebar-category {
        color: #818cf8 !important;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        margin: 1.2rem 0 0.4rem 0;
    }
    .hr-div {
        border: none;
        border-top: 1px solid rgba(255,255,255,0.08);
        margin: 0.5rem 0 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ── API Configuration ──────────────────────────────────────────────────────────
API_URL = "http://127.0.0.1:8000"

# ── Helper Functions ───────────────────────────────────────────────────────────
def get_risk_css_class(category: str) -> str:
    mapping = {
        "Critical Risk": "risk-critical",
        "High Risk":     "risk-high",
        "Medium Risk":   "risk-medium",
        "Low Risk":      "risk-low",
    }
    return mapping.get(category, "risk-low")

def get_risk_emoji(category: str) -> str:
    mapping = {
        "Critical Risk": "🔴",
        "High Risk":     "🟠",
        "Medium Risk":   "🟡",
        "Low Risk":      "🟢",
    }
    return mapping.get(category, "🟢")

def call_predict_api(payload: dict) -> dict | None:
    try:
        res = requests.post(f"{API_URL}/predict", json=payload, timeout=10)
        if res.status_code == 200:
            return res.json()
        else:
            st.error(f"API Error {res.status_code}: {res.text}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot connect to FastAPI backend. Please start the API first:\n```\nsource venv/bin/activate && uvicorn app:app --host 127.0.0.1 --port 8000\n```")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return None

def check_api_health() -> bool:
    try:
        res = requests.get(f"{API_URL}/health", timeout=5)
        return res.status_code == 200
    except Exception:
        return False

# ── Hero Header ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-header">
    <h1>🧠 Workforce Attrition Intelligence Platform</h1>
    <p>Enterprise-grade predictive analytics · Real-time flight risk scoring · AI-powered retention recommendations</p>
</div>
""", unsafe_allow_html=True)

# ── API Status Banner ──────────────────────────────────────────────────────────
api_healthy = check_api_health()
if api_healthy:
    st.success("✅ Connected to Prediction API — Model loaded and ready")
else:
    st.warning("⚠️ Prediction API offline. Start it with: `source venv/bin/activate && uvicorn app:app --host 127.0.0.1 --port 8000`")

# ── Sidebar Inputs ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 👤 Employee Profile")
    st.markdown('<hr class="hr-div">', unsafe_allow_html=True)

    # Demographics
    st.markdown('<p class="sidebar-category">Demographics</p>', unsafe_allow_html=True)
    age = st.slider("Age", 18, 65, 36)
    gender = st.selectbox("Gender", ["Male", "Female"])
    marital = st.selectbox("Marital Status", ["Single", "Married", "Divorced"])
    distance = st.slider("Distance From Home (km)", 1, 29, 9)

    # Job Details
    st.markdown('<hr class="hr-div"><p class="sidebar-category">Job Details</p>', unsafe_allow_html=True)
    dept = st.selectbox("Department", ["Research & Development", "Sales", "Human Resources"])
    role_options = {
        "Research & Development": ["Research Scientist", "Laboratory Technician", "Research Director", "Manufacturing Director", "Healthcare Representative", "Manager"],
        "Sales":                  ["Sales Executive", "Sales Representative"],
        "Human Resources":        ["Human Resources", "Manager"]
    }
    job_role = st.selectbox("Job Role", role_options[dept])
    job_level = st.slider("Job Level", 1, 5, 2)
    overtime = st.selectbox("OverTime", ["No", "Yes"])
    travel = st.selectbox("Business Travel", ["Travel_Rarely", "Travel_Frequently", "Non-Travel"])
    job_involvement = st.slider("Job Involvement", 1, 4, 3)
    education = st.slider("Education Level", 1, 5, 3)
    edu_field = st.selectbox("Education Field", ["Life Sciences", "Medical", "Marketing", "Technical Degree", "Human Resources", "Other"])

    # Satisfaction
    st.markdown('<hr class="hr-div"><p class="sidebar-category">Satisfaction Ratings</p>', unsafe_allow_html=True)
    job_sat = st.slider("Job Satisfaction", 1, 4, 3)
    env_sat = st.slider("Environment Satisfaction", 1, 4, 3)
    rel_sat = st.slider("Relationship Satisfaction", 1, 4, 3)
    wlb = st.slider("Work-Life Balance", 1, 4, 3)
    perf_rating = st.slider("Performance Rating", 1, 4, 3)

    # Compensation & Tenure
    st.markdown('<hr class="hr-div"><p class="sidebar-category">Compensation & Tenure</p>', unsafe_allow_html=True)
    monthly_income = st.number_input("Monthly Income ($)", min_value=1000, max_value=25000, value=5000, step=250)
    stock_option = st.slider("Stock Option Level", 0, 3, 1)
    pct_hike = st.slider("% Salary Hike Last Year", 11, 25, 15)
    hourly_rate = st.slider("Hourly Rate", 30, 100, 66)
    daily_rate = st.slider("Daily Rate", 102, 1499, 800)
    monthly_rate = st.slider("Monthly Rate", 2094, 26999, 14000)

    st.markdown('<hr class="hr-div"><p class="sidebar-category">Work History</p>', unsafe_allow_html=True)
    yrs_company = st.slider("Years at Company", 0, 40, 5)
    yrs_role = st.slider("Years in Current Role", 0, 18, 4)
    yrs_promo = st.slider("Years Since Last Promotion", 0, 15, 1)
    yrs_mgr = st.slider("Years with Current Manager", 0, 17, 3)
    total_yrs = st.slider("Total Working Years", 0, 40, 10)
    num_companies = st.slider("Num Companies Worked", 0, 9, 2)
    training = st.slider("Training Times Last Year", 0, 6, 3)

    st.markdown('<br>', unsafe_allow_html=True)
    predict_btn = st.button("🔍 Run Attrition Analysis")

# ── Payload Builder ─────────────────────────────────────────────────────────────
payload = {
    "Age": age,
    "BusinessTravel": travel,
    "DailyRate": daily_rate,
    "Department": dept,
    "DistanceFromHome": distance,
    "Education": education,
    "EducationField": edu_field,
    "EnvironmentSatisfaction": env_sat,
    "Gender": gender,
    "HourlyRate": hourly_rate,
    "JobInvolvement": job_involvement,
    "JobLevel": job_level,
    "JobRole": job_role,
    "JobSatisfaction": job_sat,
    "MaritalStatus": marital,
    "MonthlyIncome": monthly_income,
    "MonthlyRate": monthly_rate,
    "NumCompaniesWorked": num_companies,
    "OverTime": overtime,
    "PercentSalaryHike": pct_hike,
    "PerformanceRating": perf_rating,
    "RelationshipSatisfaction": rel_sat,
    "StockOptionLevel": stock_option,
    "TotalWorkingYears": total_yrs,
    "TrainingTimesLastYear": training,
    "WorkLifeBalance": wlb,
    "YearsAtCompany": yrs_company,
    "YearsInCurrentRole": yrs_role,
    "YearsSinceLastPromotion": yrs_promo,
    "YearsWithCurrManager": yrs_mgr,
}

# ── Session State ───────────────────────────────────────────────────────────────
if "result" not in st.session_state:
    st.session_state.result = None
if "last_payload" not in st.session_state:
    st.session_state.last_payload = None

# Auto-run on first load if API is available
if st.session_state.result is None and api_healthy:
    with st.spinner("Running initial analysis…"):
        st.session_state.result = call_predict_api(payload)
        st.session_state.last_payload = payload.copy()

if predict_btn and api_healthy:
    with st.spinner("Running attrition analysis…"):
        st.session_state.result = call_predict_api(payload)
        st.session_state.last_payload = payload.copy()

# ── Results Display ─────────────────────────────────────────────────────────────
if st.session_state.result:
    result = st.session_state.result

    risk_pct   = result.get("FlightRiskProbability", "N/A")
    risk_cat   = result.get("RiskCategory", "N/A")
    fin_risk   = result.get("EstimatedFinancialRisk", "N/A")
    costs      = result.get("CostBreakdown", {})
    plan       = result.get("RetentionPlan", [])
    risk_class = get_risk_css_class(risk_cat)
    risk_emoji = get_risk_emoji(risk_cat)

    # ── KPI Row ───────────────────────────────────────────────────────────────
    st.markdown('<p class="section-header">📊 Risk Assessment</p>', unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)

    with k1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Flight Risk Score</div>
            <div class="kpi-value {risk_class}">{risk_pct}</div>
            <div class="kpi-sub">Probability of leaving</div>
        </div>""", unsafe_allow_html=True)

    with k2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Risk Category</div>
            <div class="kpi-value {risk_class}">{risk_emoji} {risk_cat}</div>
            <div class="kpi-sub">XGBoost Classification</div>
        </div>""", unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Estimated Financial Risk</div>
            <div class="kpi-value" style="color:#a78bfa;">{fin_risk}</div>
            <div class="kpi-sub">Full replacement cost</div>
        </div>""", unsafe_allow_html=True)

    with k4:
        high_count = sum(1 for r in plan if r.get("Priority") == "HIGH")
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">High Priority Actions</div>
            <div class="kpi-value" style="color:#fb923c;">{high_count}</div>
            <div class="kpi-sub">Recommended interventions</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts + Retention Plan ───────────────────────────────────────────────
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown('<p class="section-header">💰 Replacement Cost Breakdown</p>', unsafe_allow_html=True)

        # Parse values from strings like "$12,000.00"
        def parse_cost(s):
            try:
                return float(s.replace("$", "").replace(",", ""))
            except Exception:
                return 0.0

        cost_labels = ["Recruitment", "Training", "Productivity Loss", "Knowledge Drain"]
        cost_values = [
            parse_cost(costs.get("RecruitmentCost", "$0")),
            parse_cost(costs.get("TrainingCost", "$0")),
            parse_cost(costs.get("ProductivityLoss", "$0")),
            parse_cost(costs.get("KnowledgeDrainCost", "$0")),
        ]
        cost_colors = ["#6366f1", "#a855f7", "#ec4899", "#f97316"]

        fig_donut = go.Figure(data=[go.Pie(
            labels=cost_labels,
            values=cost_values,
            hole=0.55,
            marker=dict(colors=cost_colors, line=dict(color="#0f0c29", width=3)),
            textinfo="label+percent",
            textfont=dict(color="#f1f5f9", size=12),
            hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<extra></extra>",
        )])
        fig_donut.update_layout(
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=20, b=20, l=20, r=20),
            height=320,
            annotations=[dict(
                text=f"<b>{fin_risk}</b>",
                x=0.5, y=0.5,
                font=dict(size=16, color="#f1f5f9"),
                showarrow=False
            )]
        )
        st.plotly_chart(fig_donut, use_container_width=True)

        # Bar breakdown
        fig_bar = go.Figure(data=[go.Bar(
            x=cost_labels,
            y=cost_values,
            marker=dict(color=cost_colors, line=dict(width=0)),
            hovertemplate="<b>%{x}</b><br>$%{y:,.0f}<extra></extra>",
            text=[f"${v:,.0f}" for v in cost_values],
            textposition="outside",
            textfont=dict(color="#f1f5f9", size=11),
        )])
        fig_bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, tickfont=dict(color="#94a3b8"), title=""),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)",
                       tickfont=dict(color="#94a3b8"), tickprefix="$", title=""),
            margin=dict(t=30, b=20, l=20, r=20),
            height=280,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_right:
        st.markdown('<p class="section-header">🎯 Personalized Retention Plan</p>', unsafe_allow_html=True)

        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        sorted_plan = sorted(plan, key=lambda r: priority_order.get(r.get("Priority", "LOW"), 2))

        if sorted_plan:
            for rec in sorted_plan:
                action   = rec.get("Action", "")
                detail   = rec.get("Detail", "")
                priority = rec.get("Priority", "LOW")
                impact   = rec.get("Impact", "")
                css_cls  = f"rec-{priority.lower()}"
                imp_cls  = f"impact-{priority.lower()}"

                priority_icons = {"HIGH": "🚨", "MEDIUM": "⚠️", "LOW": "✅"}
                icon = priority_icons.get(priority, "✅")

                st.markdown(f"""
                <div class="rec-card {css_cls}">
                    <div class="rec-title">{icon} {action} <span style="font-size:0.7rem; font-weight:400; opacity:0.7;">· {priority} PRIORITY</span></div>
                    <div class="rec-detail">{detail}</div>
                    <div class="rec-impact {imp_cls}">📈 {impact}</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="rec-card rec-low" style="text-align:center; padding: 2rem;">
                <div style="font-size:2rem; margin-bottom:0.5rem;">✅</div>
                <div class="rec-title">No urgent interventions required</div>
                <div class="rec-detail">This employee shows healthy engagement and satisfaction metrics.</div>
            </div>""", unsafe_allow_html=True)

    # ── Feature Context Panel ──────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="section-header">🔬 Key Risk Drivers Analysis</p>', unsafe_allow_html=True)

    driver_cols = st.columns(4)
    comp_ratio = monthly_income / (job_level * 1000)
    eng_index  = ((job_sat-1)/3 + (env_sat-1)/3 + (rel_sat-1)/3 + (wlb-1)/3) / 4
    burnout    = 0.4*(1 if overtime=="Yes" else 0) + 0.3*(yrs_role/18) + 0.3*({"Non-Travel":0,"Travel_Rarely":1,"Travel_Frequently":2}.get(travel,0)/2)
    promo_gap  = yrs_promo / (total_yrs + 1)

    indicators = [
        ("Compensation Ratio", comp_ratio, 1.0, "Income vs. peer baseline"),
        ("Engagement Index",   eng_index,  0.6, "Composite satisfaction score"),
        ("Burnout Score",      min(burnout, 1.0), 0.4, "Overtime + travel + role tenure"),
        ("Promotion Gap",      min(promo_gap, 1.0), 0.4, "Career advancement velocity"),
    ]

    for col, (label, val, threshold, desc) in zip(driver_cols, indicators):
        is_risky = val < threshold if label in ("Compensation Ratio", "Engagement Index") else val > threshold
        indicator_color = "#ef4444" if is_risky else "#22c55e"
        status = "⚠️ Risk Factor" if is_risky else "✅ Healthy"
        with col:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value" style="color:{indicator_color}; font-size:1.8rem;">{val:.2f}</div>
                <div class="kpi-sub" style="color:{indicator_color}; font-weight:600;">{status}</div>
                <div class="kpi-sub" style="margin-top:0.3rem;">{desc}</div>
            </div>""", unsafe_allow_html=True)

    # ── Raw Output Expander ────────────────────────────────────────────────────
    with st.expander("🔧 Raw API Response (Debug View)"):
        st.json(result)

else:
    # ── Landing State ──────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    for col, title, desc, icon in [
        (c1, "Flight Risk Score",     "ML-powered probability of employee departure within 6 months", "🎯"),
        (c2, "Financial Impact",      "Full replacement cost breakdown: recruitment, training, productivity & knowledge", "💰"),
        (c3, "Retention Playbook",    "Personalized, priority-ranked HR intervention plan per employee", "📋"),
    ]:
        with col:
            st.markdown(f"""
            <div class="kpi-card" style="padding:2rem; text-align:center;">
                <div style="font-size:3rem; margin-bottom:1rem;">{icon}</div>
                <div style="color:#f1f5f9; font-size:1.1rem; font-weight:600; margin-bottom:0.5rem;">{title}</div>
                <div style="color:#94a3b8; font-size:0.85rem;">{desc}</div>
            </div>""", unsafe_allow_html=True)

    if not api_healthy:
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("👆 Start the API server and configure the sidebar to begin analysis.")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center; color:#475569; font-size:0.78rem; border-top:1px solid rgba(255,255,255,0.05); padding-top:1.5rem;">
    🧠 Workforce Attrition Intelligence Platform &nbsp;·&nbsp; Powered by XGBoost + FastAPI + MLflow &nbsp;·&nbsp; Built for Enterprise HR Teams
</div>
""", unsafe_allow_html=True)
