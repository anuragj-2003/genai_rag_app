import streamlit as st
import requests
from tavily import TavilyClient

def run_tavily_search(query: str, search_depth: str = "advanced", result_count: int = 7, sites: list = None):
    """
    Executes a web search using the Tavily API with retry logic.
    
    Input:
        query (str): Search term.
        search_depth (str): 'basic' or 'advanced'.
        result_count (int): Number of results to return.
        sites (list): Optional list of domains to restrict search to.
        
    Output:
        tuple: (Combined text content of results, List of result dictionaries)
    """
    api_key = st.session_state.get("TAVILY_API_KEY")
    if not api_key:
        return "Error: Tavily API key not set.", []
    

    # Retry logic
    max_retries = 3
    last_error = None
    
    for attempt in range(max_retries):
        try:
            client = TavilyClient(api_key=api_key)
            params = {"query": query, "search_depth": search_depth, "max_results": result_count}
            
            if sites:
                if sites[0]:
                    params["include_domains"] = sites
            
            response = client.search(**params)
            

            results_content = []
            results_list = response.get("results", [])
            
            for result in results_list:
                content = result["content"]
                results_content.append(content)
                
            combined_content = "\n\n".join(results_content)
            return combined_content, results_list
            
        except Exception as e:
            last_error = e
            # Continue to next attempt
            continue
            
    # If we failed all attempts
    return f"Error during Tavily search after {max_retries} attempts: {last_error}", []

def ask_groq(messages: list, model: str, temperature: float):
    """
    Sends a chat completion request to the Groq API with retry logic.
    
    Input:
        messages (list): List of message dicts (role, content).
        model (str): Groq model name.
        temperature (float): Sampling temperature.
        
    Output:
        str: The content of the assistant's response.
    """
    api_key = st.session_state.get("GROQ_API_KEY")
    if not api_key:
        return "Error: Groq API key not set."
        
    max_retries = 3
    last_error = None
    
    for attempt in range(max_retries):
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}", 
                "Content-Type": "application/json"
            }
            data = {
                "messages": messages, 
                "model": model, 
                "temperature": temperature
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            response_json = response.json()
            message_content = response_json["choices"][0]["message"]["content"]
            return message_content
            
        except Exception as e:
            last_error = e
            continue
            
    return f"Error querying Groq API after {max_retries} attempts: {last_error}"
