import re, json, html, urllib.request, time

BASE = "https://trana.marathon.se/adidas-stockholm-halvmarathon-2026/adidas-stockholm-halvmarathon-140"

def clean(x):
    x = re.sub(r"<[^>]+>", " ", x)
    x = html.unescape(x)
    return re.sub(r"\s+", " ", x).strip()

def fetch(week):
    url = f"{BASE}/{week}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(4):
        try:
            return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
        except Exception as e:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)

def parse_week(s, wk):
    out = {"week": wk}
    m = re.search(r"Träningsvecka\s*(\d+)\s*\(av\s*(\d+)\)", clean(s))
    if m:
        out["week"] = int(m.group(1)); out["total_weeks"] = int(m.group(2))
    m = re.search(r"Denna vecka:\s*(\d+)\s*träningspass", clean(s))
    out["sessions"] = int(m.group(1)) if m else None
    # weekly km: the views-field-field-distance right after the sessions span
    m = re.search(r"Denna vecka.*?field-content\">\s*([\d,\.]+)\s*km", s, re.S)
    out["km"] = float(m.group(1).replace(",", ".")) if m else None

    days = []
    for dm in re.finditer(r'<div class="exercise" id="([\d\-]+)">(.*?)(?=<div class="exercise" id="|\Z)', s, re.S):
        did, body = dm.group(1), dm.group(2)
        head = re.search(r'<div class="exercise-head">(.*?)</div>\s*<div class="exercise-content', body, re.S)
        head_html = head.group(1) if head else ""
        weekday = re.search(r'<span class="h2"><span class="date-display-single">([^<]+)', head_html)
        dist = re.search(r'<div class="distance"><span></span>([^<]*)</div>', head_html)
        tim = re.search(r'<div class="time"><span></span>([^<]*)</div>', head_html)
        moments = []
        for mm in re.finditer(r'<div class="field-exercise-moment">(.*?)</div>\s*(?=<div class="field-exercise-moment">|</div>\s*</div>|\Z)', body, re.S):
            mb = mm.group(1)
            typ = re.search(r'<div class="field-ref-exercise-type">\s*(.*?)\s*</div>', mb, re.S)
            d = re.search(r'field-readable-distance inline">\s*(.*?)\s*</span>', mb, re.S)
            t = re.search(r'field-readable-time inline">\s*(.*?)\s*</span>', mb, re.S)
            r = re.search(r'field-readable-repetition[^"]*inline">\s*(.*?)\s*</span>', mb, re.S)
            if typ:
                moments.append({
                    "type": clean(typ.group(1)),
                    "distance": clean(d.group(1)) if d else None,
                    "time": clean(t.group(1)) if t else None,
                    "reps": clean(r.group(1)) if r else None,
                })
        dd, mo, yy = did.split("-")
        days.append({
            "date": f"{yy}-{int(mo):02d}-{int(dd):02d}",
            "weekday": clean(weekday.group(1)) if weekday else None,
            "distance": clean(dist.group(1)) if dist else None,
            "time": clean(tim.group(1)) if tim else None,
            "moments": moments,
        })
    out["days"] = days
    return out

weeks = []
for w in range(1, 21):
    s = fetch(w)
    pw = parse_week(s, w)
    weeks.append(pw)
    print(f"week {pw['week']}: {pw['sessions']} pass, {pw['km']} km, {len(pw['days'])} dagar, "
          f"{pw['days'][0]['date'] if pw['days'] else '?'} .. {pw['days'][-1]['date'] if pw['days'] else '?'}")

json.dump(weeks, open("program.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("TOTAL km:", sum(w["km"] or 0 for w in weeks))
