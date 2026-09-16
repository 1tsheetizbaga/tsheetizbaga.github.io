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


# -----------------------------------
# Models
# -----------------------------------

MODELS = [
    "gemini-3.8-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
]

# -----------------------------------
# Select topic from discovered topics
# -----------------------------------

def select_topic():

    with open(
        "generated/topics.json",
        "r",
        encoding="utf-8"
    ) as f:

        topics = json.load(f)

    if not topics:
        raise RuntimeError(
            "No discovered topics available."
        )

    topic_list = "\n".join(
        f"{i + 1}. {topic}"
        for i, topic in enumerate(topics)
    )

    prompt = f"""
You are the editorial director of an AI and technology website.

Choose ONE topic from the list below.

The website focuses on:
- Artificial intelligence
- AI tools
- AI models
- AI video and image generation
- Automation
- Software
- Productivity technology
- Developer technology
- Cybersecurity
- Consumer technology

Avoid:
- Politics
- Elections
- Political personalities
- Political arguments
- General wars or geopolitical news
- Celebrity gossip
- Topics unrelated to technology

Choose the topic that has the strongest potential for a useful,
evergreen or timely technology article for digital creators.

Do NOT create a new topic.
Choose ONLY one topic from the supplied list.

Topics:

{topic_list}

Return ONLY valid JSON:

{{
  "selected_topic": "exact topic from the list"
}}
"""

    response = client.models.generate_content(
        model=MODELS[0],
        contents=prompt
    )

    result = response.text.strip()

    if result.startswith("```json"):
        result = result[7:]

    elif result.startswith("```"):
        result = result[3:]

    if result.endswith("```"):
        result = result[:-3]

    result = result.strip()

    selection = json.loads(result)

    selected_topic = selection["selected_topic"]

    if selected_topic not in topics:
        raise RuntimeError(
            "Gemini selected a topic that was not in topics.json."
        )

    print("-----------------------------------")
    print("SELECTED TOPIC")
    print("-----------------------------------")
    print(selected_topic)

    return selected_topic


TOPIC = select_topic()

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
import re
from html import escape


def create_slug(title):
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def create_article_html(article):

    title = escape(article["title"])
    description = escape(article["description"])
    category = escape(article["category"])
    introduction = escape(article["introduction"])
    conclusion = escape(article["conclusion"])

    sections_html = ""

    for section in article["sections"]:

        heading = escape(section["heading"])
        content = escape(section["content"])

        paragraphs = content.split("\n")

        content_html = ""

        for paragraph in paragraphs:

            if paragraph.strip():

                content_html += (
                    f"<p>{paragraph.strip()}</p>\n"
                )

        sections_html += f"""
        <section>
            <h2>{heading}</h2>
            {content_html}
        </section>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>{title}</title>

    <meta name="description"
          content="{description}">

    <meta property="og:title"
          content="{title}">

    <meta property="og:description"
          content="{description}">

    <meta name="robots"
          content="index, follow">

    <link rel="stylesheet"
          href="../style.css">

</head>

<body>

<header>

    <div class="container">

        <h1>AI & Technology Hub</h1>

        <p>AI, technology and digital insights.</p>

    </div>

</header>


<main class="container article-page">

    <article>

        <div class="category">
            {category}
        </div>

        <h1>{title}</h1>

        <p class="article-description">
            {description}
        </p>

        <div class="article-content">

            <p>
                {introduction}
            </p>

            {sections_html}

            <section>

                <h2>Conclusion</h2>

                <p>
                    {conclusion}
                </p>

            </section>

        </div>

    </article>

</main>


<footer>

    <div class="container">

        <p>
            © 2026 AI & Technology Hub
        </p>

    </div>

</footer>

</body>

</html>
"""

    return html


# -----------------------------------
# Create HTML article
# -----------------------------------

slug = create_slug(article["title"])

os.makedirs("posts", exist_ok=True)

article_path = f"posts/{slug}.html"

html = create_article_html(article)

with open(
    article_path,
    "w",
    encoding="utf-8"
) as f:

    f.write(html)

print("-----------------------------------")
print("HTML ARTICLE CREATED")
print("-----------------------------------")
print(article_path)
# -----------------------------------
# Update homepage
# -----------------------------------

def update_homepage():

    posts = []

    if os.path.exists("posts"):

        for filename in os.listdir("posts"):

            if not filename.endswith(".html"):
                continue

            filepath = os.path.join("posts", filename)

            with open(
                filepath,
                "r",
                encoding="utf-8"
            ) as f:

                content = f.read()

            # Get title from HTML
            match = re.search(
                r"<title>(.*?)</title>",
                content,
                re.IGNORECASE
            )

            if match:
                title = match.group(1)
            else:
                title = filename.replace(
                    ".html", ""
                ).replace("-", " ").title()

            # Get description
            description_match = re.search(
                r'<meta name="description"\s+content="(.*?)">',
                content,
                re.IGNORECASE
            )

            if description_match:
                description = description_match.group(1)
            else:
                description = "Read the latest AI and technology article."

            posts.append({
                "title": title,
                "description": description,
                "url": "posts/" + filename
            })


    # Newest posts first
    posts.reverse()


    # -----------------------------------
    # Create article cards
    # -----------------------------------

    cards = ""

    for post in posts:

        cards += f"""
        <article class="card">

            <h3>
                {post["title"]}
            </h3>

            <p>
                {post["description"]}
            </p>

            <a href="{post["url"]}">
                Read Article →
            </a>

        </article>
        """


    # -----------------------------------
    # Create homepage
    # -----------------------------------

    homepage = f"""<!DOCTYPE html>
<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>AI & Technology Hub</title>

    <meta name="description"
          content="AI tools, technology, tutorials and digital insights.">

    <link rel="stylesheet"
          href="style.css">

</head>

<body>

<header>

    <div class="container">

        <h1>AI & Technology Hub</h1>

        <p>
            AI tools, technology, tutorials and insights.
        </p>

    </div>

</header>


<main class="container">

    <section class="hero">

        <h2>Latest Articles</h2>

        <p>
            Explore the latest developments in AI
            and technology.
        </p>

    </section>


    <section class="articles">

        {cards}

    </section>

</main>


<footer>

    <div class="container">

        <p>
            © 2026 AI & Technology Hub
        </p>

    </div>

</footer>

</body>

</html>
"""


    with open(
        "index.html",
        "w",
        encoding="utf-8"
    ) as f:

        f.write(homepage)


    print("-----------------------------------")
    print("HOMEPAGE UPDATED")
    print("-----------------------------------")


update_homepage()
