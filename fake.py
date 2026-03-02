import requests
import json
import os
import re
from dotenv import load_dotenv
from datetime import date

# تحميل المفاتيح من ملف .env
load_dotenv()

TRUSTED_DOMAINS = ["reuters.com", "apnews.com", "bbc.com", "aljazeera.com"]

def clean_json_response(text):
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```', '', text)
    return text.strip()

def chat(text):
    API_KEY = os.getenv("MISTRAL_API_KEY")
    if not API_KEY:
        return "Error: Mistral API key not found."

    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
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
    url = "https://google-search-open.p.rapidapi.com/custm"
    querystring = {"q": q, "hl": "en-US", "n": "50"} 
    
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
    prompt = f"""
    We are trying to verify this exact news claim: "{topic}"
    Today's date is: {date.today()}.
    
    CRITICAL CONSTRAINT: Our search API ONLY returns article HEADLINES (Titles) and URLs. It does not return the full text or snippets.
    Therefore, you MUST generate a specific search query that forces search engines to return articles where the truth is explicitly stated in the TITLE itself.
    
    Strategies to use:
    - Use terms like "fact check", "debunked", "hoax", or "rumor" to find articles specifically addressing if it's fake.
    - Use terms like "official statement", "announces", or "confirmed" to find official news.
    - Focus strictly on exact names and roles.

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
 
        return f'"{topic}" fact check truth {date.today().year}'
def evaluate_step(topic, new_data, current_summary):
    prompt = f"""
    You are a STRICT fact-checker. We are verifying: '{topic}'
    Today's date is: {date.today()}.

    CRITICAL RULE: Pay exact attention to ENTITIES (Names, Titles, Countries). 
    If the topic asks about the "President of Israel" and the search data talks about the "Supreme Leader of Iran", this DOES NOT confirm the topic. It is a contradiction.

    New Search Data to analyze:
    {json.dumps(new_data)[:6000]} 

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

# --- Main Application Loop ---
while True:
    topic = input("\nEnter the news topic to check (or type 'quit' to exit): ")
    
    if topic.lower() == 'quit':
        break
        
    print("\n🧠 Initializing verification process...")
    
    cumulative_confidence = 0
    previous_queries = []
    accumulated_findings = ""
    global_verdict = "Unverified"
    final_reasoning = ""
  

    max_searches = 5
    
    for i in range(max_searches):
        print(f"\n--- Round {i+1} ---")
        

        print("🤔 AI is thinking of the next best search query...")
        current_query = generate_next_query(topic, previous_queries, accumulated_findings)
        
    
        if i >= 2:
            domain = TRUSTED_DOMAINS[i % len(TRUSTED_DOMAINS)]
            current_query = f"{current_query}  OR site:{domain} "
        
        previous_queries.append(current_query)
        print(f"🔍 Searching: [{current_query}]")
       
        data = get(current_query)
        
        if "error" in data:
            print("⚠️ Error fetching search results. Skipping round.")
            continue
            
    
        print("⚖️ Analyzing this specific search data...")
        evaluation = evaluate_step(topic, data, accumulated_findings)
        
        step_verdict = evaluation.get("step_verdict", "Unrelated")
        points_earned = evaluation.get("confidence_points", 0)
        step_reasoning = evaluation.get("step_reasoning", "No clear reasoning provided.")
        
        print(f"📌 Step Result: {step_verdict} | Points Earned: +{points_earned}")
        print(f"📝 AI Notes: {step_reasoning}")
        
     
        accumulated_findings += f"\nRound {i+1}: {step_reasoning}"
        
        if step_verdict == "Confirms":
            global_verdict = "Real"
            cumulative_confidence += points_earned
        elif step_verdict == "Refutes":
            global_verdict = "Fake"
            cumulative_confidence += points_earned
        else:
            pass
            
        
        if cumulative_confidence >= 100:
            cumulative_confidence = 100
            final_reasoning = accumulated_findings
            print("\n✅ Cumulative confidence reached 100%! Stopping further searches.")
            break
        else:
            print(f"📊 Current Cumulative Confidence: {cumulative_confidence}%/100%. Need more evidence...")
            final_reasoning = accumulated_findings

    print("\n================ FINAL ANALYSIS ================")
    print(f"📰 Topic: {topic}")
    
   
    if cumulative_confidence < 50:
        global_verdict = "Unverified / Not Enough Evidence"
        
    print(f"🎯 Final Verdict: **{global_verdict}** (Total Confidence: {cumulative_confidence}%)")
    print("📝 Combined Reasoning Journey:")
    print(final_reasoning.strip())
    print("================================================\n")