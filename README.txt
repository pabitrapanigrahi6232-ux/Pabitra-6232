
AI Notes Summarizer - Prototype (Offline heuristic summarizer)
Files:
- app.py (Flask backend)
- templates/index.html (Frontend)
- static/styles.css, static/main.js (Frontend assets)
- requirements.txt

How to run locally:
1. (Optional) Create virtualenv: python -m venv venv && source venv/bin/activate
2. Install: pip install -r requirements.txt
3. Run: python app.py
4. Open browser at http://127.0.0.1:5000/

Notes:
- This prototype uses a simple frequency-based summarizer (no external LLM APIs) so it works offline.
- PDF and TXT uploads are supported. DOCX is supported if python-docx is installed and available.
- For hackathon demo, this is fast and reliable; to productionize, swap summarizer with OpenAI/HF models.
