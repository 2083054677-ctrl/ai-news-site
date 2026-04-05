"""
fetch_ai_news.py
从多个公开 RSS / API 源抓取最新 AI 资讯
转换为 articles.json 格式并合并到现有数据中
零依赖，纯标准库
"""

import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError
from html.parser import HTMLParser


ARTICLES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "articles.json")

# RSS 源列表
RSS_FEEDS = [
    {
        "name": "Hacker News (AI)",
        "url": "https://hnrss.org/newest?q=AI+OR+LLM+OR+GPT+OR+Claude+OR+OpenAI&count=10",
        "tags": ["AI", "行业"],
    },
    {
        "name": "The Decoder",
        "url": "https://the-decoder.com/feed/",
        "tags": ["AI", "研究"],
    },
    {
        "name": "Hugging Face Blog",
        "url": "https://huggingface.co/blog/feed.xml",
        "tags": ["AI", "开源", "大模型"],
    },
]

# 限制每个源最多取几条
MAX_PER_FEED = 5
# 只取最近 N 小时的新闻
MAX_AGE_HOURS = 48


class HTMLStripper(HTMLParser):
    """去除 HTML 标签"""
    def __init__(self):
        super().__init__()
        self.result = []

    def handle_data(self, data):
        self.result.append(data)

    def get_text(self):
        return ''.join(self.result).strip()


def strip_html(html_str):
    if not html_str:
        return ""
    s = HTMLStripper()
    s.feed(html_str)
    text = s.get_text()
    # 清理多余空白
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def fetch_url(url, timeout=20):
    req = Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; AI-News-Bot/1.0)",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    })
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_rss(xml_text, feed_config):
    """解析 RSS/Atom feed，返回文章列表"""
    articles = []
    cutoff = datetime.now() - timedelta(hours=MAX_AGE_HOURS)

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        print(f"  [XML Error] {feed_config['name']}: {e}")
        return []

    # 处理命名空间
    ns = {
        'atom': 'http://www.w3.org/2005/Atom',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'content': 'http://purl.org/rss/1.0/modules/content/',
    }

    items = []
    # RSS 2.0
    for item in root.iter('item'):
        items.append(('rss', item))
    # Atom
    for entry in root.iter('{http://www.w3.org/2005/Atom}entry'):
        items.append(('atom', entry))

    for fmt, item in items[:MAX_PER_FEED]:
        try:
            if fmt == 'rss':
                title = (item.findtext('title') or '').strip()
                link = (item.findtext('link') or '').strip()
                desc = item.findtext('description') or item.findtext('{http://purl.org/rss/1.0/modules/content/}encoded') or ''
                pub_date_str = item.findtext('pubDate') or item.findtext('{http://purl.org/dc/elements/1.1/}date') or ''
                author = item.findtext('{http://purl.org/dc/elements/1.1/}creator') or feed_config['name']
            else:
                title = (item.findtext('{http://www.w3.org/2005/Atom}title') or '').strip()
                link_el = item.find('{http://www.w3.org/2005/Atom}link')
                link = link_el.get('href', '') if link_el is not None else ''
                desc = item.findtext('{http://www.w3.org/2005/Atom}summary') or item.findtext('{http://www.w3.org/2005/Atom}content') or ''
                pub_date_str = item.findtext('{http://www.w3.org/2005/Atom}published') or item.findtext('{http://www.w3.org/2005/Atom}updated') or ''
                author_el = item.find('{http://www.w3.org/2005/Atom}author')
                author = author_el.findtext('{http://www.w3.org/2005/Atom}name') if author_el is not None else feed_config['name']

            if not title or not link:
                continue

            # 解析日期
            pub_date = parse_date(pub_date_str)
            if pub_date and pub_date < cutoff:
                continue

            date_str = pub_date.strftime("%Y-%m-%d") if pub_date else datetime.now().strftime("%Y-%m-%d")

            # 清理描述
            summary = strip_html(desc)[:200]
            content = strip_html(desc)[:500]

            articles.append({
                "title": title,
                "summary": summary if summary else title,
                "content": content if content else summary,
                "author": strip_html(str(author)) or feed_config['name'],
                "date": date_str,
                "tags": feed_config['tags'],
                "source": link,
            })
        except Exception as e:
            print(f"  [Parse Error] {feed_config['name']}: {e}")
            continue

    return articles


def parse_date(date_str):
    """尝试解析各种日期格式"""
    if not date_str:
        return None
    date_str = date_str.strip()

    formats = [
        "%a, %d %b %Y %H:%M:%S %z",       # RSS: Mon, 01 Apr 2026 12:00:00 +0000
        "%a, %d %b %Y %H:%M:%S %Z",        # RSS: Mon, 01 Apr 2026 12:00:00 GMT
        "%Y-%m-%dT%H:%M:%S%z",             # Atom: 2026-04-01T12:00:00+00:00
        "%Y-%m-%dT%H:%M:%SZ",              # Atom: 2026-04-01T12:00:00Z
        "%Y-%m-%d %H:%M:%S",               # Generic
        "%Y-%m-%d",                          # Just date
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.replace(tzinfo=None)  # 去掉时区，简化比较
        except ValueError:
            continue

    # 尝试去掉尾部时区文本
    cleaned = re.sub(r'\s+\w{3,4}$', '', date_str)
    for fmt in formats:
        try:
            return datetime.strptime(cleaned, fmt).replace(tzinfo=None)
        except ValueError:
            continue

    return None


def get_next_id(articles):
    max_num = 0
    for a in articles:
        m = re.match(r"news-(\d+)", a.get("id", ""))
        if m:
            max_num = max(max_num, int(m.group(1)))
    return max_num + 1


def main():
    print(f"[AI News] 开始抓取，最近 {MAX_AGE_HOURS} 小时的新闻...")

    # 读取现有文章
    if os.path.exists(ARTICLES_PATH):
        with open(ARTICLES_PATH, "r", encoding="utf-8") as f:
            articles = json.load(f)
    else:
        articles = []

    # 现有文章的 source URL 集合，用于去重
    existing_urls = {a.get("source", "") for a in articles}

    next_id = get_next_id(articles)
    new_count = 0

    for feed in RSS_FEEDS:
        print(f"  [Feed] {feed['name']}...")
        try:
            xml_text = fetch_url(feed['url'])
            new_items = parse_rss(xml_text, feed)
            print(f"    获取到 {len(new_items)} 条")

            for item in new_items:
                # 去重：URL 或标题相同则跳过
                if item['source'] in existing_urls:
                    continue
                if any(a['title'] == item['title'] for a in articles):
                    continue

                item['id'] = f"news-{next_id:03d}"
                next_id += 1
                articles.insert(0, item)
                existing_urls.add(item['source'])
                new_count += 1
                print(f"    [+] {item['id']}: {item['title'][:50]}")

        except Exception as e:
            print(f"    [Error] {feed['name']}: {e}")

    if new_count == 0:
        print("[Done] 没有新文章")
        return

    # 按日期降序
    articles.sort(key=lambda a: a.get("date", ""), reverse=True)

    with open(ARTICLES_PATH, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"[Done] 新增 {new_count} 篇，总计 {len(articles)} 篇")


if __name__ == "__main__":
    main()
