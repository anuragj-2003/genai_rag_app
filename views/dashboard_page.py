import streamlit as st
import pandas as pd
import altair as alt
from utils.database import get_dashboard_stats

def render_page():
    """Renders the main Dashboard page with persistent database statistics."""
    st.title("📊 Dashboard")
    st.caption("Usage Statistics & Analytics")
    
    user_email = st.session_state.get("user_email")
    if not user_email:
        st.warning("Please log in to view stats.")
        return

    # Fetch stats from DB
    stats = get_dashboard_stats(user_email)
    
    # Top Metrics
    with st.container(border=True):
        st.subheader("Overview")
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Conversations", stats.get("total_conversations", 0))
        m2.metric("Total Messages", stats.get("total_interactions", 0))
        
        # Calculate roughly avg messages per chat
        total_conv = stats.get("total_conversations", 0)
        total_msg = stats.get("total_interactions", 0)
        avg = round(total_msg / total_conv, 1) if total_conv > 0 else 0
        m3.metric("Avg. Messages / Chat", avg)

    st.markdown("") # Spacing

    # Charts Section
    c1, c2 = st.columns(2)
    
    with c1:
        with st.container(border=True):
            st.subheader("Recent Activity")
            activity_data = stats.get("activity_by_date", [])
            
            if activity_data:
                df_activity = pd.DataFrame(activity_data)
                # Ensure date format
                df_activity["day"] = pd.to_datetime(df_activity["day"]).dt.strftime('%Y-%m-%d')
                
                chart = alt.Chart(df_activity).mark_bar(cornerRadius=5).encode(
                    x=alt.X("day", title="Date", sort="-x"),
                    y=alt.Y("count", title="Interactions"),
                    color=alt.value("#ff4b4b"),
                    tooltip=["day", "count"]
                ).properties(height=300)
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("No activity recorded yet.")

    with c2:
        with st.container(border=True):
            st.subheader("Usage by Source")
            source_data = stats.get("source_distribution", [])
            
            if source_data:
                df_source = pd.DataFrame(source_data)
                # Clean up source names (remove model details if needed, but keeping for now)
                chart = alt.Chart(df_source).mark_arc(innerRadius=50).encode(
                    theta="count",
                    color=alt.Color("source", legend=alt.Legend(orient="bottom")),
                    tooltip=["source", "count"]
                ).properties(height=300)
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("No data available.")

    st.markdown("---")
    st.caption("Statistics are generated from your saved history.")
