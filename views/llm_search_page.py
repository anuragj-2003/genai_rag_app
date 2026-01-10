import streamlit as st
import json
import os
from utils.api_clients import run_tavily_search, ask_groq
from utils.logging_utils import log_search, log_llm_call
from utils.text_utils import count_tokens
from utils.database import log_interaction, find_similar_interaction, update_interaction_rating
from utils.prompt_loader import load_prompt
from utils.document_processor import process_uploaded_file
from utils.vector_store_manager import VectorStoreManager
from utils.retriever_agent import get_retriever_decision

from utils.constants import RetrievalStrategy

# Initialize Vector Store Manager in Session State
if "vector_store_manager" not in st.session_state:
    st.session_state.vector_store_manager = VectorStoreManager()

# Helper to Handle Auto-Run from Dashboard
def check_pending_query():
    if "pending_query" in st.session_state and st.session_state.pending_query:
        q = st.session_state.pending_query
        st.session_state.pending_query = None
        return q
    return None

def render_page():
    """
    Renders the RAG Agent page.
    Handled file uploads, auto-processing, chat interface, and intelligent agent routing.
    """
    st.title("RAG Agent")
    st.caption("Upload documents or ask general questions. The Agent will route your query.")

    #  File Uploader Section 
    with st.expander("Upload Documents", expanded=False):
        uploaded_files = st.file_uploader(
            "Upload files", 
            type=["pdf", "docx", "xlsx", "xls", "txt"], 
            accept_multiple_files=True
        )
        
        # Auto-Processing Logic
        if "processed_files" not in st.session_state:
            st.session_state.processed_files = set()
            
        if uploaded_files:
            new_files = []
            for f in uploaded_files:
                if f.name not in st.session_state.processed_files:
                    new_files.append(f)
            
            if new_files:
                with st.spinner(f"Auto-processing {len(new_files)} new file(s)..."):
                    try:
                        all_docs = []
                        for uploaded_file in new_files:
                            docs = process_uploaded_file(uploaded_file)
                            all_docs.extend(docs)
                            # Mark as processed
                            st.session_state.processed_files.add(uploaded_file.name)
                        
                        if all_docs:
                            st.session_state.vector_store_manager.add_documents(all_docs)
                            st.success(f"Successfully indexed {len(all_docs)} chunks from new files!")
                        else:
                            st.warning("No text found in uploaded files.")
                            
                    except Exception as e:
                        st.error(f"Error processing files: {e}")

    # Display chat history
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            if "source" in msg: st.caption(msg["source"])
            st.markdown(msg["content"])

            # Feedback
            if msg["role"] == "assistant" and "interaction_id" in msg:
                feedback_key_base = f"feedback_{msg['interaction_id']}"
                col1, col2, _ = st.columns([1, 1, 10])
                with col1:
                    if st.button("👍", key=f"{feedback_key_base}_up"):
                        update_interaction_rating(msg["interaction_id"], 1)
                        st.toast("Thanks!")
                with col2:
                    if st.button("👎", key=f"{feedback_key_base}_down"):
                        update_interaction_rating(msg["interaction_id"], -1)

    # Logic to handle both User Input AND Pending Query
    pending_q = check_pending_query()
    user_prompt = st.chat_input("Ask about your documents or anything else...")
    
    # If we have a pending query, override user_prompt (simulated)
    if pending_q:
        user_prompt = pending_q

    if user_prompt:
        st.session_state.chat_messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        with st.chat_message("assistant"):
            # 0. Check Semantic Memory
            cached_response = st.session_state.vector_store_manager.check_memory(user_prompt)
            if cached_response:
                st.success("⚡ Accessed from Memory")
                st.markdown(cached_response)
                st.session_state.chat_messages.append({
                    "role": "assistant", 
                    "content": cached_response,
                    "source": "Memory Cache"
                })
                # We can skip logging stats for memory hits or log them differently if desired
                # For now, we rerun to update UI
                st.session_state.completed_interaction = True # Flag to avoid re-run loops if needed, but rerun is simple
            else:
                # 1. Intelligent Agent Decision
                with st.spinner("Intelligent Agent is analyzing query..."):
                    agent_decision = get_retriever_decision(
                        user_prompt, 
                        st.session_state.get("GROQ_API_KEY"),
                        st.session_state.settings.get("groq_model", "llama3-8b-8192")
                    )
                
                # Display Agent's Thought Process
                with st.expander("Agent Reasoning & Strategy", expanded=True):
                    st.write(f"**Strategy:** {agent_decision['strategy']}")
                    st.write(f"**Reasoning:** {agent_decision['reasoning']}")
                    st.write(f"**Refined Query:** {agent_decision['refined_query']}")

                # 2. Retrieval Execution
                context_text = ""
                sources = []
                
                # Use Constants for Strategy Logic
                is_retrieval_needed = agent_decision['strategy'] in [RetrievalStrategy.VECTOR_BASED.value, RetrievalStrategy.HYBRID.value]
                
                if is_retrieval_needed and st.session_state.vector_store_manager.vector_store is not None:
                    with st.spinner("Searching Vector Database..."):
                        docs = st.session_state.vector_store_manager.similarity_search(agent_decision['refined_query'], k=4)
                        if docs:
                            context_text += "\n\n**Retrieved Documents:**\n"
                            for doc in docs:
                                # Use file name as source identifier
                                src_name = doc.metadata.get('source', 'Unknown Doc')
                                page_num = doc.metadata.get('page', 'Unknown')
                                context_text += f"--Source: {src_name} (Page {page_num})--\n{doc.page_content}\n"
                                sources.append(doc)
                
                # 3. Generate Answer
                if agent_decision['strategy'] == RetrievalStrategy.DIRECT_LLM.value:
                     system_prompt = load_prompt("direct_llm_system.txt")
                else:
                    rag_template = load_prompt("rag_response_system.txt")
                    system_prompt = rag_template.format(context_text=context_text)
                
                messages = [{"role": "system", "content": system_prompt}] + [
                    {"role": m["role"], "content": m["content"]} for m in st.session_state.chat_messages if m["role"] != "system"
                ]

                provider = "Groq (Web-based)"
                model = st.session_state.settings.get("groq_model", "llama-3.3-70b-versatile")
                
                with st.spinner("Generating answer..."):
                    response_text = ask_groq(messages, model, st.session_state.settings.get("temperature", 0.5))
                    st.markdown(response_text)

                # 4. Log Interaction
                interaction_id = log_interaction(
                    user_prompt=user_prompt,
                    web_context=context_text,
                    llm_response=response_text,
                    source=f"Groq ({model}) - {agent_decision['strategy']}",
                    sources=[s.metadata if hasattr(s, 'metadata') else s for s in sources]
                )
                
                # 5. Save to Memory
                st.session_state.vector_store_manager.add_to_memory(user_prompt, response_text)

                st.session_state.chat_messages.append({
                    "role": "assistant", 
                    "content": response_text,
                    "source": f"Groq ({model})", 
                    "sources": sources,
                    "retrieval_strategy": agent_decision['strategy'],
                    "interaction_id": interaction_id
                })
                
                # Stats
                log_llm_call(provider, model, count_tokens(str(messages)), count_tokens(response_text))
            
            st.rerun()
