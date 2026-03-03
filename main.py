"""
AI-Powered Automated Fact-Checking Agent
This script uses Mistral AI and a Google Search API to autonomously verify news claims.
It acts as an AI agent that generates its own search queries, analyzes search results,
and builds cumulative confidence to determine if a claim is Real or Fake.
"""

import requests
import json
import os
import re
from dotenv import load_dotenv
from datetime import date

# Load environment variables from the .env file (API keys)
load_dotenv()

# List of highly reliable news domains used to narrow down searches in later rounds
TRUSTED_DOMAINS = ["reuters.com", "apnews.com", "bbc.com", "aljazeera.com"]

def clean_json_response(text):
    """
    Cleans the markdown formatting (like ```json ... ```) often returned by LLMs
    to ensure the output can be safely parsed by Python's json.loads().
    """
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```', '', text)
    return text.strip()

def chat(text):
    """
    Wrapper function for the Mistral AI API.
    Sends a prompt to the 'mistral-large-latest' model and retrieves the response.
    """
    API_KEY = os.getenv("MISTRAL_API_KEY")
    if not API_KEY:
        return "Error: Mistral API key not found."

    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # We use a low temperature (0.2) to make the AI responses more analytical and deterministic
    data = {
        "model": "mistral-large-latest", 
        "max_tokens": 1500,
        "temperature": 0.2, 
        "messages": [
            {"role": "user", "content": text}
        ]
    }

    try:
        response = requests.post(url, timeout=30, headers=headers, json=data)
        response.raise_for_status() 
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {e}"

def get(q):
    """
    Fetches Google search results using the RapidAPI custom search endpoint.
    Retrieves up to 100 results per query.
    """
    url = "https://google-search-open.p.rapidapi.com/custm"
    querystring = {"q": q, "hl": "en-US", "n": "100"} 
    
    RAPID_KEY = os.getenv("RAPIDAPI_KEY")
    headers = {
        "x-rapidapi-key": RAPID_KEY,
        "x-rapidapi-host": "google-search-open.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=20)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def generate_next_query(topic, previous_queries, previous_findings):
    """
    Prompts the AI to act as a search strategist. 
    It reviews what has been searched and found so far, and generates the NEXT best 
    Google search query to fill in the missing evidence.
    """
    prompt = f"""
    We are trying to verify this exact news claim: "{topic}"
    Today's date is: {date.today()}.
    
    CRITICAL CONSTRAINT: Our search API ONLY returns article HEADLINES (Titles) and URLs. It does not return the full text or snippets.
    Therefore, you MUST generate a specific search query that forces search engines to return articles where the truth is explicitly stated in the TITLE itself.
    
    Strategies to use:
    - Use terms like "fact check", "debunked", "hoax", or "rumor" to find articles specifically addressing if it's fake.
    - Use terms like "official statement", "announces", or "confirmed" to find official news.
    - Focus strictly on exact names and roles.
     
    CRITICAL SEARCH RULES:
    1. DO NOT generate long sentences. Use a maximum of 4 to 6 broad keywords.
    2. DO NOT use multiple 'OR' statements. 
    3. Example of a BAD query: "NASA Perseverance rover cavern breathable atmosphere debunked OR hoax OR fake"
    4. Example of a GOOD query: "Perseverance rover Mars cavern fact check"

    Previous search queries we already tried: {previous_queries}
    What we found so far: {previous_findings}
    
    Based on what is missing, generate EXACTLY ONE short Google search query.
    Return ONLY a JSON object in this format:
    {{
        "next_query": "your precise search query here"
    }}
    """
    response = chat(prompt)
    try:
        cleaned = clean_json_response(response)
        start = cleaned.find('{')
        end = cleaned.rfind('}') + 1
        return json.loads(cleaned[start:end])["next_query"]
    except:
        # Fallback query in case the LLM fails to return valid JSON
        return f'"{topic}" fact check truth {date.today().year}'

def evaluate_step(topic, new_data, current_summary):
    """
    Prompts the AI to analyze a fresh batch of search results.
    It returns a structured JSON evaluation assessing whether the new data
    confirms, refutes, or is unrelated to the claim, and awards confidence points.
    """
    prompt = f"""
    You are a STRICT fact-checker. We are verifying: '{topic}'
    Today's date is: {date.today()}.

    CRITICAL RULE: Pay exact attention to ENTITIES (Names, Titles, Countries). 
    If the topic asks about the "President of Israel" and the search data talks about the "Supreme Leader of Iran", this DOES NOT confirm the topic. It is a contradiction.

    New Search Data to analyze:
    {json.dumps(new_data)[:10000]} 

    Analyze this specific batch of data. Does it prove the topic is Real, Fake, or does it lack evidence?
    Return ONLY a JSON object:
    {{
        "step_verdict": "Confirms" or "Refutes" or "Unrelated",
        "confidence_points": <number from 0 to 40. Give max 40 ONLY if the exact entities match perfectly and the source is highly reliable. Give 0 if unrelated or contradictory>,
        "step_reasoning": "<short summary of what THIS specific search revealed, mentioning exact names found>"
    }}
    """
    response = chat(prompt)
    try:
        cleaned = clean_json_response(response)
        start = cleaned.find('{')
        end = cleaned.rfind('}') + 1
        return json.loads(cleaned[start:end])
    except Exception as e:
        return {"step_verdict": "Error", "confidence_points": 0, "step_reasoning": "Failed to parse API response."}

# ==========================================
# --- Main Application Loop ---
# ==========================================

while True:
    # 1. Get the claim from the user
    topic = input("\nEnter the news topic to check (or type 'quit' to exit): ")
    
    if topic.lower() == 'quit':
        break
        
    print("\n🧠 Initializing verification process...")
    
    # Initialize state variables for the verification journey
    cumulative_confidence = 0
    previous_queries = []
    accumulated_findings = ""
    global_verdict = "Unverified"
    final_reasoning = ""
  
    # Maximum number of iterative searches the AI is allowed to perform
    max_searches = 5
    
    for i in range(max_searches):
        print(f"\n--- Round {i+1} ---")
        
        # 2. Let the AI decide what to search for next based on current knowledge
        print("🤔 AI is thinking of the next best search query...")
        current_query = generate_next_query(topic, previous_queries, accumulated_findings)
        
        # In later rounds, append trusted domains to force high-quality sources
        if i >= 2:
            domain = TRUSTED_DOMAINS[i % len(TRUSTED_DOMAINS)]
            current_query = f"{current_query}  OR site:{domain} "
        
        previous_queries.append(current_query)
        print(f"🔍 Searching: [{current_query}]")
       
        # 3. Fetch data from Google Search API
        data = get(current_query)
        
        if "error" in data:
            print("⚠️ Error fetching search results. Skipping round.")
            continue
            
        # 4. Data Optimization: Remove Image_URLs to save LLM context window tokens
        # This allows us to feed many more results to the AI without hitting limits.
        cleaned_results = [{k: v for k, v in item.items() if k != "Image_URL"} for item in data.get("results", [])]

        # 5. Evaluate the cleaned search results
        print("⚖️ Analyzing this specific search data...")
        evaluation = evaluate_step(topic, cleaned_results, accumulated_findings)
        
        # Extract verdict details
        step_verdict = evaluation.get("step_verdict", "Unrelated")
        points_earned = evaluation.get("confidence_points", 0)
        step_reasoning = evaluation.get("step_reasoning", "No clear reasoning provided.")
        
        print(f"📌 Step Result: {step_verdict} | Points Earned: +{points_earned}")
        print(f"📝 AI Notes: {step_reasoning}")
        
        # Log the findings for context in the next round
        accumulated_findings += f"\nRound {i+1}: {step_reasoning}"
        
        # 6. Update global confidence based on step results
        if step_verdict == "Confirms":
            global_verdict = "Real"
            cumulative_confidence += points_earned
        elif step_verdict == "Refutes":
            global_verdict = "Fake"
            cumulative_confidence += points_earned
            
        # 7. Check if we have enough confidence to stop early
        if cumulative_confidence >= 100:
            cumulative_confidence = 100
            final_reasoning = accumulated_findings
            print("\n✅ Cumulative confidence reached 100%! Stopping further searches.")
            break
        else:
            print(f"📊 Current Cumulative Confidence: {cumulative_confidence}%/100%. Need more evidence...")
            final_reasoning = accumulated_findings

    # ==========================================
    # --- Final Output Report ---
    # ==========================================
    print("\n================ FINAL ANALYSIS ================")
    print(f"📰 Topic: {topic}")
    
    # If the AI couldn't gather enough points, mark it as Unverified
    if cumulative_confidence < 50:
        global_verdict = "Unverified / Not Enough Evidence"
        
    print(f"🎯 Final Verdict: **{global_verdict}** (Total Confidence: {cumulative_confidence}%)")
    print("📝 Combined Reasoning Journey:")
    print(final_reasoning.strip())
    print("================================================\n")