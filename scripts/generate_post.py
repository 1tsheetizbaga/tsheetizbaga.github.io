import os
import json
import time
import re
from html import escape
from urllib.parse import quote
from urllib.request import Request, urlopen

from google import genai


# ============================================================
# CONFIG
# ============================================================

MODELS = [
    "gemini-3.8-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
]

API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set")


client = genai.Client(api_key=API_KEY)


# ============================================================
# LOAD TOPICS
# ============================================================

def load_topics():
    with open("generated/topics.json", "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# SELECT TOPIC
# ============================================================

def select_topic():
    topics_data = load_topics()

    if not topics_data:
        raise RuntimeError("No topics found")

    topic_titles = [
        item["title"] if isinstance(item, dict) else item
        for item in topics_data
    ]

    prompt = f"""
You are an editor for a modern AI and technology website.

Choose ONE topic from the list below.

Choose the topic that would make the most useful and interesting
article for readers interested in AI, technology, software,
automation, productivity, developers, or digital tools.

Return ONLY the exact topic title.

Topics:

{chr(10).join(topic_titles)}
"""

    for model in MODELS:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )

                selected = response.text.strip().strip('"')

                for item in topics_data:
                    title = item["title"] if isinstance(item, dict) else item

                    if title.lower() == selected.lower():
                        return item if isinstance(item, dict) else {
                            "title": item,
                            "source": "",
                            "url": ""
                        }

                # Fallback if Gemini slightly changes the title
                for item in topics_data:
                    title = item["title"] if isinstance(item, dict) else item

                    if selected.lower() in title.lower():
                        return item if isinstance(item, dict) else {
                            "title": item,
                            "source": "",
                            "url": ""
                        }

            except Exception as e:
                print(f"Topic selection failed with {model}: {e}")
                time.sleep(10)

    # Final fallback
    first = topics_data[0]

    return first if isinstance(first, dict) else {
        "title": first,
        "source": "",
        "url": ""
    }


TOPIC_DATA = select_topic()
TOPIC = TOPIC_DATA["title"]

print("Selected topic:", TOPIC)


# ============================================================
# GENERATE ARTICLE
# ============================================================

article_prompt = f"""
Write a high-quality article for a modern AI and technology website.

Topic:
{TOPIC}

The topic was discovered from:

Source:
{TOPIC_DATA.get("source", "")}

URL:
{TOPIC_DATA.get("url", "")}

Create an informative article for general readers.

Return ONLY valid JSON.

Use exactly this structure:

{{
  "title": "article title",
  "description": "short SEO description",
  "category": "AI",
  "keywords": ["keyword 1", "keyword 2", "keyword 3"],
  "introduction": "introduction paragraph",
  "sections": [
    {{
      "heading": "section heading",
      "content": "section content"
    }},
    {{
      "heading": "section heading",
      "content": "section content"
    }},
    {{
      "heading": "section heading",
      "content": "section content"
    }}
  ],
  "conclusion": "conclusion paragraph"
}}

Requirements:

- Do not invent facts.
- Keep the article useful and readable.
- Use clear headings.
- Avoid political content.
- Avoid exaggerated claims.
- Do not include markdown.
- Return JSON only.
"""


def generate_article():

    for model in MODELS:

        for attempt in range(2):

            try:

                response = client.models.generate_content(
                    model=model,
                    contents=article_prompt
                )

                text = response.text.strip()

                # Remove accidental markdown fences
                text = re.sub(
                    r"^```json\s*",
                    "",
                    text,
                    flags=re.IGNORECASE
                )

                text = re.sub(
                    r"\s*```$",
                    "",
                    text
                )

                return json.loads(text)

            except Exception as e:

                print(
                    f"Article generation failed "
                    f"with {model}: {e}"
                )

                time.sleep(10)

    raise RuntimeError("All article generation attempts failed")


article = generate_article()


# ============================================================
# FIND IMAGE FROM OPENVERSE
# ============================================================

def find_image(topic):

    print("Searching Openverse for image:", topic)

    # Simplify the search query
    query = topic

    api_url = (
        "https://api.openverse.org/v1/images/"
        f"?q={quote(query)}"
        "&page_size=10"
    )

    try:

        request = Request(
            api_url,
            headers={
                "User-Agent": "AI-Tech-Blog/1.0"
            }
        )

        with urlopen(request, timeout=30) as response:

            data = json.loads(
                response.read().decode("utf-8")
            )

        results = data.get("results", [])

        if not results:
            print("No Openverse images found.")
            return None

        # Prefer images with useful dimensions
        results = sorted(
            results,
            key=lambda x: (
                x.get("width", 0) or 0
            ),
            reverse=True
        )

        for item in results:

            image_url = item.get("url")

            if not image_url:
                continue

            width = item.get("width") or 0
            height = item.get("height") or 0

            # Avoid tiny images
            if width and width < 600:
                continue

            creator = (
                item.get("creator")
                or "Unknown creator"
            )

            title = (
                item.get("title")
                or topic
            )

            license_name = (
                item.get("license")
                or "Open license"
            )

            landing_url = (
                item.get("foreign_landing_url")
                or ""
            )

            return {
                "url": image_url,
                "title": title,
                "creator": creator,
                "license": license_name,
                "landing_url": landing_url,
                "width": width,
                "height": height
            }

        return None

    except Exception as e:

        print("Image search failed:", e)

        return None


image = find_image(TOPIC)

if image:
    print("Image found:", image["url"])
else:
    print("Continuing without image.")


# ============================================================
# SAVE ARTICLE JSON
# ============================================================

article["image"] = image

article["source"] = {
    "name": TOPIC_DATA.get("source", ""),
    "url": TOPIC_DATA.get("url", "")
}

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


# ============================================================
# CREATE SLUG
# ============================================================

def make_slug(title):

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


slug = make_slug(
    article["title"]
)

if not slug:

    slug = "ai-technology-article"


# ============================================================
# ARTICLE HTML
# ============================================================

def create_article_html(article):

    title = escape(article["title"])

    description = escape(
        article.get("description", "")
    )

    category = escape(
        article.get("category", "Technology")
    )

    introduction = escape(
        article.get("introduction", "")
    )

    conclusion = escape(
        article.get("conclusion", "")
    )

    sections_html = ""

    for section in article.get("sections", []):

        heading = escape(
            section.get("heading", "")
        )

        content = escape(
            section.get("content", "")
        )

        sections_html += f"""
        <section class="article-section">
            <h2>{heading}</h2>
            <p>{content}</p>
        </section>
        """

    # --------------------------------------------------------
    # IMAGE HTML
    # --------------------------------------------------------

    image_html = ""

    if article.get("image"):

        img = article["image"]

        image_url = escape(
            img.get("url", "")
        )

        image_title = escape(
            img.get("title", article["title"])
        )

        creator = escape(
            img.get("creator", "Unknown creator")
        )

        license_name = escape(
            img.get("license", "Open license")
        )

        landing_url = escape(
            img.get("landing_url", "")
        )

        credit = f"Image: {creator} · {license_name}"

        if landing_url:

            credit_html = f"""
            <a href="{landing_url}"
               target="_blank"
               rel="noopener noreferrer">
                {credit}
            </a>
            """

        else:

            credit_html = credit

        image_html = f"""
        <figure class="article-hero-image">

            <img
                src="{image_url}"
                alt="{image_title}"
                loading="eager"
            >

            <figcaption>
                {credit_html}
            </figcaption>

        </figure>
        """

    # --------------------------------------------------------
    # FULL HTML
    # --------------------------------------------------------

    return f"""<!DOCTYPE html>

<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>{title}</title>

    <meta
        name="description"
        content="{description}"
    >

    <link
        rel="stylesheet"
        href="../style.css"
    >

</head>

<body>

<header class="site-header">

    <div class="container header-inner">

        <a
            href="../index.html"
            class="logo"
        >
            AI <span>&</span> Technology
        </a>

        <nav>

            <a href="../index.html">
                Home
            </a>

            <a href="../index.html#latest">
                Latest
            </a>

            <a href="../index.html#about">
                About
            </a>

        </nav>

    </div>

</header>


<main class="article-page">

    <div class="container">

        <div class="article-category">
            {category}
        </div>

        <h1>
            {title}
        </h1>

        <p class="article-description">
            {description}
        </p>

        {image_html}

        <div class="article-content">

            <p class="article-introduction">
                {introduction}
            </p>

            {sections_html}

            <section class="article-section">

                <h2>
                    Conclusion
                </h2>

                <p>
                    {conclusion}
                </p>

            </section>

        </div>

    </div>

</main>


<footer class="footer">

    <div class="container">

        <p>
            © 2026 AI & Technology
        </p>

    </div>

</footer>

</body>

</html>
"""


# ============================================================
# SAVE ARTICLE PAGE
# ============================================================

os.makedirs("posts", exist_ok=True)

article_path = f"posts/{slug}.html"

with open(
    article_path,
    "w",
    encoding="utf-8"
) as f:

    f.write(
        create_article_html(article)
    )


print("Article created:", article_path)


# ============================================================
# HOMEPAGE
# ============================================================

def generate_homepage():

    posts_dir = "posts"

    posts = []

    for filename in os.listdir(posts_dir):

        if not filename.endswith(".html"):
            continue

        path = os.path.join(
            posts_dir,
            filename
        )

        try:

            with open(
                path,
                "r",
                encoding="utf-8"
            ) as f:

                html = f.read()

            title_match = re.search(
                r"<h1>(.*?)</h1>",
                html,
                re.S
            )

            description_match = re.search(
                r'<p class="article-description">(.*?)</p>',
                html,
                re.S
            )

            category_match = re.search(
                r'<div class="article-category">(.*?)</div>',
                html,
                re.S
            )

            image_match = re.search(
                r'<img\s+src="([^"]+)"',
                html
            )

            title = (
                title_match.group(1).strip()
                if title_match
                else filename
            )

            description = (
                description_match.group(1).strip()
                if description_match
                else ""
            )

            category = (
                category_match.group(1).strip()
                if category_match
                else "Technology"
            )

            image_url = (
                image_match.group(1)
                if image_match
                else ""
            )

            posts.append({
                "filename": filename,
                "title": title,
                "description": description,
                "category": category,
                "image": image_url
            })

        except Exception as e:

            print(
                f"Could not read {filename}: {e}"
            )


    posts.reverse()

    cards = ""

    for post in posts[:12]:

        image_html = ""

        if post["image"]:

            image_html = f"""
            <img
                src="{post["image"]}"
                alt="{post["title"]}"
                loading="lazy"
            >
            """

        else:

            image_html = """
            <div class="card-image-placeholder">
                AI & Technology
            </div>
            """

        cards += f"""

        <article class="card">

            <a href="posts/{post["filename"]}">

                <div class="card-image">

                    {image_html}

                </div>

                <div class="card-body">

                    <div class="card-category">
                        {post["category"]}
                    </div>

                    <h3>
                        {post["title"]}
                    </h3>

                    <p>
                        {post["description"]}
                    </p>

                    <span class="read-more">
                        Read Article →
                    </span>

                </div>

            </a>

        </article>

        """


    homepage = f"""<!DOCTYPE html>

<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>
        AI & Technology
    </title>

    <meta
        name="description"
        content="AI, technology, software, automation and digital innovation."
    >

    <link
        rel="stylesheet"
        href="style.css"
    >

</head>


<body>


<header class="site-header">

    <div class="container header-inner">

        <a
            href="index.html"
            class="logo"
        >
            AI <span>&</span> Technology
        </a>

        <nav>

            <a href="index.html">
                Home
            </a>

            <a href="#latest">
                Latest
            </a>

            <a href="#about">
                About
            </a>

        </nav>

    </div>

</header>


<section class="hero">

    <div class="container">

        <div class="hero-label">
            AI & TECHNOLOGY
        </div>

        <h1>
            The latest in AI,
            technology and
            digital innovation.
        </h1>

        <p>
            Practical insights, tools,
            tutorials and technology
            news for curious minds.
        </p>

    </div>

</section>


<section
    class="articles"
    id="latest"
>

    <div class="container">

        <div class="section-header">

            <h2>
                Latest Articles
            </h2>

            <span>
                Updated automatically
            </span>

        </div>


        <div class="articles-grid">

            {cards}

        </div>

    </div>

</section>


<section
    class="about"
    id="about"
>

    <div class="container">

        <h2>
            About
        </h2>

        <p>
            AI & Technology explores
            artificial intelligence,
            software, automation,
            digital tools and the
            technologies shaping the future.
        </p>

    </div>

</section>


<footer class="footer">

    <div class="container">

        <p>
            © 2026 AI & Technology
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


generate_homepage()

print("Homepage updated successfully.")
