import json
import re
import urllib.request
import xml.etree.ElementTree as ET

# -----------------------------------
# Google News RSS feeds
# -----------------------------------

FEEDS = [
    "https://news.google.com/rss/search?q=AI+technology&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=AI+tools&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=generative+AI&hl=en-US&gl=US&ceid=US:en",
]


def get_feed(url):

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=20
    ) as response:

        return response.read()


def clean_title(title):

    # Remove publisher name after " - "
    title = re.sub(
        r"\s+-\s+[^-]+$",
        "",
        title
    )

    return title.strip()


# -----------------------------------
# Collect headlines
# -----------------------------------

topics = []
seen_titles = set()

for feed_url in FEEDS:

    try:

        data = get_feed(feed_url)

        root = ET.fromstring(data)

        for item in root.findall(".//item"):

            title_element = item.find("title")
            link_element = item.find("link")
            source_element = item.find("source")

            if title_element is None:
                continue

            title = clean_title(
                title_element.text or ""
            )

            if not title:
                continue

            if title in seen_titles:
                continue

            url = ""

            if link_element is not None:
                url = link_element.text or ""

            source = ""

            if source_element is not None:
                source = source_element.text or ""

            topics.append({
                "title": title,
                "source": source,
                "url": url
            })

            seen_titles.add(title)

    except Exception as e:

        print(
            f"Feed failed: {feed_url}"
        )

        print(e)


# -----------------------------------
# Filter topics
# -----------------------------------

BLOCKED_WORDS = [
    "Trump",
    "Biden",
    "Sanders",
    "Senate",
    "Congress",
    "election",
    "Democrat",
    "Republican",
    "politics",
    "political",
    "regulation",
    "bipartisan",
    "China",
    "Iran",
    "Israel",
    "war",
    "Ukraine",
    "Russia",
]


def is_relevant(topic):

    topic_lower = topic["title"].lower()

    for word in BLOCKED_WORDS:

        if word.lower() in topic_lower:
            return False

    return True


topics = [
    topic
    for topic in topics
    if is_relevant(topic)
]


# -----------------------------------
# Keep first 20 relevant topics
# -----------------------------------

topics = topics[:20]


if not topics:

    raise RuntimeError(
        "No topics were found."
    )


# -----------------------------------
# Save topics
# -----------------------------------

with open(
    "generated/topics.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        topics,
        f,
        ensure_ascii=False,
        indent=2
    )


# -----------------------------------
# Display results
# -----------------------------------

print("-----------------------------------")
print("TOPICS DISCOVERED")
print("-----------------------------------")

for number, topic in enumerate(
    topics,
    start=1
):

    print(
        f"{number}. {topic['title']}"
    )

    print(
        f"   Source: {topic['source']}"
    )

    print(
        f"   URL: {topic['url']}"
    )
