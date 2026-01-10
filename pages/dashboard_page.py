import streamlit as st
import pandas as pd
import altair as alt


def render_page():
    """
    Renders the main Dashboard page.
    Displays hero section, system status, feature cards, and analytics tabs.
    """
    #  Top Bar: Title & Compact Status 
    c1, c2 = st.columns([2, 1])
    with c1:
        st.title("GenAI Workspace")
        st.caption("Intelligent Document & Web Retrieval")
        
    with c2:
        # Compact Status Card at Top Right
        with st.container(border=True):
            st.caption("**System Status**")
            sc1, sc2 = st.columns(2)
            sc1.markdown("🟢 **VectorDB**: Active")
            sc2.markdown(f"🤖 **Model**: {st.session_state.settings.get('groq_model', 'llama-3.3-70b')}")

    st.markdown("")

    #  Feature Cards 
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        with st.container(border=True):
            st.markdown("**🧠 Intelligent Routing**")
            st.caption("Auto-detects Intent")
    with col_f2:
        with st.container(border=True):
            st.markdown("**📄 Auto-RAG**")
            st.caption("PDF/Doc/Excel Processing")
    with col_f3:
        with st.container(border=True):
            st.markdown("**🌐 Live Web Search**")
            st.caption("Tavily Integration")
    
    st.markdown("") # Spacing

    #  Analytics Cards (Tabs) 
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "📈 Analytics", "🕒 Activity"])
    
    with tab1:
        with st.container(border=True):
            st.subheader("Session Overview")
            # Key Metrics
            m1, m2, m3, m4 = st.columns(4)
            m1.metric(label="Total Searches", value=st.session_state.search_count, delta="Session")
            m2.metric(label="LLM Calls", value=st.session_state.llm_call_count)
            m3.metric(label="Sources Scraped", value=st.session_state.pages_scraped_count)
            m4.metric(label="Tokens Used", value=f"{st.session_state.token_count:,}")
        
    with tab2:
        #  Efficiency Metrics (New) 
        with st.container(border=True):
            st.subheader("🚀 Efficiency Metrics")
            e1, e2, e3 = st.columns(3)
            
            # Derived Metrics
            total_calls = st.session_state.llm_call_count
            total_tokens = st.session_state.token_count
            avg_tokens = int(total_tokens / total_calls) if total_calls > 0 else 0
            
            total_searches = st.session_state.search_count
            total_pages = st.session_state.pages_scraped_count
            avg_pages = round(total_pages / total_searches, 1) if total_searches > 0 else 0.0

            e1.metric(label="Avg. Tokens / Call", value=avg_tokens, help="Average complexity of LLM interactions")
            e2.metric(label="Avg. Sources / Search", value=avg_pages, help="Average depth of web research")
            e3.metric(label="Est. Cost Savings", value=f"${(total_tokens/1000)*0.03:.2f}", help="Estimated savings compared to GPT-4 ($0.03/1k tokens)")

        st.write("") # Spacing

        #  Charts 
        c_chart1, c_chart2 = st.columns(2)
        with c_chart1:
            with st.container(border=True):
                st.markdown("**Provider Usage**")
                
                # Sanitize Data
                raw_data = st.session_state.llm_provider_usage
                # Filter out legacy/local keys
                clean_data = {k: v for k, v in raw_data.items() if "Ollama" not in k}
                
                if sum(clean_data.values()) > 0:
                    df = pd.DataFrame(list(clean_data.items()), columns=['Provider', 'Count'])
                    st.altair_chart(alt.Chart(df).mark_bar(cornerRadius=5, color='#02ab21').encode(
                        x=alt.X('Provider', axis=alt.Axis(labelAngle=0)), 
                        y='Count',
                        tooltip=['Provider', 'Count']
                    ), use_container_width=True)
                else:
                    st.info("No LLM calls yet.")
                    
        with c_chart2:
            with st.container(border=True):
                st.markdown("**Search Types**")
                if st.session_state.query_history:
                    df = pd.DataFrame([q['Type'] for q in st.session_state.query_history], columns=['Type']).value_counts().reset_index(name='Count')
                    st.altair_chart(alt.Chart(df).mark_arc(innerRadius=60).encode(
                        theta="Count", 
                        color=alt.Color("Type", scale=alt.Scale(scheme='accent')),
                        tooltip=['Type', 'Count']
                    ), use_container_width=True)
                else:
                    st.info("No data yet.")

    with tab3:
        with st.container(border=True):
            st.subheader("Recent Activity")
            if st.session_state.query_history:
                st.caption("Click 'Reload' to run again.")
                
                # Header
                h1, h2, h3 = st.columns([3, 1, 1])
                h1.markdown("**Query**")
                h2.markdown("**Type**")
                h3.markdown("**Action**")
                st.markdown("---")
                
                for i, item in enumerate(st.session_state.query_history):
                    c1, c2, c3 = st.columns([3, 1, 1])
                    c1.write(item["Query"])
                    c2.caption(item["Type"])
                    
                    target_page = "Custom Search" if item["Type"] == "Custom Search" else "RAG Agent"
                    
                    if c3.button("🔄 Reload", key=f"hist_btn_{i}"):
                        st.session_state.max_nav_page = target_page
                        st.session_state.pending_query = item["Query"]
                        st.session_state.switch_page = target_page
                        st.rerun()
                    
                    st.markdown("---")
            else:
                st.info("No recent activity.")
