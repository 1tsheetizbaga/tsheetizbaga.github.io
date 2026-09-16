import os
import json
import time
from google import genai

API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set.")

client = genai.Client(api_key=API_KEY)

# Stable Gemini model
MODEL = "gemini-3.8-flash"

TOPIC = "Best AI Video Generators for YouTube Creators"


def generate_article():
    prompt = f"""
You are an expert technology writer.

Write a useful, accurate and original article about:

{TOPIC}

Target audience:
YouTube creators and digital content creators.

Requirements:

- Create a clear, useful title.
- Write a strong introduction.
- Use logical H2 sections.
- Give practical information.
- Avoid filler.
- Do not invent statistics.
- Do not invent prices.
- Do not invent product features.
- Do not make unsupported claims.
- Do not mention that AI wrote the article.
- Write naturally.
- Return ONLY valid JSON.

Use this exact structure:

{{
  "title": "Article title",
  "description": "Meta description",
  "category": "AI",
  "keywords": [
    "keyword 1",
    "keyword 2",
    "keyword 3"
  ],
  "introduction": "Introduction",
  "sections": [
    {{
      "heading": "Section heading",
      "content": "Section content"
    }}
  ],
  "conclusion": "Conclusion"
}}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    return response.text


# Try up to 3 times if Gemini temporarily returns an error
for attempt in range(1, 4):

    try:
        print(f"Generating article... attempt {attempt}/3")

        result = generate_article()

        # Remove accidental markdown code fences
        result = result.strip()

        if result.startswith("```json"):
            result = result[7:]

        if result.startswith("```"):
            result = result[3:]

        if result.endswith("```"):
            result = result[:-3]

        result = result.strip()

        article = json.loads(result)

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

        break

    except Exception as e:

        print(f"Attempt {attempt} failed:")
        print(e)

        if attempt < 3:
            print("Waiting 10 seconds before retry...")
            time.sleep(10)

        else:
            print("All attempts failed.")
            raise
