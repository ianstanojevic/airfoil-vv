import re, json, html, urllib.request, time, sys
sys.path.insert(0, "/tmp/claude-0/-home-user-airfoil-vv/e0d67b19-fb3a-5005-9f31-03d2385f9eca/scratchpad")
from scrape import parse_week  # reuse parser

BASE = "https://trana.marathon.se/adidas-stockholm-halvmarathon-2026/adidas-stockholm-halvmarathon-"
LEVELS = ["120", "130", "140", "210", "245"]

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for a in range(4):
        try:
            return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
        except Exception:
            if a == 3: raise
            time.sleep(2 ** a)

out = {}
for lv in LEVELS:
    weeks = []
    for w in range(1, 21):
        weeks.append(parse_week(fetch(f"{BASE}{lv}/{w}"), w))
    out[lv] = weeks
    km = [x["km"] or 0 for x in weeks]
    ss = [x["sessions"] or 0 for x in weeks]
    longest = []
    for x in weeks:
        best = 0
        for d in x["days"]:
            try:
                best = max(best, float((d["distance"] or "0").replace(" km", "").replace(",", ".")))
            except ValueError:
                pass
        longest.append(best)
    print(f"--- {lv[0]}.{lv[1:]}  totalt {sum(km):.0f} km")
    print(f"    v1 {km[0]:.0f} km/{ss[0]} pass · topp {max(km):.0f} km (v{km.index(max(km))+1}) · "
          f"snitt {sum(km)/20:.1f} km/v · pass {min(ss)}-{max(ss)}")
    print(f"    långpass v1 {longest[0]:.0f} km · max {max(longest):.0f} km")
    out[lv + "_summary"] = {"total": round(sum(km)), "w1": km[0], "w1_sess": ss[0],
                            "peak": max(km), "avg": round(sum(km)/20, 1),
                            "long1": longest[0], "longmax": max(longest),
                            "km": km, "sess": ss, "long": longest}

json.dump(out, open("/tmp/claude-0/-home-user-airfoil-vv/e0d67b19-fb3a-5005-9f31-03d2385f9eca/scratchpad/all_levels.json", "w", encoding="utf-8"), ensure_ascii=False)
print("\nsaved all_levels.json")
