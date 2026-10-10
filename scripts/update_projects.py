#!/usr/bin/env python3
"""Update the auto-generated projects section in the profile README."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

USERNAME = os.environ.get("GITHUB_USERNAME", "Yassine-Jemi01")
PROFILE_REPO = os.environ.get("PROFILE_REPO", USERNAME).casefold()
README_PATH = Path(os.environ.get("README_PATH", "README.md"))
START_MARKER = "<!-- AUTO-PROJECTS:START -->"
END_MARKER = "<!-- AUTO-PROJECTS:END -->"
PROJECT_LIMIT = 5
API_ROOT = "https://api.github.com"


def parse_datetime(value: str | None) -> datetime:
    """Parse a GitHub ISO timestamp, falling back to the Unix epoch."""
    if not value:
        return datetime.fromtimestamp(0, tz=timezone.utc)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except (ValueError, TypeError):
        return datetime.fromtimestamp(0, tz=timezone.utc)


def fetch_repositories() -> list[dict]:
    """Read all public repositories owned by USERNAME through the GitHub API."""
    token = os.environ.get("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "profile-readme-project-updater",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    repositories: list[dict] = []
    for page in range(1, 11):
        url = (
            f"{API_ROOT}/users/{quote(USERNAME, safe='')}/repos"
            f"?type=owner&sort=updated&per_page=100&page={page}"
        )
        request = Request(url, headers=headers)
        try:
            with urlopen(request, timeout=20) as response:
                batch = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Could not fetch repositories from GitHub: {exc}") from exc

        if not istance(batch, list):
            raise RuntimeError("GitHub API returned an unexpected response format.")
        if not batch:
            break

        repositories.extend(batch)
        if len(batch) < 100:
            break

    return repositories


def markdown_cell(value: object) -> str:
    """Keep repository fields safe for a Markdown table cell."""
    text = str(value or "—")
    text = re.sub(r"[\r\n\t]+", " ", text).strip()
    text = text.replace("|", r"\|").replace("`", r"\`")
    return text or "—"


def project_score(repo: dict, now: datetime) -> tuple[float, int, float]:
    """Weight stars and recent maintenance; recency bonus falls to zero after 30 days."""
    try:
        stars = int(repo.get("stargazers_count") or 0)
    except (ValueError, TypeError):
        stars = 0

    pushed = parse_datetime(repo.get("pushed_at"))
    age_days = max(0, (now - pushed).days)
    recency_bonus = max(0, 30 - age_days)
    score = stars * 2 + recency_bonus
    return (score, stars, pushed.timestamp())


def select_projects(repositories: list[dict], now: datetime | None = None) -> list[dict]:
    """Select owned, public, non-forked, active projects and rank them by score."""
    now = now or datetime.now(timezone.utc)
    candidates = []
    for repo in repositories:
        if not isinstance(repo, dict):
            continue
        name = str(repo.get("name") or "")
        if not name or name.casefold() == PROFILE_REPO:
            continue
        if repo.get("private") or repo.get("fork") or repo.get("archived") or repo.get("disabled"):
            continue
        if not repo.get("html_url"):
            continue
        candidates.append(repo)

    candidates.sort(key=lambda repo: project_score(repo, now), reverse=True)
    return candidates[:PROJECT_LIMIT]


def render_projects(projects: list[dict]) -> str:
    """Render the selected projects as a compact Markdown table."""
    if not projects:
        return "_No public repositories were found yet._"

    rows = [
        "| Project | Description | Language | Stars |",
        "|---|---|---:|---:|",
    ]
    for repo in projects:
        name = markdown_cell(repo.get("name"))
        url = markdown_cell(repo.get("html_url"))
        description = markdown_cell(repo.get("description") or "Open-source project; see the repository for details.")
        language = markdown_cell(repo.get("language"))
        try:
            stars = max(0, int(repo.get("stargazers_count") or 0))
        except (ValueError, TypeError):
            stars = 0
        rows.append(f"| [{name}]({url}) | {description} | {language} | {stars} |")
    return "\n".join(rows)


def update_readme(readme_path: Path, generated_section: str) -> bool:
    """Replace exactly the content between the project's README markers."""
    content = readme_path.read_text(encoding="utf-8")
    if content.count(START_MARKER) != 1 or content.count(END_MARKER) != 1:
        raise RuntimeError(
            f"README must contain exactly one {START_MARKER} and one {END_MARKER} marker."
        )
    start = content.index(START_MARKER) + len(START_MARKER)
    end = content.index(END_MARKER)
    if end < start:
        raise RuntimeError("README project markers are in the wrong order.")

    new_content = content[:start] + "\n" + generated_section + "\n" + content[end:]
    if new_content == content:
        print("Project list is already up to date.")
        return False

    readme_path.write_text(new_content, encoding="utf-8")
    print("Updated the generated project section.")
    return True


def main() -> int:
    try:
        repositories = fetch_repositories()
        now = datetime.now(timezone.utc)
        projects = select_projects(repositories, now)
        generated_section = render_projects(projects)
        update_readme(README_PATH, generated_section)
    except (OSError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
