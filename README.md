# 🧠 AI Multi-Step News Fact Checker

An AI-powered news verification tool that determines whether a news claim is Real, Fake, or Unverified using multi-step reasoning and Google search headlines.

---

## 🚀 Overview

This project is a fully functional experimental fact-checking system built using:

- Google Search Open API (via RapidAPI)
- Mistral AI Large Language Model
- Multi-round AI reasoning
- Confidence scoring system
- Strict entity matching (names, titles, countries)

The system generates strategic search queries, analyzes headlines only, evaluates entity consistency, and accumulates confidence across multiple rounds before giving a final verdict.

---

## 💰 Cost

Total development cost: **0 USD**

All APIs used to run this tool are available with free tiers.

No paid infrastructure.  
No paid backend.  
No paid hosting required.  

This project can run entirely using free API plans.

---

## 🔗 APIs Used

### 🤖 Mistral AI
Official Website:
https://mistral.ai

API Documentation:
https://docs.mistral.ai

Used for:
- Query generation
- Headline evaluation
- Fact-check reasoning
- Confidence scoring

Free tier available.

---

### 🔎 Google Search Open API (RapidAPI)

RapidAPI Marketplace Page:
https://rapidapi.com/moham3iof/api/google-search-open

Used for:
- Fetching Google search headlines
- Returning article titles and URLs
- Multi-round evidence gathering

Free tier available on RapidAPI.

---

## 🏗 How It Works

1. User enters a news claim.
2. AI generates a precise search query.
3. Google Search API returns headlines and URLs.
4. AI evaluates whether the headlines:
   - Confirm the claim
   - Refute the claim
   - Are unrelated
5. Each round adds confidence points (up to 40 per round).
6. After multiple rounds (max 5), a final verdict is produced.

---

## 📊 Confidence Logic

- Each round can add up to 40 points.
- Maximum total confidence: 100%.
- Below 50% → Unverified / Not Enough Evidence.
- 100% → Strong evidence.

---

## 📦 Technologies Used

- Python 3
- requests
- python-dotenv
- RapidAPI
- Mistral AI API

Trusted domains prioritized in later search rounds:
- reuters.com
- apnews.com
- bbc.com
- aljazeera.com

---

## 🔑 Setup Instructions

### 1. Clone Repository

```bash
git clone https://github.com/mohamoha0000/AI-Fact-Checker.git
cd 'AI-Fact-Checker'
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

If requirements.txt is not available:

```bash
pip install requests python-dotenv
```

### 3. Create .env File

Create a file named `.env` in the root folder:

```
MISTRAL_API_KEY=your_mistral_api_key
RAPIDAPI_KEY=your_rapidapi_key
```

### 4. Run the Application

```bash
python main.py
```

Type a news claim and press Enter.  
Type `quit` to exit.

---

## 🧪 Example

Input:
```
Iran attacked Israel in 2026
```

Output:
```
Final Verdict: Fake (Confidence: 82%)
```

---

## ⚠ Limitations

- Only analyzes headlines (not full article content).
- Depends on search engine results.
- May not handle very recent breaking news.

---

## 🔮 Future Improvements

- Full article scraping
- Named Entity Recognition (NER)
- Semantic similarity analysis
- Web interface (Streamlit / Flask)
- Database logging system

---

## 🤝 Contributing

Contributions, improvements, and suggestions are welcome.

---

## 📜 License

MIT License

---

Built as a zero-cost AI fact-checking system using free API tiers.