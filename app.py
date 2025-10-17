
from flask import Flask, request, jsonify, send_from_directory, render_template
import io, os
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader

try:
    import docx
    DOCX_AVAILABLE = True
except Exception:
    DOCX_AVAILABLE = False

app = Flask(__name__, static_folder='static', template_folder='templates')
ALLOWED_EXT = {'.pdf', '.txt', '.docx'}

def extract_text_from_pdf(file_stream):
    try:
        reader = PdfReader(io.BytesIO(file_stream.read()))
        texts = []
        for p in reader.pages:
            t = p.extract_text()
            if t:
                texts.append(t)
        return "\\n".join(texts)
    except Exception as e:
        return ""

def extract_text_from_docx(file_stream):
    if not DOCX_AVAILABLE:
        return ""
    try:
        doc = docx.Document(io.BytesIO(file_stream.read()))
        paragraphs = [p.text for p in doc.paragraphs if p.text]
        return "\\n".join(paragraphs)
    except Exception:
        return ""

def extract_text_from_txt(file_stream):
    try:
        return file_stream.read().decode('utf-8', errors='ignore')
    except Exception:
        return ""

import re
from collections import Counter

def simple_summarize(text, max_sentences=5):
    if not text or len(text.strip())<20:
        return "No readable text found in the uploaded document."
    sentences = re.split(r'(?<=[.!?])\s+', text.replace('\\n', ' '))
    words = re.findall(r'\\w+', text.lower())
    stopwords = set([
        'the','and','is','in','to','of','a','for','that','on','with','as','are','be','this','it','by','an','or','from','at','which','we','can','have','has'
    ])
    words = [w for w in words if w not in stopwords and len(w)>1]
    freq = Counter(words)
    if not freq:
        return "Couldn't extract meaningful words to summarize."
    sent_scores = []
    for i,s in enumerate(sentences):
        s_words = re.findall(r'\\w+', s.lower())
        score = sum(freq.get(w,0) for w in s_words)
        sent_scores.append( (i, score, s.strip()) )
    sent_scores.sort(key=lambda x: x[1], reverse=True)
    top = sorted(sent_scores[:max_sentences], key=lambda x: x[0])
    summary = ' '.join([s for (_,_,s) in top])
    return summary if summary else "Summary could not be generated."

def make_flashcards(text, max_cards=6):
    import re
    sentences = re.split(r'(?<=[.!?])\\s+', text.replace('\\n', ' '))
    candidates = [s.strip() for s in sentences if len(s.strip())>30]
    cards = []
    for s in candidates[:max_cards]:
        words = s.split()
        idx = len(words)//2
        answer = words[idx].strip('.,!?')
        question = ' '.join(words[:idx] + ['____'] + words[idx+1:])
        cards.append({'q': question, 'a': answer})
    if not cards:
        cards = [{'q':'What is the main idea?', 'a': simple_summarize(text, max_sentences=1)}]
    return cards

def quick_resolution(text):
    return simple_summarize(text, max_sentences=1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/summarize', methods=['POST'])
def summarize_route():
    mode = request.form.get('mode','summarizer')
    file = request.files.get('file')
    if not file:
        return jsonify({'error':'No file uploaded.'}), 400
    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXT:
        return jsonify({'error':'Unsupported file type.'}), 400
    file.stream.seek(0)
    text = ""
    if ext == '.pdf':
        text = extract_text_from_pdf(file.stream)
    elif ext == '.txt':
        text = extract_text_from_txt(file.stream)
    elif ext == '.docx':
        text = extract_text_from_docx(file.stream)
    if not text:
        return jsonify({'error':'Could not extract text from document.'}), 400
    if mode == 'summarizer':
        summary = simple_summarize(text, max_sentences=6)
        return jsonify({'summary': summary})
    elif mode == 'note_maker':
        summary = simple_summarize(text, max_sentences=8)
        bullets = [s.strip() for s in re.split(r'(?<=[.!?])\\s+', summary) if s.strip()]
        return jsonify({'notes': bullets})
    elif mode == 'question_predictor':
        cards = make_flashcards(text, max_cards=6)
        return jsonify({'cards': cards})
    elif mode == 'quick_resolution':
        thr = quick_resolution(text)
        return jsonify({'quick': thr})
    else:
        return jsonify({'error':'Unknown mode.'}), 400

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
