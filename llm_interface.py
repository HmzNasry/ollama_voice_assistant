import asyncio
import json
import re
import requests
import ollama
from typing import Dict, List, Optional, Any
from llm_axe import Agent, OnlineAgent, OllamaChat

from config import LLM_MODEL, CONVERSATION_CONTEXT, CITY, COUNTRY, DATE_STR

class LLMInterface:
    def __init__(self, conversation_manager):
        """Initialize LLM interface with conversation context."""
        self.conversation_manager = conversation_manager
        self.ollama_model = LLM_MODEL
        self.system_prompt = CONVERSATION_CONTEXT
        
        # Initialize LLM client
        self.llm = OllamaChat(model=self.ollama_model)
        
    async def ask_llm(self, query: str) -> str:
        """Send a query to the appropriate LLM and get response."""
        print(f"[LLM] Processing query: {query}")
        
        # Get plan for internet usage
        plan_data = await self._get_internet_plan(query)
        
        # Choose method based on plan
        if plan_data.get("internet") == "yes" and plan_data.get("search_query"):
            print(f"[LLM] Using model with internet context")
            response = await self._get_internet_enhanced_response(query, plan_data["search_query"])
        else:
            print(f"[LLM] Using local Ollama model")
            response = await self._get_offline_response(query)
            
        return response
    
    async def _get_internet_plan(self, query: str) -> Dict[str, str]:
        """Determine if a query requires internet access and generate search query."""
        try:
            # CUSTOMIZE: Planning agent prompt - controls when internet search is triggered
            planning_prompt = f"""
            You have one job: decide if the user query requires an internet search for an LLM like yourself.
            Your response MUST be a valid JSON object with exactly two keys: "internet" and "search_query". 
            - "internet" must be either "yes" or "no".
            - "search_query" must be a string: if internet is "yes", provide an optimized search query; if "no", use an empty string.
            Do NOT include any extra text, explanations, markdown, or symbols.
            Respond exactly with the JSON object only.
            if you need the time in location, it is {CITY}, {COUNTRY}, {DATE_STR}
            Example: {{{{ "internet": "yes", "search_query": "current weather in Seattle" }}}}
            
            You are just a plan agent, the responses in the history are not from you and you don't have anything to do with them.
            Your job is only to analyze and decide if an internet search is needed.
            If your response does not follow the format of the example, you will break the system.
            """
            
            # Create plan agent
            plan_agent = Agent(self.llm, custom_system_prompt=planning_prompt)
            
            # Get recent conversation history
            history = self.conversation_manager.get_recent_history()
            
            # Ask the plan agent
            json_regex = r'^\s*\{\s*"internet"\s*:\s*"(yes|no)"\s*,\s*"search_query"\s*:\s*".*"\s*\}\s*$'
            loop = asyncio.get_event_loop()
            plan_response = await loop.run_in_executor(
                None,
                plan_agent.ask,
                f"USER QUERY: {query}, HISTORY: {history}"
            )
            
            print(f"[Plan Agent] Response: {repr(plan_response)}")
            
            # Parse the response
            if not re.match(json_regex, plan_response.strip()):
                m = re.search(r'\{.*\}', plan_response, re.DOTALL)
                if m:
                    try:
                        plan_data = json.loads(m.group(0))
                    except json.JSONDecodeError:
                        print("[LLM] Extracted JSON block invalid. Fallback to direct search.")
                        plan_data = {"internet": "yes", "search_query": query}
                else:
                    print("[LLM] Plan agent did not return valid JSON. Fallback to direct search.")
                    plan_data = {"internet": "yes", "search_query": query}
            else:
                try:
                    plan_data = json.loads(plan_response)
                except json.JSONDecodeError:
                    print("[LLM] JSON Parsing Failed. Fallback to direct search.")
                    plan_data = {"internet": "yes", "search_query": query}
                    
            return plan_data
        
        except Exception as e:
            print(f"[LLM] Error determining internet plan: {e}")
            return {"internet": "no", "search_query": ""}
    
    async def _get_internet_enhanced_response(self, query: str, search_query: str) -> str:
        """Get a response with internet data enhancement."""
        try:
            method = None
            summary = None
            url = None
            loop = asyncio.get_event_loop()
            
            # CUSTOMIZE: Search service URL
            # This requires running SearXNG search service on this port
            search_url = f"http://localhost:8080/search?q={search_query}&format=json"
            
            # Get search results from local search service
            print(f"[LLM] Fetching real-time data for: {search_query}")
            
            try:
                search_response = await loop.run_in_executor(None, requests.get, search_url)
                
                if search_response.status_code == 200:
                    raw_text = search_response.text.strip()
                    
                    if raw_text in ['"query"', 'query']:
                        search_results = {}
                    else:
                        try:
                            search_results = json.loads(raw_text)
                            if isinstance(search_results, str):
                                search_results = {}
                        except Exception:
                            search_results = {}
                    
                    # Process search results
                    if "answers" in search_results and search_results["answers"]:
                        summary = search_results["answers"][0]
                        method = "answers"
                        print(f"[LLM] Answer Found: {summary}")
                    elif ("results" in search_results and 
                        isinstance(search_results["results"], list) and 
                        len(search_results["results"]) > 0):
                        first_result = search_results["results"][0]
                        if isinstance(first_result, dict) and "url" in first_result:
                            url = first_result["url"]
                            method = "onlineagent"
                            print(f"[LLM] Using URL from results: {url}")
                        else:
                            print("[LLM] Search result does not contain a valid URL.")
                    else:
                        print("[LLM] No usable search results found.")
            except Exception as e:
                print(f"[LLM] Error fetching search results: {e}")
            
            # Process based on method
            if method == "answers":
                # Add summary to prompt
                enhanced_prompt = self.system_prompt + f" Additional internet data: {summary}"
                
                # Format conversation for the chat API
                history = self.conversation_manager.get_recent_history()
                messages = [{"role": "system", "content": enhanced_prompt}]
                
                # Add previous conversation turns
                for i in range(len(history["user"])):
                    messages.append({"role": "user", "content": history["user"][i]})
                    if i < len(history["assistant"]):
                        messages.append({"role": "assistant", "content": history["assistant"][i]})
                
                # Add current query
                messages.append({"role": "user", "content": query})
                
                # CUSTOMIZE: Model parameters for internet-enhanced responses
                response = await loop.run_in_executor(
                    None, 
                    lambda: ollama.chat(
                        model=self.ollama_model,
                        messages=messages
                    )
                )
                
                return response["message"]["content"].strip()
                
            elif method == "onlineagent":
                # Use OnlineAgent to extract info from the URL
                searcher = OnlineAgent(self.llm)
                history = self.conversation_manager.get_recent_history()
                
                online_answer = await loop.run_in_executor(
                    None, 
                    searcher.search,
                    f"{self.system_prompt}, extract info from this website: {url} to answer the user's question, {query}"
                )
                
                # Clean up the response
                cleaned_answer = online_answer.replace('Based to the information from the internet,', '')
                return cleaned_answer
                
            else:
                # Fall back to offline response if no internet data found
                return await self._get_offline_response(query)
                
        except Exception as e:
            print(f"[LLM] Error getting internet-enhanced response: {e}")
            return "Sorry, I'm having trouble retrieving information from the internet right now."
    
    async def _get_offline_response(self, query: str) -> str:
        """Get response from local Ollama model."""
        try:
            # Get recent conversation history
            history = self.conversation_manager.get_recent_history()
            
            # Format conversation for the chat API
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add previous conversation turns
            for i in range(len(history["user"])):
                messages.append({"role": "user", "content": history["user"][i]})
                if i < len(history["assistant"]):
                    messages.append({"role": "assistant", "content": history["assistant"][i]})
            
            # Add current query
            messages.append({"role": "user", "content": query})
            
            # CUSTOMIZE: Model parameters for regular responses
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: ollama.chat(
                    model=self.ollama_model,
                    messages=messages
                )
            )
            
            # Extract the response text
            return response['message']['content']
            
        except Exception as e:
            print(f"[LLM] Error getting offline response: {e}")
            return "I'm having trouble processing your request right now."
    
    def update_conversation(self, user_input: str, assistant_response: str) -> None:
        """Update conversation history with the latest exchange."""
        self.conversation_manager.update_conversation(user_input, assistant_response)