"""
fetch_indie_projects.py
从 1c7/chinese-independent-developer 抓取最近新增的项目
转换为 articles.json 格式并合并到现有数据中
"""

import json
import re
import os
import sys
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError


RAW_URL = "https://raw.githubusercontent.com/1c7/chinese-independent-developer/master/README.md"
ARTICLES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "articles.json")


def fetch_readme():
    """下载 README.md 原文"""
    req = Request(RAW_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def parse_recent_sections(md_text, days=7):
    """解析最近 N 天内新增的项目区块"""
    # 匹配日期标题: ## 或 ### 2026年4月5日新增 或 2026 年 4 月 5 日新增（有空格版本）
    date_pattern = re.compile(
        r"^#{2,4}\s+(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日\s*新增",
        re.MULTILINE,
    )
    cutoff = datetime.now() - timedelta(days=days)

    sections = []
    matches = list(date_pattern.finditer(md_text))

    for i, m in enumerate(matches):
        year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
        section_date = datetime(year, month, day)

        if section_date < cutoff:
            continue

        # 截取该日期到下一个日期之间的内容
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md_text)
        block = md_text[start:end]

        sections.append({
            "date": section_date.strftime("%Y-%m-%d"),
            "content": block,
        })

    return sections


def parse_projects_from_block(block):
    """从一个日期区块中提取项目列表"""
    projects = []

    # 匹配开发者标题: #### [Name](url) 或 ### [Name](url)
    dev_pattern = re.compile(r"^#{2,4}\s+\[([^\]]+)\]\(([^)]+)\)", re.MULTILINE)
    # 也匹配无链接的开发者: #### Name 或 #### Name - [Github](url)
    dev_plain_pattern = re.compile(r"^#{2,4}\s+(\S+?)(?:\s*-\s*\[(?:Github|github)\]\(([^)]+)\))?", re.MULTILINE)
    # 匹配项目条目: * :emoji: [Name](url): description
    item_pattern = re.compile(
        r"^\*\s+:(\w+):\s+\[([^\]]+)\]\(([^)]+)\)[：:]\s*(.+)",
        re.MULTILINE,
    )

    current_dev = "未知开发者"
    current_dev_url = ""

    lines = block.split("\n")
    for line in lines:
        stripped = line.strip()

        # 跳过日期标题行
        if re.match(r"^#{2,4}\s+\d{4}年", stripped):
            continue

        dev_m = dev_pattern.match(stripped)
        if dev_m:
            current_dev = dev_m.group(1)
            current_dev_url = dev_m.group(2)
            continue

        # 无链接的开发者名 + 可能带 Github 链接
        dev_p = re.match(r"^#{2,4}\s+(.+?)(?:\s*-\s*\[(?:Github|github|GitHub)\]\(([^)]+)\))?\s*$", stripped)
        if dev_p and not stripped.startswith("* "):
            current_dev = dev_p.group(1).strip()
            current_dev_url = dev_p.group(2) or ""
            continue

        item_m = item_pattern.match(line.strip())
        if item_m:
            status_emoji = item_m.group(1)
            name = item_m.group(2)
            url = item_m.group(3)
            desc = item_m.group(4).strip()

            # 状态映射
            if status_emoji == "white_check_mark":
                status = "运营中"
            elif status_emoji == "x":
                status = "已关闭"
            elif status_emoji == "clock8":
                status = "开发中"
            else:
                status = "未知"

            projects.append({
                "name": name,
                "url": url,
                "description": desc,
                "developer": current_dev,
                "developer_url": current_dev_url,
                "status": status,
            })

    return projects


def projects_to_article(projects, date_str):
    """把一天的项目列表转成一篇 article"""
    if not projects:
        return None

    # 只取运营中和开发中的项目，限制最多 20 个
    active = [p for p in projects if p["status"] in ("运营中", "开发中")][:20]
    if not active:
        active = projects[:20]

    # 构建摘要
    names = [p["name"] for p in active[:5]]
    summary = f"中国独立开发者项目列表 {date_str} 更新，新增 {len(active)} 个项目：{'、'.join(names)}{'等' if len(active) > 5 else ''}。"

    # 构建正文
    content_lines = [f"中国独立开发者项目列表 {date_str} 更新，共新增 {len(projects)} 个项目。\n"]
    for p in active:
        status_tag = f"[{p['status']}]" if p["status"] != "运营中" else ""
        content_lines.append(f"【{p['name']}】{status_tag} {p['description']}")
        content_lines.append(f"  开发者: {p['developer']} | 链接: {p['url']}")
        content_lines.append("")

    return {
        "title": f"独立开发者项目周报 · {date_str}",
        "summary": summary,
        "content": "\n".join(content_lines),
        "author": "1c7/chinese-independent-developer",
        "date": date_str,
        "tags": ["开源", "产品", "行业"],
        "source": "https://github.com/1c7/chinese-independent-developer",
    }


def get_next_id(articles):
    """获取下一个可用 ID"""
    max_num = 0
    for a in articles:
        m = re.match(r"news-(\d+)", a.get("id", ""))
        if m:
            max_num = max(max_num, int(m.group(1)))
    return max_num + 1


def main():
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7

    print(f"[Fetch] 抓取最近 {days} 天的独立开发者项目...")
    md_text = fetch_readme()
    print(f"[Fetch] README 大小: {len(md_text)} 字符")

    sections = parse_recent_sections(md_text, days=days)
    print(f"[Parse] 找到 {len(sections)} 个日期区块")

    if not sections:
        print("[Done] 没有新项目，退出")
        return

    # 读取现有 articles
    if os.path.exists(ARTICLES_PATH):
        with open(ARTICLES_PATH, "r", encoding="utf-8") as f:
            articles = json.load(f)
    else:
        articles = []

    # 检查已有的日期，避免重复
    existing_dates = set()
    for a in articles:
        if "独立开发者项目周报" in a.get("title", ""):
            # 从标题中提取日期
            m = re.search(r"\d{4}-\d{2}-\d{2}", a["title"])
            if m:
                existing_dates.add(m.group(0))

    next_id = get_next_id(articles)
    new_count = 0

    for section in sections:
        if section["date"] in existing_dates:
            print(f"[Skip] {section['date']} 已存在")
            continue

        projects = parse_projects_from_block(section["content"])
        if not projects:
            print(f"[Skip] {section['date']} 没有解析到项目")
            continue

        article = projects_to_article(projects, section["date"])
        if article:
            article["id"] = f"news-{next_id:03d}"
            next_id += 1
            articles.insert(0, article)
            new_count += 1
            print(f"[Add] {article['id']}: {article['title']} ({len(projects)} 个项目)")

    if new_count == 0:
        print("[Done] 没有新文章需要添加")
        return

    # 按日期降序排列
    articles.sort(key=lambda a: a.get("date", ""), reverse=True)

    # 写回
    with open(ARTICLES_PATH, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"[Done] 新增 {new_count} 篇文章，总计 {len(articles)} 篇")


if __name__ == "__main__":
    main()
