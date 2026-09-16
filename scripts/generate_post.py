import os
import json
import time
import re
from html import escape
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

    # Support the new topic format:
    # {
    #   "title": "...",
    #   "source": "...",
    #   "url": "..."
    # }

    topic_list = "\n".join(
        f"{i + 1}. {topic['title']}"
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
  "selected_topic": "exact topic title from the list"
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

    selected_title = selection["selected_topic"]

    selected_topic = None

    for topic in topics:

        if topic["title"] == selected_title:

            selected_topic = topic
            break

    if selected_topic is None:

        raise RuntimeError(
            "Gemini selected a topic that was not in topics.json."
        )

    print("-----------------------------------")
    print("SELECTED TOPIC")
    print("-----------------------------------")
    print(selected_topic["title"])

    print("SOURCE")
    print(selected_topic["source"])

    print("URL")
    print(selected_topic["url"])

    return selected_topic


TOPIC_DATA = select_topic()

TOPIC = TOPIC_DATA["title"]


# -----------------------------------
# Prompt
# -----------------------------------

def create_prompt():

    return f"""
You are an expert technology writer.

Write a useful, accurate and original article about:

{TOPIC}

The topic was discovered from this source:

Source: {TOPIC_DATA["source"]}
URL: {TOPIC_DATA["url"]}

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


# -----------------------------------
# Create slug
# -----------------------------------

def create_slug(title):

    slug = title.lower()

    slug = re.sub(
        r"[^a-z0-9\s-]",
        "",
        slug
    )

    slug = re.sub(
        r"\s+",
        "-",
        slug
    )

    slug = re.sub(
        r"-+",
        "-",
        slug
    )

    return slug.strip("-")


# -----------------------------------
# Create article HTML
# -----------------------------------

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

    <div class="container header-inner">

        <a href="../index.html" class="logo">
            AI <span>&</span> Technology Hub
        </a>

        <nav>

            <a href="../index.html">
                Home
            </a>

            <a href="../index.html#articles">
                Latest
            </a>

            <a href="../index.html#about">
                About
            </a>

        </nav>

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

    <div class="container footer-inner">

        <p>
            © 2026 AI & Technology Hub
        </p>

        <p>
            AI • Technology • Innovation
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

            filepath = os.path.join(
                "posts",
                filename
            )

            with open(
                filepath,
                "r",
                encoding="utf-8"
            ) as f:

                content = f.read()

            # Get title
            match = re.search(
                r"<title>(.*?)</title>",
                content,
                re.IGNORECASE
            )

            if match:

                title = match.group(1)

            else:

                title = filename.replace(
                    ".html",
                    ""
                ).replace(
                    "-",
                    " "
                ).title()

            # Get description
            description_match = re.search(
                r'<meta name="description"\s+content="(.*?)">',
                content,
                re.IGNORECASE
            )

            if description_match:

                description = description_match.group(1)

            else:

                description = (
                    "Read the latest AI and technology article."
                )

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

            <div class="card-category">
                AI & Technology
            </div>

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
          content="AI tools, technology, tutorials and digital insights for creators and developers.">

    <meta name="robots"
          content="index, follow">

    <link rel="stylesheet"
          href="style.css">

</head>

<body>

<header>

    <div class="container header-inner">

        <a href="index.html" class="logo">
            AI <span>&</span> Technology Hub
        </a>

        <nav>

            <a href="index.html">
                Home
            </a>

            <a href="#articles">
                Latest
            </a>

            <a href="#about">
                About
            </a>

        </nav>

    </div>

</header>


<main>

    <section class="hero">

        <div class="container">

            <div class="hero-label">
                AI & Technology
            </div>

            <h1>
                The latest in AI, technology and digital innovation.
            </h1>

            <p>
                Practical insights, tools, tutorials and technology news
                for creators, developers and curious minds.
            </p>

        </div>

    </section>


    <section class="container" id="articles">

        <div class="section-header">

            <h2>
                Latest Articles
            </h2>

        </div>


        <section class="articles">

            {cards}

        </section>

    </section>


    <section class="container" id="about">

        <div class="hero">

            <div class="hero-label">
                About
            </div>

            <h2>
                AI & Technology Hub
            </h2>

            <p>
                Exploring useful developments in artificial intelligence,
                software, automation, digital tools and emerging technology.
            </p>

        </div>

    </section>

</main>


<footer>

    <div class="container footer-inner">

        <p>
            © 2026 AI & Technology Hub
        </p>

        <p>
            AI • Technology • Innovation
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
