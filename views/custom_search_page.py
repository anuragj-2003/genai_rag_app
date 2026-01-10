import streamlit as st
from utils.api_clients import run_tavily_search
from utils.logging_utils import log_search

def render_page():
    """
    Renders the Custom Search page.
    Allows users to perform specific Tavily searches with adjustable depth and domain filtering.
    """
    st.title("Custom Search")
    st.caption("Direct web search with optional domain filtering.")

    # Check for pending query from Dashboard
    default_query = ""
    if "pending_query" in st.session_state and st.session_state.pending_query:
        default_query = st.session_state.pending_query
        # Clear it so it doesn't persist forever
        st.session_state.pending_query = None

    with st.form("search_form"):
        query = st.text_input("Enter your search query", value=default_query, placeholder="e.g., 'Latest trends in AI'")
        domain = st.text_input("Optional: Limit to a website", placeholder="e.g., 'langchain.com'")

        col1, col2 = st.columns(2)
        with col1:
            depth = st.selectbox("Search Depth (1-2: Basic, 3-5: Adv)", options=[1, 2, 3, 4, 5], index=st.session_state.settings.get("tavily_depth", 5) - 1)
        with col2:
            result_count = st.selectbox("Number of Results", options=list(range(1, 11)), index=6)
            
        if st.form_submit_button("Search", width="stretch"):
            if query:
                depth_str = "advanced" if depth >= 3 else "basic"
                with st.spinner(f"Searching for '{query}'..."):
                    context, results = run_tavily_search(query, search_depth=depth_str, result_count=result_count, sites=[domain] if domain else None)
                    # Note: We still log the search for dashboard stats
                    log_search(query, "Custom Search", len(results))

                if "Error" in context:
                    st.error(context)
                elif not results:
                    st.warning("No results found.")
                else:
                    st.success(f"Found {len(results)} results.")
                    
                    # --- MODIFIED: Use expanders instead of tabs ---
                    st.subheader("Search Results")
                    for r in results:
                        with st.expander(f"**{r['title']}**"):
                            st.markdown(f"**URL:** [{r['url']}]({r['url']})")
                            st.divider()
                            st.write(r['content'])
