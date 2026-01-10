import json
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from utils.constants import RetrievalStrategy
from utils.prompt_loader import load_prompt

class RetrieverDecision(BaseModel):
    strategy: str = Field(description="The chosen retrieval strategy.")
    reasoning: str = Field(description="Explanation of why this strategy was chosen based on the query and retriever types.")
    refined_query: str = Field(description="A refined version of the query optimized for the chosen strategy.")

def get_retriever_decision(user_query, api_key, model_name="llama3-8b-8192"):
    """
    Analyzes the user query and decides the best retrieval strategy using an LLM.

    Input:
        user_query (str): The user's search query.
        api_key (str): Groq API Key.
        model_name (str): The Groq model to use.

    Output:
        dict: A dictionary containing:
            - strategy (str): 'Direct LLM', 'Vector-Based', or 'Hybrid'.
            - reasoning (str): Explanation for the choice.
            - refined_query (str): Optimized query.
    """
    # Default fallback
    fallback_decision = {
        "strategy": RetrievalStrategy.VECTOR_BASED.value,
        "reasoning": "Default fallback.",
        "refined_query": user_query
    }

    if not api_key:
        fallback_decision["reasoning"] = "No API key provided."
        return fallback_decision

    try:
        llm = ChatGroq(temperature=0, groq_api_key=api_key, model_name=model_name)
        
        parser = JsonOutputParser(pydantic_object=RetrieverDecision)
        
        # Dynamic Prompt using Enum values
        strategies_template = load_prompt("retriever_strategies.txt")
        strategies_text = strategies_template.format(
            direct_llm=RetrievalStrategy.DIRECT_LLM.value,
            vector_based=RetrievalStrategy.VECTOR_BASED.value,
            hybrid=RetrievalStrategy.HYBRID.value
        )
        
        router_system_template = load_prompt("retriever_router_system.txt")
        retriever_knowledge_base = load_prompt("retriever_knowledge_base.txt")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", router_system_template),
            ("user", "Query: {query}\n\n{format_instructions}")
        ])
        
        chain = prompt | llm | parser
        
        # Retry logic
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                decision = chain.invoke({
                    "strategies_text": strategies_text,
                    "knowledge_base": retriever_knowledge_base,
                    "vector_strategy": RetrievalStrategy.VECTOR_BASED.value,
                    "direct_strategy": RetrievalStrategy.DIRECT_LLM.value,
                    "query": user_query,
                    "format_instructions": parser.get_format_instructions()
                })
                # Validate strategy is known
                if decision.get("strategy") not in [s.value for s in RetrievalStrategy]:
                     decision["strategy"] = RetrievalStrategy.VECTOR_BASED.value # Default to safe option if hallucinated
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
