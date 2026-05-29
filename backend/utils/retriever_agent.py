import json
from llama_index.llms.groq import Groq
from llama_index.core.llms import ChatMessage, MessageRole
from pydantic import BaseModel, Field
from utils.constants import RetrievalStrategy
from utils.prompt_loader import load_prompt

class RetrieverDecision(BaseModel):
    strategy: str = Field(description="The chosen retrieval strategy.")
    reasoning: str = Field(description="Explanation of why this strategy was chosen based on the query and retriever types.")
    refined_query: str = Field(description="A refined version of the query optimized for the chosen strategy.")
    context_source: str = Field(description="The primary source of context for this query: 'document', 'chat_history', or 'general_knowledge'.")
    confidence_score: int = Field(description="A score from 1-10 indicating confidence in the chosen context source.")
    clarification_needed: bool = Field(description="True if the user's intent is ambiguous (e.g., 'update code' when multiple codes exist in different contexts).")

def get_retriever_decision(user_query, api_key, model_name="llama-3.3-70b-versatile", system_prompt=None):
    """
    Analyzes the user query and decides the best retrieval strategy using an LLM.
    
    Args:
        user_query (str): The user's message.
        api_key (str): Groq API Key.
        model_name (str): LLM Model to use.
        system_prompt (str): Optional custom behavior.

    Returns:
        dict: Decision with keys 'strategy', 'confidence_score', 'reasoning', 'refined_query', 'context_source'.
    """
    if system_prompt:
        base_instruction = f"SYSTEM BEHAVIOR: {system_prompt}\n\n"
    else:
        base_instruction = ""

    # Default fallback
    fallback_decision = {
        "strategy": RetrievalStrategy.VECTOR.value,
        "reasoning": "Default fallback.",
        "refined_query": user_query,
        "context_source": "general_knowledge",
        "confidence_score": 5,
        "clarification_needed": False
    }

    # Regex Check for URLs
    import re
    # Pattern to find URLs
    url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
    urls = re.findall(url_pattern, user_query)
    
    if urls:
        return {
            "strategy": RetrievalStrategy.WEB_SEARCH.value,
            "reasoning": f"User query contains specific URLs: {urls}. Switching to Web Search.",
            "refined_query": user_query,
            "urls": urls # Pass extracted URLs
        }

    if not api_key:
        fallback_decision["reasoning"] = "No API key provided."
        return fallback_decision

    try:
        llm = Groq(model=model_name, api_key=api_key, temperature=0.0)
        
        # Dynamic Prompt using Enum values
        strategies_template = load_prompt("retriever_strategies.txt")
        strategies_text = strategies_template.format(
            direct_llm=RetrievalStrategy.DIRECT_LLM.value,
            vector_based=RetrievalStrategy.VECTOR.value,
            hybrid=RetrievalStrategy.HYBRID.value,
            web_search=RetrievalStrategy.WEB_SEARCH.value
        )
        
        router_system_template = load_prompt("retriever_router_system.txt")
        retriever_knowledge_base = load_prompt("retriever_knowledge_base.txt")
        
        system_content = f"{base_instruction}{router_system_template.format(strategies_text=strategies_text, knowledge_base=retriever_knowledge_base, vector_strategy=RetrievalStrategy.VECTOR.value, direct_strategy=RetrievalStrategy.DIRECT_LLM.value, web_strategy=RetrievalStrategy.WEB_SEARCH.value)}"
        
        format_instructions = (
            "Format your output as a valid JSON object matching the following Pydantic schema:\n"
            "{\n"
            '  "strategy": "string",  # The chosen retrieval strategy\n'
            '  "reasoning": "string", # Explanation of why this strategy was chosen\n'
            '  "refined_query": "string", # A refined version of the query\n'
            '  "context_source": "string", # "document", "chat_history", or "general_knowledge"\n'
            '  "confidence_score": 1-10,  # Confidence score\n'
            '  "clarification_needed": boolean # True if user intent is ambiguous\n'
            "}\n"
            "Ensure the response is ONLY a JSON block, nothing else."
        )

        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=system_content),
            ChatMessage(role=MessageRole.USER, content=f"Query: {user_query}\n\n{format_instructions}")
        ]
        
        # Retry logic
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = llm.chat(messages)
                content = response.message.content
                
                # Extract JSON if markdown wrapped
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                
                decision = json.loads(content.strip())
                
                # Validate strategy is known
                if decision.get("strategy") not in [s.value for s in RetrievalStrategy]:
                     decision["strategy"] = RetrievalStrategy.VECTOR.value
                return decision
            except Exception as e:
                last_error = e
                continue
        
        # Fallback if retries fail
        fallback_decision["strategy"] = RetrievalStrategy.DIRECT_LLM.value
        fallback_decision["reasoning"] = f"Agent decision failed after {max_retries} attempts: {str(last_error)}"
        return fallback_decision

    except Exception as e:
        # Outer catch
        fallback_decision["strategy"] = RetrievalStrategy.DIRECT_LLM.value
        fallback_decision["reasoning"] = f"Agent initialization failed: {str(e)}"
        return fallback_decision
