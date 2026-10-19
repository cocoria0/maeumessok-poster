"""스레드 예약 게시: threads_posts.json 에서 시간(한국시간)이 지난 것 하나를 글로 올린다.
항목: {"id": "w1-am", "text": "...", "at": "2026-10-19 21:00", "done": null, "post_id": null}
실패하면 error 를 적고 done 처리(같은 글을 계속 재시도하지 않음)."""
import datetime as dt, json, os, time, urllib.parse, urllib.request

TOK = os.environ["THREADS_TOKEN"]
UID = os.environ["THREADS_USER_ID"]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = "https://graph.threads.net/v1.0"


def api(path, data):
    req = urllib.request.Request(f"{G}/{path}", data=urllib.parse.urlencode({**data, "access_token": TOK}).encode())
    try:
        return json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Threads API {e.code}: {e.read().decode('utf-8', 'ignore')[:300]}")


p = os.path.join(ROOT, "threads_posts.json")
posts = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []
now = dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).strftime("%Y-%m-%d %H:%M")
for x in posts:
    if x.get("done") or x["at"] > now:
        continue
    try:
        cid = api(f"{UID}/threads", {"media_type": "TEXT", "text": x["text"]})["id"]
        time.sleep(5)
        pid = api(f"{UID}/threads_publish", {"creation_id": cid})["id"]
        x.update(done=now, post_id=pid)
        print(now, "스레드 게시:", x["id"], pid)
    except Exception as e:
        x.update(done=now, error=str(e)[:300])
        print(now, "스레드 실패:", x["id"], e)
    json.dump(posts, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    break
else:
    print(now, "올릴 스레드 예약 없음")
