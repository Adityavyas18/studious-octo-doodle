from flask import Flask, request, jsonify
import re
import spacy
import subprocess

app = Flask(__name__)

# Load SpaCy model (with auto-download if missing)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")


def extract_any_category(text):
    # grab first number
    numbers = re.findall(r"\d+(?:\.\d+)?", text)
    amount = float(numbers[0]) if numbers else None

    doc = nlp(text.lower())

    # try to get the noun phrase following the word "for"
    cat = None
    for token in doc:
        if token.text == "for" and token.i < len(doc)-1:
            phrase = []
            for t in doc[token.i+1:]:
                if t.is_punct:
                    break
                phrase.append(t.text)
            if phrase:
                cat = " ".join(phrase)
                break

    # fallback: if no explicit "for", take the most significant noun chunk
    if not cat:
        noun_chunks = [chunk.text for chunk in doc.noun_chunks if chunk.text.strip()]
        if noun_chunks:
            cat = max(noun_chunks, key=len)

    return cat, amount


@app.route('/extract', methods=['POST'])
def extract():
    data = request.json
    texts = data.get("texts")
    if not texts or not isinstance(texts, list):
        return jsonify({"error": "Please provide a list of texts"}), 400

    results = {}
    for s in texts:
        cat, amt = extract_any_category(s)
        if cat is None:
            cat = s  # fallback
        if amt is None or amt == 0:
            continue  # skip this line if amount is 0
        results[cat] = results.get(cat, 0) + amt

    return jsonify(results)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
