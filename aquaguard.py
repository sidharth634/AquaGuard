import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import time
import sqlite3
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# ---------------- DATABASE CONFIG & HELPERS ----------------
DB_NAME = "aquaguard_history.db"

def get_db_connection():
    # SQLite connection with safe timeout for Streamlit threads
    return sqlite3.connect(DB_NAME, timeout=10.0)

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS water_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                persona TEXT,
                ph REAL,
                turbidity TEXT,
                tds INTEGER,
                season TEXT,
                risk_score INTEGER,
                risk_level TEXT
            )
        """)
        conn.commit()

def save_analysis(persona, ph, turbidity, tds, season, risk_score, risk_level):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Convert UTC to IST (+5:30) for correct timezone display on cloud hosting
        from datetime import timezone, timedelta
        utc_now = datetime.now(timezone.utc)
        ist_now = utc_now + timedelta(hours=5, minutes=30)
        now_str = ist_now.strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO water_history (timestamp, persona, ph, turbidity, tds, season, risk_score, risk_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (now_str, persona, ph, turbidity, tds, season, risk_score, risk_level))
        conn.commit()

def fetch_history():
    with get_db_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM water_history ORDER BY id DESC", conn)
        return df

def clear_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM water_history")
        conn.commit()

# Initialize DB on load
init_db()

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="AquaGuard AI",
    page_icon="💧",
    layout="wide"
)

# ---------------- SESSION STATE INIT ----------------
if "ph_slider" not in st.session_state:
    st.session_state.ph_slider = 7.0

if "ph_text" not in st.session_state:
    st.session_state.ph_text = 7.0

# ---------------- CALLBACK FUNCTIONS ----------------
def sync_slider_to_text():
    st.session_state.ph_text = st.session_state.ph_slider

def sync_text_to_slider():
    st.session_state.ph_slider = st.session_state.ph_text

# ---------------- HEADER ----------------
st.markdown(
    """
    <h1 style='text-align:center;color:#1f77b4;'>💧 AquaGuard AI</h1>
    <h4 style='text-align:center;'>Smart Water Quality Monitoring & Early Warning System</h4>
    <p style='text-align:center;'>SDG 6 – Clean Water & Sanitation</p>
    <hr>
    """,
    unsafe_allow_html=True
)

# ---------------- SIDEBAR NAVIGATION ----------------
st.sidebar.markdown("### 🗺️ Navigation")
page = st.sidebar.radio(
    "Select Page:",
    ["Dashboard", "History"]
)

# ---------------- RUN DASHBOARD OR HISTORY PAGE ----------------
if page == "Dashboard":
    # ---------------- SIDEBAR FOR DASHBOARD ----------------
    st.sidebar.header("👤 User Persona")
    persona = st.sidebar.radio(
        "Select usage environment:",
        ["Home", "School", "Hospital"]
    )

    st.sidebar.header("🔍 Water Quality Inputs")

    # -------- pH INPUT (TRUE TWO-WAY SYNC) --------
    st.sidebar.subheader("pH Level")

    st.sidebar.slider(
        "Adjust pH using slider",
        min_value=0.0,
        max_value=14.0,
        step=0.1,
        key="ph_slider",
        on_change=sync_slider_to_text
    )

    st.sidebar.number_input(
        "Enter pH value manually",
        min_value=0.0,
        max_value=14.0,
        step=0.1,
        key="ph_text",
        on_change=sync_text_to_slider
    )

    ph = st.session_state.ph_slider

    turbidity = st.sidebar.selectbox("Turbidity Level", ["Low", "Medium", "High"])
    tds = st.sidebar.number_input("TDS (ppm)", min_value=0, value=300)
    season = st.sidebar.selectbox("Season", ["Summer", "Winter", "Monsoon"])

    # ---------------- BASIC DEFINITIONS ----------------
    st.sidebar.markdown("---")
    st.sidebar.subheader("📘 Parameter Basics")

    st.sidebar.info(
        """
        **pH Level**  
        Measures acidity or alkalinity of water.  
        Safe range: **6.5 – 8.5**

        **Turbidity**  
        Cloudiness caused by particles.  
        High turbidity may carry microbes.

        **TDS (Total Dissolved Solids)**  
        Dissolved salts & minerals.  
        >500 ppm reduces water quality.
        """
    )

    # ---------------- AI RULE LOGIC ----------------
    risk_score = 0
    reasons = []
    risk_map = {
        "pH Issue": 0,
        "High Turbidity": 0,
        "High TDS": 0,
        "Seasonal Risk": 0
    }

    if ph < 6.5 or ph > 8.5:
        risk_score += 1
        risk_map["pH Issue"] = 1
        reasons.append("pH is outside the safe drinking range (6.5–8.5).")

    if turbidity == "High":
        risk_score += 1
        risk_map["High Turbidity"] = 1
        reasons.append("High turbidity increases microbial contamination risk.")

    if tds > 500:
        risk_score += 1
        risk_map["High TDS"] = 1
        reasons.append("High TDS indicates excess dissolved solids.")

    if season == "Monsoon":
        risk_score += 1
        risk_map["Seasonal Risk"] = 1
        reasons.append("Monsoon increases contamination due to runoff and flooding.")

    # Extra reasoning
    reasons.append("Multiple unsafe parameters together compound health risks.")
    reasons.append("Improper storage can worsen already unsafe water.")

    # ---------------- RISK CLASSIFICATION ----------------
    if risk_score >= 3:
        risk = "High Risk"
    elif risk_score == 2:
        risk = "Medium Risk"
    else:
        risk = "Safe"

    # Automatically save analysis without duplicates
    current_inputs = (persona, ph, turbidity, tds, season, risk_score, risk)
    if "last_saved_inputs" not in st.session_state:
        st.session_state.last_saved_inputs = None

    if st.session_state.last_saved_inputs != current_inputs:
        try:
            save_analysis(persona, ph, turbidity, tds, season, risk_score, risk)
            st.session_state.last_saved_inputs = current_inputs
        except Exception as e:
            st.error(f"Error saving to database: {e}")

    # ---------------- PERSONA ALERTS & RECOMMENDATIONS ----------------
    if persona == "Home":
        alert = "⚠️ Home Alert: Unsafe water may cause long-term family health issues."
        advice = [
            "Boil water for at least 5 minutes",
            "Use certified household water purifiers",
            "Avoid giving untreated water to children & elderly",
            "Clean storage tanks weekly"
        ]
    elif persona == "School":
        alert = "🚨 School Alert: Children are highly vulnerable to water-borne diseases."
        advice = [
            "Do NOT allow direct drinking of untreated water",
            "Provide only filtered or boiled water",
            "Monitor students for symptoms",
            "Perform regular water testing"
        ]
    else:
        alert = "🚨 Hospital Alert: Unsafe water is extremely dangerous for patients."
        advice = [
            "STRICTLY avoid untreated water",
            "Use only RO or sterilized water",
            "Never use unsafe water for medical procedures",
            "Immediate corrective action required"
        ]

    # ---------------- DASHBOARD PAGE ----------------
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("🧠 AI Risk Assessment")
        time.sleep(0.2)

        if risk == "High Risk":
            st.error("🚨 WATER STATUS: HIGH RISK")
        elif risk == "Medium Risk":
            st.warning("⚠️ WATER STATUS: MEDIUM RISK")
        else:
            st.success("✅ WATER STATUS: SAFE")

        # Explainable AI: AI Decision Summary Card
        status_color = "#2ca02c" if risk == "Safe" else ("#ff7f0e" if risk == "Medium Risk" else "#d62728")
        st.markdown(f"""
        <div style="border: 1px solid #e6e9ef; border-radius: 8px; padding: 15px; background-color: #fdfdfd; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; border-left: 5px solid {status_color};">
            <h4 style="margin-top: 0; color: #1f77b4; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
                🧠 AI Decision Summary
            </h4>
            <hr style="margin: 8px 0 12px 0; border: 0; border-top: 1px solid #eee;">
            <div style="display: flex; flex-wrap: wrap; justify-content: space-between; gap: 10px; font-family: sans-serif;">
                <div style="flex: 1; min-width: 100px;">
                    <span style="font-size: 0.75rem; color: #666; text-transform: uppercase; font-weight: bold; display: block; margin-bottom: 3px;">Final Risk</span>
                    <span style="font-size: 1.0rem; font-weight: bold; color: {status_color};">{risk}</span>
                </div>
                <div style="flex: 1; min-width: 100px;">
                    <span style="font-size: 0.75rem; color: #666; text-transform: uppercase; font-weight: bold; display: block; margin-bottom: 3px;">Risk Score</span>
                    <span style="font-size: 1.0rem; font-weight: bold; color: #333;">{risk_score} / 4</span>
                </div>
                <div style="flex: 1; min-width: 100px;">
                    <span style="font-size: 0.75rem; color: #666; text-transform: uppercase; font-weight: bold; display: block; margin-bottom: 3px;">Triggered Rules</span>
                    <span style="font-size: 1.0rem; font-weight: bold; color: #333;">{risk_score}</span>
                </div>
                <div style="flex: 1; min-width: 100px;">
                    <span style="font-size: 0.75rem; color: #666; text-transform: uppercase; font-weight: bold; display: block; margin-bottom: 3px;">Water Status</span>
                    <span style="display: inline-block; padding: 2px 6px; border-radius: 4px; color: white; background-color: {status_color}; font-size: 0.8rem; font-weight: bold;">
                        {risk.upper()}
                    </span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 📊 Risk Gauge")
        st.progress(risk_score / 4)

        st.markdown("### 📉 Risk Contributing Factors")
        fig, ax = plt.subplots()
        ax.bar(list(risk_map.keys()), list(risk_map.values()))
        ax.set_ylim(0, 1.2)
        ax.set_ylabel("Triggered (1 = Yes)")
        plt.xticks(rotation=90)
        st.pyplot(fig)

        # Plotly Donut Chart (Risk Contribution)
        st.markdown("### 🍩 Risk Contribution")
        triggered_rules = {k: v for k, v in risk_map.items() if v == 1}
        if triggered_rules:
            chart_labels = []
            if ph < 6.5 or ph > 8.5:
                chart_labels.append(f"pH ({ph})")
            if turbidity == "High":
                chart_labels.append("Turbidity (High)")
            if tds > 500:
                chart_labels.append(f"TDS ({tds} ppm)")
            if season == "Monsoon":
                chart_labels.append("Season (Monsoon)")

            chart_values = [100.0 / len(chart_labels)] * len(chart_labels)
            fig_donut = go.Figure(data=[go.Pie(
                labels=chart_labels,
                values=chart_values,
                hole=0.5,
                textinfo='percent+label',
                marker=dict(colors=['#d62728', '#ff7f0e', '#1f77b4', '#9467bd'])
            )])
            fig_donut.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                height=250,
                showlegend=True
            )
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("No risk factors contributed.")

        st.markdown("### 🔍 AI Reasoning (Why this result?)")
        for r in reasons:
            st.write("•", r)

        # Triggered and Non-triggered Rules Details
        st.markdown("### 🔬 Detailed Rule Analysis")
        
        # pH rule detail
        if ph < 6.5 or ph > 8.5:
            st.markdown(f"""
            <div style="padding: 12px; border-left: 4px solid #d62728; background-color: #fdf2f2; border-radius: 4px; margin-bottom: 12px; font-family: sans-serif;">
                <span style="color: #d62728; font-weight: bold; font-size: 1.05rem;">✔ pH Rule Triggered</span><br>
                <div style="margin-top: 5px; font-size: 0.95rem; color: #333;">
                    Current pH = <b>{ph}</b><br>
                    Safe Range = <b>6.5–8.5</b><br>
                    <b>Reason:</b><br>
                    The water is {'acidic' if ph < 6.5 else 'alkaline'} and may corrode plumbing while affecting drinking quality.
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="padding: 12px; border-left: 4px solid #2ca02c; background-color: #f4faf4; border-radius: 4px; margin-bottom: 12px; font-family: sans-serif;">
                <span style="color: #2ca02c; font-weight: bold; font-size: 1.05rem;">✔ pH is within safe limits</span><br>
                <div style="margin-top: 5px; font-size: 0.95rem; color: #333;">
                    Current pH = <b>{ph}</b> is within the safe drinking range of 6.5–8.5.
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Turbidity rule detail
        if turbidity == "High":
            st.markdown("""
            <div style="padding: 12px; border-left: 4px solid #d62728; background-color: #fdf2f2; border-radius: 4px; margin-bottom: 12px; font-family: sans-serif;">
                <span style="color: #d62728; font-weight: bold; font-size: 1.05rem;">✔ Turbidity Rule Triggered</span><br>
                <div style="margin-top: 5px; font-size: 0.95rem; color: #333;">
                    Current Turbidity = <b>High</b><br>
                    <b>Reason:</b><br>
                    High turbidity may hide microorganisms and reduce disinfection effectiveness.
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="padding: 12px; border-left: 4px solid #2ca02c; background-color: #f4faf4; border-radius: 4px; margin-bottom: 12px; font-family: sans-serif;">
                <span style="color: #2ca02c; font-weight: bold; font-size: 1.05rem;">✔ Turbidity is within safe limits</span><br>
                <div style="margin-top: 5px; font-size: 0.95rem; color: #333;">
                    Current Turbidity = <b>{turbidity}</b> is within acceptable cloudiness limits.
                </div>
            </div>
            """, unsafe_allow_html=True)

        # TDS rule detail
        if tds > 500:
            st.markdown(f"""
            <div style="padding: 12px; border-left: 4px solid #d62728; background-color: #fdf2f2; border-radius: 4px; margin-bottom: 12px; font-family: sans-serif;">
                <span style="color: #d62728; font-weight: bold; font-size: 1.05rem;">✔ High TDS Rule Triggered</span><br>
                <div style="margin-top: 5px; font-size: 0.95rem; color: #333;">
                    Current TDS = <b>{tds} ppm</b><br>
                    Recommended <b>&lt;500 ppm</b><br>
                    <b>Reason:</b><br>
                    High dissolved solids can affect taste and may indicate contamination.
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="padding: 12px; border-left: 4px solid #2ca02c; background-color: #f4faf4; border-radius: 4px; margin-bottom: 12px; font-family: sans-serif;">
                <span style="color: #2ca02c; font-weight: bold; font-size: 1.05rem;">✔ TDS is within safe limits</span><br>
                <div style="margin-top: 5px; font-size: 0.95rem; color: #333;">
                    Current TDS = <b>{tds} ppm</b> is within the recommended limit of &lt;500 ppm.
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Seasonal rule detail
        if season == "Monsoon":
            st.markdown("""
            <div style="padding: 12px; border-left: 4px solid #d62728; background-color: #fdf2f2; border-radius: 4px; margin-bottom: 12px; font-family: sans-serif;">
                <span style="color: #d62728; font-weight: bold; font-size: 1.05rem;">✔ Seasonal Rule Triggered</span><br>
                <div style="margin-top: 5px; font-size: 0.95rem; color: #333;">
                    Current Season = <b>Monsoon</b><br>
                    <b>Reason:</b><br>
                    Monsoon increases runoff and contamination probability.
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="padding: 12px; border-left: 4px solid #2ca02c; background-color: #f4faf4; border-radius: 4px; margin-bottom: 12px; font-family: sans-serif;">
                <span style="color: #2ca02c; font-weight: bold; font-size: 1.05rem;">✔ Seasonal risk is low</span><br>
                <div style="margin-top: 5px; font-size: 0.95rem; color: #333;">
                    Current Season = <b>{season}</b> has standard seasonal baseline risk.
                </div>
            </div>
            """, unsafe_allow_html=True)

        # How AquaGuard AI Made This Decision Flow Box
        with st.expander("🔗 How AquaGuard AI Made This Decision", expanded=False):
            st.markdown("""
            <div style="font-size: 0.95rem; line-height: 1.8; font-family: sans-serif;">
                <div style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 10px; margin-bottom: 5px;">
                    📝 <b>Input Parameters</b><br>
                    <span style="color: #555;">Received user inputs (Persona: <b>Home/School/Hospital</b>, pH, Turbidity, TDS, Season)</span>
                </div>
                <div style="text-align: center; color: #1f77b4; font-weight: bold; font-size: 1.2rem; margin: 2px 0;">↓</div>
                <div style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 10px; margin-bottom: 5px;">
                    🧪 <b>Evaluate pH</b><br>
                    <span style="color: #555;">Checks if pH is outside the safe range (6.5 – 8.5)</span>
                </div>
                <div style="text-align: center; color: #1f77b4; font-weight: bold; font-size: 1.2rem; margin: 2px 0;">↓</div>
                <div style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 10px; margin-bottom: 5px;">
                    🌫️ <b>Evaluate Turbidity</b><br>
                    <span style="color: #555;">Checks if water has High Turbidity (cloudiness)</span>
                </div>
                <div style="text-align: center; color: #1f77b4; font-weight: bold; font-size: 1.2rem; margin: 2px 0;">↓</div>
                <div style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 10px; margin-bottom: 5px;">
                    📊 <b>Evaluate TDS</b><br>
                    <span style="color: #555;">Checks if Total Dissolved Solids exceeds the 500 ppm threshold</span>
                </div>
                <div style="text-align: center; color: #1f77b4; font-weight: bold; font-size: 1.2rem; margin: 2px 0;">↓</div>
                <div style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 10px; margin-bottom: 5px;">
                    🍂 <b>Evaluate Seasonal Risk</b><br>
                    <span style="color: #555;">Checks if the current season is Monsoon (high surface runoff risk)</span>
                </div>
                <div style="text-align: center; color: #1f77b4; font-weight: bold; font-size: 1.2rem; margin: 2px 0;">↓</div>
                <div style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 10px; margin-bottom: 5px;">
                    🧮 <b>Calculate Risk Score</b><br>
                    <span style="color: #555;">Aggregates the total number of triggered rules (0 to 4)</span>
                </div>
                <div style="text-align: center; color: #1f77b4; font-weight: bold; font-size: 1.2rem; margin: 2px 0;">↓</div>
                <div style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 10px; margin-bottom: 5px;">
                    🏷️ <b>Classify Risk Level</b><br>
                    <span style="color: #555;">Categorizes risk as: <b>Safe</b> (Score 0-1), <b>Medium Risk</b> (Score 2), or <b>High Risk</b> (Score 3+)</span>
                </div>
                <div style="text-align: center; color: #1f77b4; font-weight: bold; font-size: 1.2rem; margin: 2px 0;">↓</div>
                <div style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 10px; margin-bottom: 5px;">
                    💡 <b>Generate Recommendations</b><br>
                    <span style="color: #555;">Constructs prioritized safety advices based on selected usage Persona</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.subheader("🚨 Persona-Based Alert")
        st.warning(alert)

        # Prioritized Recommendations
        st.subheader("🛡️ Prioritized Recommendations")
        
        critical_items = []
        recommended_items = []
        preventive_items = []
        
        if persona == "Home":
            critical_items = [
                "Boil water for at least 5 minutes",
                "Avoid giving untreated water to children & elderly"
            ]
            recommended_items = [
                "Use certified household water purifiers"
            ]
            preventive_items = [
                "Clean storage tanks weekly"
            ]
        elif persona == "School":
            critical_items = [
                "Do NOT allow direct drinking of untreated water",
                "Provide only filtered or boiled water"
            ]
            recommended_items = [
                "Monitor students for symptoms"
            ]
            preventive_items = [
                "Perform regular water testing"
            ]
        else:  # Hospital
            critical_items = [
                "STRICTLY avoid untreated water",
                "Never use unsafe water for medical procedures",
                "Immediate corrective action required"
            ]
            recommended_items = [
                "Use only RO or sterilized water"
            ]
            preventive_items = [
                "Perform daily quality checks and clean sanitization loops"
            ]

        # Prioritized lists display
        st.markdown("""
        <div style="margin-bottom: 8px;">
            <span style="background-color: #ffebee; color: #c62828; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8rem; letter-spacing: 0.5px;">CRITICAL</span>
        </div>
        """, unsafe_allow_html=True)
        for item in critical_items:
            st.write("🔴", item)
            
        st.markdown("""
        <div style="margin-top: 15px; margin-bottom: 8px;">
            <span style="background-color: #fff3e0; color: #ef6c00; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8rem; letter-spacing: 0.5px;">RECOMMENDED</span>
        </div>
        """, unsafe_allow_html=True)
        for item in recommended_items:
            st.write("🟡", item)
            
        st.markdown("""
        <div style="margin-top: 15px; margin-bottom: 8px;">
            <span style="background-color: #e8f5e9; color: #2e7d32; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8rem; letter-spacing: 0.5px;">PREVENTIVE</span>
        </div>
        """, unsafe_allow_html=True)
        for item in preventive_items:
            st.write("🟢", item)

        # Health Impacts section
        health_impacts = []
        if ph < 6.5 or ph > 8.5:
            health_impacts.append(("Unsafe pH", ["• Corrosion", "• Digestive discomfort"]))
        if turbidity == "High":
            health_impacts.append(("High Turbidity", ["• Waterborne diseases", "• Diarrhea", "• Cholera"]))
        if tds > 500:
            health_impacts.append(("High TDS", ["• Poor taste", "• Kidney stress", "• Excess minerals"]))
        if season == "Monsoon":
            health_impacts.append(("Monsoon", ["• Increased microbial contamination"]))
            
        st.markdown("---")
        st.subheader("⚠️ Potential Health Impact")
        if health_impacts:
            for title, items in health_impacts:
                st.markdown(f"**{title}**")
                for item in items:
                    st.write(item)
        else:
            st.write("🟢 No current risk parameters active. Water health risks are low.")

        st.markdown("---")
        st.subheader("💙 Water Safety Awareness")
        st.info(
            """
            • Unsafe water causes diarrhea, cholera, typhoid, hepatitis  
            • Children, elderly, and patients face highest risk  
            • Long-term exposure may damage kidneys & digestion  
            • Contaminated water can trigger community outbreaks  
            • Early prevention saves lives and costs  
            """
        )

else:  # History Page
    st.subheader("📜 Historical Water Quality Analyses")
    
    df = fetch_history()
    
    if df.empty:
        st.info("No historical analyses found. Perform some analyses on the Dashboard to populate the database.")
    else:
        # Aggregated KPI Metrics
        total_count = len(df)
        safe_count = len(df[df['risk_level'] == 'Safe'])
        medium_count = len(df[df['risk_level'] == 'Medium Risk'])
        high_count = len(df[df['risk_level'] == 'High Risk'])
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("📊 Total Analyses", total_count)
        col_m2.metric("✅ Safe Analyses", safe_count)
        col_m3.metric("⚠️ Medium Risk", medium_count)
        col_m4.metric("🚨 High Risk", high_count)
        
        st.markdown("---")
        st.subheader("🔍 Filters & Search")
        
        # Row of Selectors
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            selected_personas = st.multiselect(
                "Filter by Persona", 
                options=["Home", "School", "Hospital"], 
                default=["Home", "School", "Hospital"]
            )
        with col_f2:
            selected_risks = st.multiselect(
                "Filter by Risk Level", 
                options=["Safe", "Medium Risk", "High Risk"], 
                default=["Safe", "Medium Risk", "High Risk"]
            )
        with col_f3:
            selected_seasons = st.multiselect(
                "Filter by Season", 
                options=["Summer", "Winter", "Monsoon"], 
                default=["Summer", "Winter", "Monsoon"]
            )
            
        search_query = st.text_input("🔍 Search History (type persona, risk level, or season to search):", "")
        
        # Apply filters
        filtered_df = df.copy()
        if selected_personas:
            filtered_df = filtered_df[filtered_df['persona'].isin(selected_personas)]
        if selected_risks:
            filtered_df = filtered_df[filtered_df['risk_level'].isin(selected_risks)]
        if selected_seasons:
            filtered_df = filtered_df[filtered_df['season'].isin(selected_seasons)]
            
        if search_query:
            filtered_df = filtered_df[
                filtered_df['persona'].str.contains(search_query, case=False) |
                filtered_df['risk_level'].str.contains(search_query, case=False) |
                filtered_df['season'].str.contains(search_query, case=False) |
                filtered_df['turbidity'].str.contains(search_query, case=False)
            ]
            
        st.markdown("### Latest Water Analyses")
        st.dataframe(filtered_df, use_container_width=True)
        
        # CSV Export & Database Clean Buttons
        col_ex1, col_ex2 = st.columns([1, 4])
        with col_ex1:
            csv_data = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download History as CSV",
                data=csv_data,
                file_name="aquaguard_history.csv",
                mime="text/csv"
            )
        with col_ex2:
            if st.button("🗑️ Clear History"):
                st.session_state.confirm_clear = True
                
            if st.session_state.get("confirm_clear"):
                st.warning("⚠️ Are you sure you want to permanently delete all historical data?")
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    if st.button("Yes, Clear Everything"):
                        clear_db()
                        st.session_state.confirm_clear = False
                        st.success("History cleared successfully!")
                        st.rerun()
                with col_c2:
                    if st.button("Cancel"):
                        st.session_state.confirm_clear = False
                        st.rerun()
                        
        st.markdown("---")
        st.subheader("📈 Interactive Visualizations")
        
        if filtered_df.empty:
            st.warning("No records match the selected filters. Change filters to see charts.")
        else:
            # 1. Pie chart & 2. Bar chart side-by-side
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                fig_pie = px.pie(
                    filtered_df, 
                    names='risk_level', 
                    title='Risk Distribution',
                    color='risk_level',
                    color_discrete_map={'Safe': '#2ca02c', 'Medium Risk': '#ff7f0e', 'High Risk': '#d62728'},
                    hole=0.4
                )
                fig_pie.update_layout(margin=dict(t=40, b=10, l=10, r=10), height=300)
                st.plotly_chart(fig_pie, use_container_width=True)
                
            with col_chart2:
                risk_counts = filtered_df['risk_level'].value_counts().reset_index()
                risk_counts.columns = ['Risk Level', 'Count']
                all_levels = pd.DataFrame({'Risk Level': ['Safe', 'Medium Risk', 'High Risk']})
                risk_counts = all_levels.merge(risk_counts, on='Risk Level', how='left').fillna(0)
                
                fig_bar = px.bar(
                    risk_counts, 
                    x='Risk Level', 
                    y='Count', 
                    color='Risk Level',
                    color_discrete_map={'Safe': '#2ca02c', 'Medium Risk': '#ff7f0e', 'High Risk': '#d62728'},
                    title='Analyses Count by Risk Level'
                )
                fig_bar.update_layout(margin=dict(t=40, b=10, l=10, r=10), height=300, showlegend=False)
                st.plotly_chart(fig_bar, use_container_width=True)
                
            # 3. Daily Analysis Count Line Chart
            chart_df = filtered_df.copy()
            chart_df['date'] = pd.to_datetime(chart_df['timestamp']).dt.date
            chart_df = chart_df.sort_values('date')
            daily_counts = chart_df.groupby('date').size().reset_index(name='Analyses')
            
            fig_daily = px.line(
                daily_counts, 
                x='date', 
                y='Analyses', 
                title='Daily Analysis Count',
                markers=True
            )
            fig_daily.update_layout(margin=dict(t=40, b=10, l=10, r=10), height=300)
            st.plotly_chart(fig_daily, use_container_width=True)
            
            # 4. Avg pH & 5. Avg TDS Trends
            col_chart3, col_chart4 = st.columns(2)
            
            with col_chart3:
                ph_trend = chart_df.groupby('date')['ph'].mean().reset_index(name='avg_ph')
                fig_ph = px.line(
                    ph_trend, 
                    x='date', 
                    y='avg_ph', 
                    title='Average pH Trend',
                    markers=True
                )
                fig_ph.add_hline(y=6.5, line_dash="dash", line_color="green", annotation_text="Min Safe pH (6.5)", annotation_position="top left")
                fig_ph.add_hline(y=8.5, line_dash="dash", line_color="green", annotation_text="Max Safe pH (8.5)", annotation_position="bottom left")
                fig_ph.update_layout(margin=dict(t=40, b=10, l=10, r=10), height=300)
                st.plotly_chart(fig_ph, use_container_width=True)
                
            with col_chart4:
                tds_trend = chart_df.groupby('date')['tds'].mean().reset_index(name='avg_tds')
                fig_tds = px.line(
                    tds_trend, 
                    x='date', 
                    y='avg_tds', 
                    title='Average TDS Trend',
                    markers=True
                )
                fig_tds.add_hline(y=500.0, line_dash="dash", line_color="red", annotation_text="Max Rec TDS (500 ppm)", annotation_position="bottom left")
                fig_tds.update_layout(margin=dict(t=40, b=10, l=10, r=10), height=300)
                st.plotly_chart(fig_tds, use_container_width=True)

# ---------------- FOOTER ----------------
st.markdown("---")
st.markdown(
    """
    <p style='text-align:center;font-size:13px;'>
    Built for the <b>1M1B – IBM SkillsBuild AI for Sustainability Virtual Internship</b><br>
    Rule-Based | Explainable | Ethical | Impact-Driven
    </p>
    """,
    unsafe_allow_html=True
)