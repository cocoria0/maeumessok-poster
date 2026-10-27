"""스레드 예약 게시: threads_posts.json 에서 시간(한국시간)이 지난 것 하나를 올린다.
항목: {"id": "w1-am", "text": "...", "image": "threads_img/01.jpg" 또는 "video": "videos/025.mp4", "topic": "스킨케어"(주제 태그, 선택),
       "at": "2026-10-19 21:00", "done": null, "post_id": null}
★ 사진이나 영상이 없는 항목은 올리지 않는다(글만 올리지 않기 — 운영 규칙). 실패하면 error 를 적고 done 처리."""
import datetime as dt, json, os, time, urllib.parse, urllib.request

TOK = os.environ["THREADS_TOKEN"]
UID = os.environ["THREADS_USER_ID"]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.environ.get("GITHUB_REPOSITORY", "")
G = "https://graph.threads.net/v1.0"


def api(path, data=None):
    if data is None:
        url = f"{G}/{path}{'&' if '?' in path else '?'}access_token={TOK}"
        req = urllib.request.Request(url)
    else:
        req = urllib.request.Request(f"{G}/{path}", data=urllib.parse.urlencode({**data, "access_token": TOK}).encode())
    try:
        return json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Threads API {e.code}: {e.read().decode('utf-8', 'ignore')[:300]}")


def raw(path):
    return f"https://raw.githubusercontent.com/{REPO}/main/{urllib.parse.quote(path)}"


p = os.path.join(ROOT, "threads_posts.json")
posts = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []
now = dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).strftime("%Y-%m-%d %H:%M")
for x in posts:
    if x.get("done") or x["at"] > now:
        continue
    try:
        if x.get("video"):
            body = {"media_type": "VIDEO", "video_url": raw(x["video"]), "text": x["text"]}
        elif x.get("image"):
            body = {"media_type": "IMAGE", "image_url": raw(x["image"]), "text": x["text"]}
        else:
            raise RuntimeError("사진·영상 없음 — 글만은 올리지 않음")
        if x.get("topic"):                       # 주제 태그 — 팔로워 없는 계정은 이걸로 노출된다
            body["topic_tag"] = x["topic"]
        cid = api(f"{UID}/threads", body)["id"]
        for _ in range(60):                      # 영상은 처리 시간이 걸린다
            st = api(f"{cid}?fields=status,error_message")
            if st.get("status") == "FINISHED":
                break
            if st.get("status") == "ERROR":
                raise RuntimeError("처리 실패: " + str(st))
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
