#!/usr/bin/env python3
"""Send a daily arXiv email digest for LLM-related papers."""

from __future__ import annotations

import datetime as dt
import os
import smtplib
import ssl
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.message import EmailMessage

DEFAULT_QUERY = (
    'all:"large language model" OR all:"text LLM" OR '
    'all:pretraining OR all:post-training OR all:"reinforcement learning" OR '
    'all:"RLHF" OR all:"alignment"'
)
ARXIV_API = "https://export.arxiv.org/api/query"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def fetch_papers(query: str, max_results: int) -> list[dict[str, str]]:
    params = {
        "search_query": query,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": str(max_results),
    }
    url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=30) as response:
        xml_data = response.read()

    root = ET.fromstring(xml_data)
    papers: list[dict[str, str]] = []

    for entry in root.findall("atom:entry", ATOM_NS):
        title = " ".join((entry.findtext("atom:title", default="", namespaces=ATOM_NS) or "").split())
        summary = " ".join((entry.findtext("atom:summary", default="", namespaces=ATOM_NS) or "").split())
        published = entry.findtext("atom:published", default="", namespaces=ATOM_NS) or ""
        link = ""
        for link_node in entry.findall("atom:link", ATOM_NS):
            if link_node.attrib.get("rel") == "alternate":
                link = link_node.attrib.get("href", "")
                break
        authors = [
            (author.findtext("atom:name", default="", namespaces=ATOM_NS) or "").strip()
            for author in entry.findall("atom:author", ATOM_NS)
        ]
        papers.append(
            {
                "title": title,
                "summary": summary,
                "published": published,
                "link": link,
                "authors": ", ".join([a for a in authors if a]),
            }
        )
    return papers


def only_recent(papers: list[dict[str, str]], lookback_days: int) -> list[dict[str, str]]:
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=lookback_days)
    filtered: list[dict[str, str]] = []
    for paper in papers:
        try:
            published = dt.datetime.fromisoformat(paper["published"].replace("Z", "+00:00"))
        except ValueError:
            continue
        if published >= cutoff:
            filtered.append(paper)
    return filtered


def build_email_body(papers: list[dict[str, str]], query: str) -> str:
    today = dt.datetime.now().strftime("%Y-%m-%d")
    header = [
        f"Daily arXiv digest ({today})",
        f"Query: {query}",
        f"Papers found: {len(papers)}",
        "",
    ]
    if not papers:
        return "\n".join(header + ["No new papers in the selected period."])

    lines = header
    for idx, paper in enumerate(papers, start=1):
        lines.extend(
            [
                f"{idx}. {paper['title']}",
                f"   Authors: {paper['authors']}",
                f"   Published: {paper['published']}",
                f"   Link: {paper['link']}",
                f"   Summary: {paper['summary']}",
                "",
            ]
        )
    return "\n".join(lines)


def send_email(subject: str, body: str) -> None:
    smtp_host = os.environ["SMTP_HOST"]
    smtp_port = int(os.getenv("SMTP_PORT", "465"))
    smtp_user = os.environ["SMTP_USER"]
    smtp_password = os.environ["SMTP_PASSWORD"]
    email_to = os.getenv("EMAIL_TO", "linweili@gmail.com")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = email_to
    msg.set_content(body)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
        server.login(smtp_user, smtp_password)
        server.send_message(msg)


def main() -> None:
    query = os.getenv("ARXIV_QUERY", DEFAULT_QUERY)
    max_results = int(os.getenv("ARXIV_MAX_RESULTS", "30"))
    lookback_days = int(os.getenv("ARXIV_LOOKBACK_DAYS", "1"))

    papers = fetch_papers(query=query, max_results=max_results)
    recent = only_recent(papers, lookback_days=lookback_days)

    subject = f"arXiv daily digest: {len(recent)} new LLM-related papers"
    body = build_email_body(recent, query=query)
    send_email(subject, body)


if __name__ == "__main__":
    main()
