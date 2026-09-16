import os
import json
import time
from google import genai

# -----------------------------------
# Configuration
# -----------------------------------

API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set.")

client = genai.Client(api_key=API_KEY)

TOPIC = "Best AI Video Generators for YouTube Creators"


# -----------------------------------
# Models
# -----------------------------------

MODELS = [
    "gemini-3.8-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
]


# -----------------------------------
# Prompt
# -----------------------------------

def create_prompt():

    return f"""
You are an expert technology writer.

Write a useful, accurate and original article about:

{TOPIC}

Target audience:
YouTube creators and digital content creators.

Requirements:

- Create a clear and useful title.
- Write a strong introduction.
- Use logical H2 sections.
- Give practical information.
- Avoid unnecessary filler.
- Do not invent statistics.
- Do not invent prices.
- Do not invent product features.
- Do not make unsupported claims.
- Do not mention that AI wrote the article.
- Write naturally.
- Return ONLY valid JSON.

Use exactly this structure:

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


# -----------------------------------
# Generate article
# -----------------------------------

def generate_article():

    prompt = create_prompt()

    for model in MODELS:

        print("-----------------------------------")
        print(f"Trying model: {model}")
        print("-----------------------------------")

        for attempt in range(1, 3):

            try:

                print(
                    f"Attempt {attempt}/2 using {model}"
                )

                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )

                result = response.text.strip()

                # Remove markdown code fences
                if result.startswith("```json"):
                    result = result[7:]

                elif result.startswith("```"):
                    result = result[3:]

                if result.endswith("```"):
                    result = result[:-3]

                result = result.strip()

                article = json.loads(result)

                print(
                    f"SUCCESS: Article generated with {model}"
                )

                return article

            except Exception as e:

                print(
                    f"{model} attempt {attempt} failed:"
                )

                print(str(e))

                if attempt == 1:

                    print(
                        "Waiting 10 seconds before retry..."
                    )

                    time.sleep(10)


    raise RuntimeError(
        "All Gemini models failed."
    )


# -----------------------------------
# Save article
# -----------------------------------

article = generate_article()

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

print("-----------------------------------")
print("ARTICLE GENERATED SUCCESSFULLY")
print("-----------------------------------")

print(
    json.dumps(
        article,
        ensure_ascii=False,
        indent=2
    )
)
