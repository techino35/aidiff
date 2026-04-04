"""
Bluesky自動投稿スクリプト
使い方:
  python tools/bluesky_poster.py tips          # Tipsをランダム投稿
  python tools/bluesky_poster.py release 0.1.2 # リリース告知
  python tools/bluesky_poster.py star 100      # starマイルストーン
  python tools/bluesky_poster.py custom "文章" # カスタム投稿
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
    "💡 aidiff tip: `aidiff scan` でリポジトリ全体のAIコード率を一発確認。どのファイルがAI生成か可視化できます。\n\npip install aidiff\ngithub.com/techino35/aidiff",
    "💡 aidiff tip: `aidiff track <file>` で行レベルのAIスコアを表示。レビュー時に「ここはAIが書いた」が一目でわかる。\n\npip install aidiff\ngithub.com/techino35/aidiff",
    "💡 aidiff tip: `aidiff install` でpre-commitフックをセット。コミットごとに自動でAIコード率を記録します。\n\npip install aidiff\ngithub.com/techino35/aidiff",
    "💡 aidiff tip: `aidiff report` でHTMLレポート生成。AIコード率のトレンド・ファイル別ヒートマップを可視化。\n\npip install aidiff\ngithub.com/techino35/aidiff",
    "💡 aidiff tip: GitHub Actionsに組み込めばPRごとにAIコード率をコメント。`aidiff init-action` で設定ファイルを自動生成。\n\npip install aidiff\ngithub.com/techino35/aidiff",
    "AI生成コードが増えてるのに、誰も追跡していない。\n\ngit blameで「誰が書いたか」はわかる。でも「AIが書いたか」はわからない。\n\naidiffはその空白を埋めるOSS。\n\npip install aidiff\ngithub.com/techino35/aidiff",
    "Claude Code / Cursor / Copilot を使うチームへ。\n\nどのファイルがほぼAI生成か把握してますか？\n\naidiffを使えば `aidiff scan` 一発でわかります。\n\npip install aidiff",
]

RELEASE_TEMPLATE = """🚀 aidiff v{version} リリース

git blameのAI版。どのコードがAIに書かれたか追跡するOSSです。

pip install aidiff=={version}

詳細: github.com/techino35/aidiff"""

STAR_TEMPLATE = """⭐ aidiff が {stars} stars を達成しました！

応援してくれた皆さんありがとうございます。

AIコード追跡ツールとして開発を続けます。

github.com/techino35/aidiff"""


def post(text: str) -> None:
    client = Client()
    client.login(HANDLE, PASSWORD)
    client.send_post(text)
    print(f"[OK] Posted: {text[:50]}...")


def main() -> None:
    if len(sys.argv) < 2:
        print("使い方: python bluesky_poster.py [tips|release|star|custom]")
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
            print("テキストを指定してください")
            sys.exit(1)
        post(text)
    else:
        print(f"不明なモード: {mode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
