# 💧 AquaGuard AI
### Smart Water Quality Monitoring & Early Warning System
**Aligning with Sustainable Development Goal 6 (SDG 6): Clean Water & Sanitation**

AquaGuard AI is a lightweight, rule-based, and highly explainable Streamlit web application designed to monitor water quality and provide early warning risk assessments. It translates complex water metrics—such as pH, turbidity, and Total Dissolved Solids (TDS)—into actionable, persona-tailored safety guidance for homes, schools, and hospitals.

---

## 🔗 Live Application
🌐 **[Launch AquaGuard AI on Streamlit Cloud](https://aquaguard-xpzfxc7glhr8otmkgugewv.streamlit.app/)** 
*(Note: Replace with your actual live link if you customize the URL, but the default linked above matches your deployed instance!)*

---

## 🌟 Key Features

### 1. 🧠 Smart AI Risk Assessment (Dashboard)
- **Rule-Based Engine**: Leverages transparent ecological rules rather than black-box machine learning models to classify water samples.
- **Water Status Alerts**: Categorizes water as **Safe** (green), **Medium Risk** (yellow), or **High Risk** (red) using visual feedback elements.
- **Risk Gauge**: A real-time progression tracker showing the relative severity of contamination.

### 2. 🔬 Explainable AI (XAI) Panel
- **AI Decision Summary**: A high-level visual card detailing the final risk, numeric score, and count of active triggers.
- **Detailed Rule Analysis**: Evaluates each check (pH, Turbidity, TDS, Season) individually, showing current measurements alongside safe thresholds and explains the scientific reasoning behind every trigger.
- **Risk Contribution Donut Chart**: An interactive Plotly chart showcasing the proportional impact of each failing parameter on the total risk score.
- **Decision Flowchart**: An expandable flowchart mapping out the exact logical sequence of calculations executed by the system.

### 3. 🛡️ Persona-Based Warnings & Prioritized Recommendations
- Select from **Home**, **School**, or **Hospital** environments.
- Displays immediate persona-specific hazard warnings.
- Sorts advice dynamically into color-coded lists:
  - 🔴 **Critical**: Immediate life-safety actions (e.g., sterilization, boiling).
  - 🟡 **Recommended**: Filtration and monitoring actions.
  - 🟢 **Preventive**: Maintenance and routine quality assurance.
- **Potential Health Impact**: Lists specific health risks (such as cholera, diarrhea, and kidney stress) associated with active parameters.

### 4. 📜 Historical Data Analytics (History Page)
- **Auto-Saving Database**: Integrated with SQLite (`aquaguard_history.db`) to record all inputs, scores, and timestamps automatically (configured to prevent duplicate entries).
- **KPI Summary Cards**: Monitors total checks run and maps them across the three risk tiers.
- **Searchable & Filterable Table**: A clean data viewer with multi-select search filters for Persona, Risk Level, and Season.
- **Interactive Visualizations (Plotly)**:
  - **Risk Distribution**: Pie chart showing overall safety ratios.
  - **Risk Levels**: Bar chart displaying check counts.
  - **Daily Analysis Count**: Line chart plotting usage frequency.
  - **Average pH Trend**: A line chart containing dashed safe-limit lines (6.5 and 8.5) for comparison.
  - **Average TDS Trend**: A line chart containing a dashed threshold warning line (500 ppm).
- **History Control**: Exporter to download results as a **CSV file** or clear the database with confirmation guards.

---

## 📊 SDG 6 Alignment
AquaGuard AI directly supports **UN Sustainable Development Goal 6 (Target 6.1 & 6.3)** by:
- Enabling local communities to perform instant, understandable water testing.
- Preventing the ingestion of contaminants through immediate warnings.
- Promoting early sanitation intervention in schools and healthcare facilities.

---

## 🛠️ Tech Stack
- **Frontend / UI**: [Streamlit](https://streamlit.io/)
- **Data Visualizations**: [Plotly Express](https://plotly.com/python/) & [Matplotlib](https://matplotlib.org/)
- **Database**: [SQLite3](https://www.sqlite.org/index.html)
- **Data Engineering**: [Pandas](https://pandas.pydata.org/)
- **Language**: Python 3.9+

---

## 🚀 Quick Start Guide

### Prerequisites
Make sure you have Python installed on your system.

### 1. Clone or Download the Repository
Clone the repository to your local machine:
```bash
git clone https://github.com/your-username/aquaguard-ai.git
cd aquaguard-ai
