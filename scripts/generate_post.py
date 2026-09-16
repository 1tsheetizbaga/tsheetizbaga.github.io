import os
import json
from google import genai

# -----------------------------
# Configuration
# -----------------------------

API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set.")

client = genai.Client(api_key=API_KEY)

MODEL = "gemini-3.8-flash"

# -----------------------------
# Topic
# -----------------------------

TOPIC = "Best AI Video Generators for YouTube Creators"

# -----------------------------
# Prompt
# -----------------------------

prompt = f"""
You are an expert technology writer.

Write a useful, accurate and original article about:

{TOPIC}

The target audience is YouTube creators and digital content creators.

The article should:

- Have a clear and interesting title
- Start with a useful introduction
- Use logical H2 sections
- Explain important concepts clearly
- Avoid unnecessary filler
- Avoid making unsupported claims
- Give practical information
- Have a concise conclusion
- Be written in natural English
- Do not mention that AI wrote the article
- Do not invent statistics, prices, features or company claims

Return ONLY valid JSON with this structure:

{{
  "title": "Article title",
  "description": "A 150-160 character meta description",
  "category": "AI",
  "keywords": [
    "keyword 1",
    "keyword 2",
    "keyword 3"
  ],
  "introduction": "Introduction paragraph",
  "sections": [
    {{
      "heading": "Section heading",
      "content": "Section content"
    }}
  ],
  "conclusion": "Conclusion paragraph"
}}
"""

# -----------------------------
# Generate article
# -----------------------------

response = client.models.generate_content(
    model=MODEL,
    contents=prompt
)

# -----------------------------
# Parse JSON
# -----------------------------

try:
    article = json.loads(response.text)
except json.JSONDecodeError:
    print("Gemini returned invalid JSON:")
    print(response.text)
    raise

# -----------------------------
# Save result
# -----------------------------

os.makedirs("generated", exist_ok=True)

with open(
    "generated/article.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        article,
        f,
        ensure_ascii=False,
        indent=2
    )

print("Article generated successfully.")
print(json.dumps(article, indent=2, ensure_ascii=False))
