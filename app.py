from flask import Flask, render_template, request, jsonify
with open("questions_pool.json", "r", encoding="utf-8") as f:
questions_pool = json.load(f)


# Helper: generate questions using OpenAI
def generate_questions_ai(ritual_text, n=5):
if not USE_OPENAI:
return generate_questions_local(n)


prompt = f"""
Create {n} multiple-choice questions (4 options each) based on the following ritual description:
"""
prompt += f"\n{ritual_text}\n\n"
prompt += (
"Return the output as JSON array with fields: question, options (array of 4), answer (exact text from options)."
)


try:
resp = openai.ChatCompletion.create(
model="gpt-5-mini",
messages=[{"role": "user", "content": prompt}],
temperature=0.7,
max_tokens=600,
)
raw = resp.choices[0].message.content.strip()
# Attempt to parse JSON from model output
questions = json.loads(raw)
# Basic validation
clean = []
for q in questions:
if all(k in q for k in ("question", "options", "answer")):
clean.append(q)
if clean:
return clean[:n]
except Exception:
pass


# fallback to local questions
return generate_questions_local(n)


# Helper: pick random questions from local pool
def generate_questions_local(n=5):
return random.sample(questions_pool, min(n, len(questions_pool)))


@app.route("/")
def index():
# Select today's ritual: rotate by day-of-year or random if you prefer
ritual = random.choice(rituals)["ritual"]
# Generate questions (AI if available, otherwise local)
questions = generate_questions_ai(ritual, n=5)
return render_template("index.html", ritual=ritual, questions=questions)


@app.route("/check", methods=["POST"])
def check():
data = request.get_json()
score = 0
answers = []
for q in data.get("questions", []):
selected = q.get("selected", "")
correct = q.get("answer", "")
answers.append({"selected": selected, "answer": correct})
if selected == correct:
score += 1
return jsonify({"score": score, "answers": answers})


if __name__ == "__main__":
app.run(debug=True)
