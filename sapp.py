# app.py
import streamlit as st
import os
from shooting_performance_analyzer import (
    ShootingDataManager,
    ShootingPerformanceAPI,
    PerformanceVisualizer,
)

# ======================================================================
# Initialize Data Manager and API
# ======================================================================

st.set_page_config(page_title="Pistol Shooting Analyzer", layout="wide")

data_manager = ShootingDataManager()
api_key = os.getenv("SHOOTING_FEEDBACK_API_KEY")  # use Streamlit secrets
api = ShootingPerformanceAPI(api_key=api_key)

# ======================================================================
# Sidebar Navigation
# ======================================================================

st.sidebar.title("Navigation")
menu = st.sidebar.radio(
    "Go to",
    ["Add Session", "View Statistics", "Generate Report", 
     "View Recommendations", "Practice Schedule", "Visualizations"]
)

# ======================================================================
# ADD NEW SESSION
# ======================================================================

if menu == "Add Session":
    st.header("Add New Shooting Session")
    
    num_series = st.number_input("Number of series in this session", min_value=1, max_value=10, value=1)
    session_series = []

    for i in range(num_series):
        st.subheader(f"Series {i+1}")
        col1, col2, col3, col4 = st.columns(4)
        seven = col1.number_input("7s or less", min_value=0, max_value=10, key=f"seven_{i}")
        eight = col2.number_input("8s", min_value=0, max_value=10, key=f"eight_{i}")
        nine = col3.number_input("9s", min_value=0, max_value=10, key=f"nine_{i}")
        ten = col4.number_input("10s", min_value=0, max_value=10, key=f"ten_{i}")
        
        if seven + eight + nine + ten != 10:
            st.warning(f"Series {i+1} total does not equal 10. Correct this before submission.")
        
        series_data = {"seven_or_less": seven, "eights": eight, "nines": nine, "tens": ten}
        session_series.append(series_data)

    if st.button("Add Session"):
        valid = all(sum(s.values()) == 10 for s in session_series)
        if valid:
            session = data_manager.add_session(series=session_series)
            analysis = api.analyze_session(session)
            st.success("Session added successfully!")
            st.subheader("Session Analysis")
            st.json(analysis)
        else:
            st.error("Each series must total 10 shots.")

# ======================================================================
# VIEW STATISTICS
# ======================================================================

elif menu == "View Statistics":
    st.header("Session Statistics")
    sessions = data_manager.get_all_sessions()
    if not sessions:
        st.warning("No sessions found. Add sessions first.")
    else:
        analyses = [api.analyze_session(s) for s in sessions]
        trend = api.get_trend_analysis(analyses)
        
        st.metric("Total Sessions", trend['total_sessions'])
        st.metric("Average Score", f"{trend['average_score']}/10")
        st.metric("Best Score", f"{trend['best_score']}/10")
        st.metric("Worst Score", f"{trend['worst_score']}/10")
        st.metric("Trend", trend['trend'])

# ======================================================================
# GENERATE REPORT
# ======================================================================

elif menu == "Generate Report":
    st.header("Performance Analysis Report")
    sessions = data_manager.get_all_sessions()
    if not sessions:
        st.warning("No sessions found.")
    else:
        analyses = [api.analyze_session(s) for s in sessions]
        for i, analysis in enumerate(analyses, 1):
            st.subheader(f"Session {i} ({analysis['date']})")
            st.write(f"Average Score: {analysis['average_score']}/10")
            st.write(f"Shot Distribution: 7s: {analysis['distribution']['7s_or_less']}, "
                     f"8s: {analysis['distribution']['8s']}, 9s: {analysis['distribution']['9s']}, "
                     f"10s: {analysis['distribution']['10s']}")
            st.write(f"Quality: {analysis['session_quality']}")
            if analysis['weak_areas']:
                st.write("Areas for Improvement:")
                for wa in analysis['weak_areas']:
                    st.write(f"- {wa}")

# ======================================================================
# VIEW RECOMMENDATIONS
# ======================================================================

elif menu == "View Recommendations":
    st.header("Personalized Recommendations")
    sessions = data_manager.get_all_sessions()
    if not sessions:
        st.warning("No sessions found.")
    else:
        analyses = [api.analyze_session(s) for s in sessions]
        recommendations = api.generate_recommendations(analyses)
        for i, rec in enumerate(recommendations, 1):
            st.write(f"{i}. [{rec['priority']}] Focus: {rec['focus']}, Action: {rec['action']}, Duration: {rec['duration']}")

# ======================================================================
# PRACTICE SCHEDULE
# ======================================================================

elif menu == "Practice Schedule":
    st.header("Generate Practice Schedule")
    sessions = data_manager.get_all_sessions()
    if not sessions:
        st.warning("No sessions found.")
    else:
        days = st.number_input("Number of days for schedule", min_value=1, max_value=14, value=7)
        analyses = [api.analyze_session(s) for s in sessions]
        recommendations = api.generate_recommendations(analyses)
        schedule_text = api.feedback_client.generate_schedule(recommendations, days) if getattr(api, 'feedback_client', None) else "Schedule generation requires FeedbackClient."
        st.text(schedule_text)

# ======================================================================
# VISUALIZATIONS
# ======================================================================

elif menu == "Visualizations":
    st.header("Performance Visualizations")
    sessions = data_manager.get_all_sessions()
    if not sessions:
        st.warning("No sessions found.")
    else:
        st.subheader("Score Trends Over Time")
        PerformanceVisualizer.plot_score_trends(sessions, save_path='score_trends.png')
        st.image('score_trends.png')

        st.subheader("Shot Distribution")
        PerformanceVisualizer.plot_shot_distribution(sessions, save_path='shot_distribution.png')
        st.image('shot_distribution.png')

        st.subheader("Session Totals")
        PerformanceVisualizer.plot_session_totals(sessions, save_path='session_totals.png')
        st.image('session_totals.png')

        st.subheader("Latest Session Pie Chart")
        PerformanceVisualizer.plot_performance_pie(sessions[-1], save_path='performance_pie.png')
        st.image('performance_pie.png')
