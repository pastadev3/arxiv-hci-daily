import feedparser
import yagmail
import yaml
from datetime import datetime, timedelta, timezone
from dateutil import parser as dateparser  # pip install python-dateutil
from translate import Translator  # pip install translate

# 設定ファイルの読み込み
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# arXiv APIのURL（HCIカテゴリ）
ARXIV_URL = (
    f"http://export.arxiv.org/api/query?search_query=cat:cs.HC"
    f"&sortBy=submittedDate&sortOrder=descending"
    f"&max_results={config['max_results']}"
)

# フィード取得
feed = feedparser.parse(ARXIV_URL)

# 前日の日付（JST）
JST = timezone(timedelta(hours=9))
now = datetime.now(JST)
yesterday_date_str = (now - timedelta(days=1)).strftime("%Y-%m-%d")

# 翻訳器（英→日）
translator = Translator(to_lang="ja")

# メール内容構築
subject = f"[arXiv HCI] {yesterday_date_str} に投稿された新着論文"
body_lines = []

# 前日投稿の論文を収集
papers = []
for entry in feed.entries:
    published_dt = dateparser.isoparse(entry.published)
    if now - published_dt <= timedelta(hours=24):
        title_en = entry.title.replace("\n ", "").strip()
        try:
            title_ja = translator.translate(title_en)
        except Exception:
            title_ja = "(翻訳失敗)"
        url = entry.link
        papers.append((title_en, title_ja, url))

# 件数と内容整形
if papers:
    body_lines.append(f"{len(papers)} 件の論文が見つかりました。\n")
    for i, (en, ja, link) in enumerate(papers, start=1):
        body_lines.append(f"{i}. {en}\n   → {ja}\n   {link}\n")
else:
    body_lines.append("直近24時間に投稿された新着論文はありませんでした。")

# メール送信
yag = yagmail.SMTP(config["gmail_user"], config["gmail_app_password"])
yag.send(to=config["to_email"], subject=subject, contents="\n".join(body_lines))

print("✅ メール送信完了")
