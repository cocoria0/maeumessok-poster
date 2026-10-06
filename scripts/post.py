"""예약 게시: posts.json 에서 시간(한국시간)이 지난 것 하나를 인스타 릴스로 올린다.

posts.json 항목: {"no": 7, "file": "videos/007.mp4", "caption": "...", "block_title": "...", "dm_keywords": [...],
                   "at": "2026-10-07 19:00", "done": null, "media_id": null, "permalink": null}
올린 뒤 posted.json(댓글 DM 감시 목록)에도 넣는다. 실패하면 error 를 적고 done 처리(같은 걸 계속 재시도하지 않음).
"""
import datetime as dt, os, time, traceback
from common import api, load, save, raw_url, IGID

KST = dt.timezone(dt.timedelta(hours=9))
now = dt.datetime.now(KST).strftime("%Y-%m-%d %H:%M")
posts = load("posts.json", [])
for p in posts:
    if p.get("done") or not p.get("at") or p["at"] > now:
        continue
    try:
        if not os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), p["file"])):
            raise RuntimeError("영상 파일이 저장소에 없음: " + p["file"])
        c = api(f"{IGID}/media", {"media_type": "REELS", "video_url": raw_url(p["file"]), "caption": p["caption"], "share_to_feed": "true"})
        cid = c["id"]
        for _ in range(60):
            st = api(f"{cid}?fields=status_code,status")
            if st.get("status_code") == "FINISHED":
                break
            if st.get("status_code") == "ERROR":
                raise RuntimeError("인스타 처리 실패: " + str(st))
            time.sleep(5)
        else:
            raise RuntimeError("인코딩 대기 시간 초과")
        mid = api(f"{IGID}/media_publish", {"creation_id": cid})["id"]
        info = api(f"{mid}?fields=permalink")
        p.update(done=now, media_id=mid, permalink=info.get("permalink"))
        posted = load("posted.json", [])
        posted.append({"no": p["no"], "media_id": mid, "permalink": info.get("permalink"),
                       "block_title": p["block_title"], "dm_keywords": p.get("dm_keywords", [])})
        save("posted.json", posted)
        print(now, "게시:", p["no"], info.get("permalink"))
    except Exception as e:
        p.update(done=now, error=str(e)[:300])
        print(now, "실패:", p["no"], e)
        traceback.print_exc()
    save("posts.json", posts)
    break
else:
    print(now, "올릴 예약 없음")
