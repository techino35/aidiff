"""
Bluesky auto-post script
Usage:
  python tools/bluesky_poster.py tips              # Random tips post
  python tools/bluesky_poster.py release 0.1.2     # Release announcement
  python tools/bluesky_poster.py star 100          # Star milestone
  python tools/bluesky_poster.py custom "text"     # Custom post
"""

import os
import sys
import random
from dotenv import load_dotenv
from atproto import Client

load_dotenv()

HANDLE = os.getenv("BLUESKY_HANDLE")
PASSWORD = os.getenv("BLUESKY_APP_PASSWORD")

TIPS = [
    "aidiff tip: Run `aidiff scan` to instantly see your repo's AI code ratio. Know exactly which files are mostly AI-generated.\n\npip install aidiff\ngithub.com/techino35/aidiff",
    "aidiff tip: `aidiff track <file>` shows AI scores line by line. Reviewers can instantly see which lines were written by AI.\n\npip install aidiff\ngithub.com/techino35/aidiff",
    "aidiff tip: `aidiff install` sets up a pre-commit hook. AI code ratio is recorded automatically on every commit.\n\npip install aidiff\ngithub.com/techino35/aidiff",
    "aidiff tip: `aidiff report` generates an HTML dashboard with AI ratio trends, file heatmaps, and contributor breakdown.\n\npip install aidiff\ngithub.com/techino35/aidiff",
    "aidiff tip: `aidiff init-action` generates a GitHub Action that auto-comments AI code ratio on every PR. Zero config.\n\npip install aidiff\ngithub.com/techino35/aidiff",
    "AI-generated code is everywhere. Nobody is tracking it.\n\ngit blame tells you who wrote it. But not whether AI wrote it.\n\naidiff fills that gap.\n\npip install aidiff\ngithub.com/techino35/aidiff",
    "Using Claude Code, Cursor, or Copilot?\n\nDo you know which files in your repo are mostly AI-generated?\n\n`aidiff scan` tells you in seconds.\n\npip install aidiff\ngithub.com/techino35/aidiff",
    "Studies show AI-assisted PRs have ~30% higher change failure rate.\n\nKnowing which code is AI-generated helps you review smarter.\n\naidiff makes AI code visible.\n\npip install aidiff\ngithub.com/techino35/aidiff",
]

RELEASE_TEMPLATE = """aidiff v{version} released

git blame for AI-generated code. Track, score, and visualize how much of your codebase was written by AI.

pip install aidiff=={version}

github.com/techino35/aidiff"""

STAR_TEMPLATE = """aidiff just hit {stars} stars!

Thank you to everyone who supported this project.

We'll keep building the best AI code tracking tool out there.

github.com/techino35/aidiff"""


def post(text: str) -> None:
    client = Client()
    client.login(HANDLE, PASSWORD)
    client.send_post(text)
    print(f"[OK] Posted: {text[:50]}...")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python bluesky_poster.py [tips|release|star|custom]")
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "tips":
        post(random.choice(TIPS))
    elif mode == "release":
        version = sys.argv[2] if len(sys.argv) > 2 else "latest"
        post(RELEASE_TEMPLATE.format(version=version))
    elif mode == "star":
        stars = sys.argv[2] if len(sys.argv) > 2 else "?"
        post(STAR_TEMPLATE.format(stars=stars))
    elif mode == "custom":
        text = sys.argv[2] if len(sys.argv) > 2 else ""
        if not text:
            print("Specify text.")
            sys.exit(1)
        post(text)
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
