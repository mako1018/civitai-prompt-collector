import requests, json, urllib.parse, sys
POST_ID = 16613809
H = {"User-Agent":"Mozilla/5.0","Accept":"application/json, text/plain, */*"}
payload = {"json": {"id": int(POST_ID)}}
url = "https://civitai.com/api/trpc/post.getById?input=" + urllib.parse.quote(json.dumps(payload, separators=(",", ":")))
try:
    r = requests.get(url, headers=H, timeout=20)
    print("status:", r.status_code, "content-type:", r.headers.get("content-type"))
    txt = r.text
    print("len_text:", len(txt))
    try:
        j = r.json()
        print(json.dumps(j, ensure_ascii=False)[:8000])
    except Exception as e:
        print("json parse error:", e)
        print("raw start:", txt[:4000])
except Exception as e:
    print("request failed:", e)