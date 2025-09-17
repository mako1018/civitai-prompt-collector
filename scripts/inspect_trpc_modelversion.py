import requests, json, sys
URL = "https://civitai.com/api/trpc/modelVersion.getById?input=%7B%22json%22:%7B%22id%22:1759168%7D%7D"
h = {"User-Agent":"Mozilla/5.0","Accept":"application/json, text/plain, */*"}
try:
    r = requests.get(URL, headers=h, timeout=15)
    print("status:", r.status_code)
    print("content-type:", r.headers.get("content-type"))
    txt = r.text
    print("len_text:", len(txt))
    with open("tmp_modelversion_trpc.json","w",encoding="utf-8") as f:
        f.write(txt)
    try:
        j = r.json()
    except Exception as e:
        print("json parse error:", e)
        print("raw start:", txt[:4000])
        sys.exit(0)
    if isinstance(j, dict):
        print("top keys:", list(j.keys())[:50])
    print(json.dumps(j, ensure_ascii=False)[:8000])
except Exception as e:
    print("request failed:", e)