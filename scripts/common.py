"""공통: 인스타 API 호출, 파일 읽고 쓰기. 토큰은 GitHub Secrets(IG_TOKEN, IG_USER_ID)에서 환경변수로 받는다."""
import json, os, urllib.parse, urllib.request

G = "https://graph.instagram.com/v21.0"
TOK = os.environ["IG_TOKEN"]
IGID = os.environ["IG_USER_ID"]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.environ.get("GITHUB_REPOSITORY", "cocoria0/maeumessok-poster")
INPOCK = "https://link.inpock.co.kr/maeumessok"
HEAD = "이 포스팅은 쿠팡파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다."


def api(path, data=None):
    url = f"{G}/{path}"
    if data is None:
        url += ("&" if "?" in url else "?") + "access_token=" + TOK
        req = urllib.request.Request(url)
    else:
        req = urllib.request.Request(url, data=urllib.parse.urlencode({**data, "access_token": TOK}).encode())
    try:
        return json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"IG API {e.code}: {e.read().decode('utf-8', 'ignore')[:300]}")


def load(name, default):
    p = os.path.join(ROOT, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default


def save(name, obj):
    json.dump(obj, open(os.path.join(ROOT, name), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def raw_url(path):
    """저장소 파일의 공개 주소 (인스타가 영상을 가져가는 주소)."""
    return f"https://raw.githubusercontent.com/{REPO}/main/{urllib.parse.quote(path)}"
