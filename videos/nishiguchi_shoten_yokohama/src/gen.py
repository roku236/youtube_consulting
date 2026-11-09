import base64, json, sys, urllib.request, os
src, out, size = sys.argv[1], sys.argv[2], sys.argv[3]
extra = sys.argv[4] if len(sys.argv) > 4 else ""
b64 = base64.b64encode(open(src,'rb').read()).decode()
prompt = ("参照写真を元に、構図・料理の種類と形・具材の色・器の柄・テーブル・暗めで暖かい店内照明をできるだけ忠実に保ったまま、"
          "ほんの少しだけデフォルメした「写実寄りの厚塗りイラスト」に描き直してください。質感と焼き色・具材のディテールは写真の雰囲気を7割残し、"
          "輪郭をわずかに整え、色を少しだけ鮮やかに、ツヤとシズル感を少し強調。アニメ調・漫画調にはしない。"
          "文字・ロゴ・透かしは入れない。" + extra)
body = {"model":os.environ.get("MODEL","seedream-4-0-250828"),"prompt":prompt,"image":"data:image/jpeg;base64,"+b64,
        "size":size,"response_format":"b64_json","watermark":False,"sequential_image_generation":"disabled"}
req = urllib.request.Request("https://ark.ap-southeast.bytepluses.com/api/v3/images/generations",
      data=json.dumps(body).encode(), headers={"Content-Type":"application/json","Authorization":"Bearer placeholder"})
try:
    r = json.load(urllib.request.urlopen(req, timeout=300))
except urllib.error.HTTPError as e:
    print("HTTP", e.code, e.read().decode()[:800]); sys.exit(1)
d = r["data"][0]
open(out,'wb').write(base64.b64decode(d["b64_json"]))
print(out, r.get("usage"))
