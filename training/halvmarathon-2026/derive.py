import json, datetime as dt

prog = json.load(open("/tmp/claude-0/-home-user-airfoil-vv/e0d67b19-fb3a-5005-9f31-03d2385f9eca/scratchpad/program.json", encoding="utf-8"))

# --- faktiska pass fran Coros (Jun 1 - Aug 11) ---
runs = [
 ("2026-08-05", 0.979, "8:30"), ("2026-08-05", 3.68, "5:14"), ("2026-08-03", 4.01, "5:59"),
 ("2026-08-02", 3.61, "9:25"), ("2026-07-31", 10.82, "7:18"), ("2026-07-31", 0.0, "-"),
 ("2026-07-29", 5.45, "6:31"), ("2026-07-27", 5.56, "6:53"), ("2026-07-21", 4.00, "6:12"),
 ("2026-07-18", 8.19, "7:18"), ("2026-07-12", 8.65, "8:15"), ("2026-07-09", 5.47, "7:06"),
 ("2026-07-07", 4.01, "6:12"), ("2026-07-05", 4.13, "7:18"), ("2026-06-25", 4.01, "7:19"),
 ("2026-06-23", 5.60, "8:00"), ("2026-06-22", 4.02, "6:44"), ("2026-06-17", 5.46, "7:29"),
 ("2026-06-16", 4.82, "8:12"), ("2026-06-10", 0.920, "6:00"), ("2026-06-08", 1.02, "6:03"),
 ("2026-06-07", 1.99, "7:14"),
]

def monday(d):
    d = dt.date.fromisoformat(d)
    return (d - dt.timedelta(days=d.weekday())).isoformat()

actual = {}
for d, km, _ in runs:
    actual[monday(d)] = actual.get(monday(d), 0) + km

rows = []
for w in prog:
    start = w["days"][0]["date"]
    if start < "2026-06-01":
        continue
    a = round(actual.get(start, 0), 1)
    rows.append({"week": w["week"], "start": start, "plan": round(w["km"], 1), "actual": a,
                 "pct": round(100 * a / w["km"])})

print("v  vecka-start   plan   faktisk   %")
for r in rows:
    print(f"{r['week']:2d}  {r['start']}  {r['plan']:5.1f}  {r['actual']:6.1f}  {r['pct']:4d}%")
tp, ta = sum(r["plan"] for r in rows), sum(r["actual"] for r in rows)
print(f"SUMMA (v{rows[0]['week']}-{rows[-1]['week']}): plan {tp:.0f} km, faktisk {ta:.0f} km = {100*ta/tp:.0f}%")
print("Snitt faktisk/vecka:", round(ta / len(rows), 1), "km  | Langsta pass:", max(k for _, k, _ in runs), "km")

# --- tempozoner fran troskelfart 5:05 ---
LT = 5 * 60 + 5
def mmss(s):
    s = round(s); return f"{s // 60}:{s % 60:02d}"
zones = [
 ("Aterhamtning", 1.28, 1.40, "Konversationstempo. Ska kannas nastan for latt."),
 ("Lugn distans",  1.18, 1.28, "Grundpasset. Har ligger de flesta km."),
 ("Langpass / tavlingsfart", 1.08, 1.15, "Din halvmarathonfart pa loppdagen."),
 ("Troskel",       0.97, 1.03, "~60 min max-tempo. Har byggs farthallfasthet."),
 ("Intervall (VO2)", 0.88, 0.94, "3-5 min-intervaller."),
 ("Koordination / kort", 0.80, 0.86, "80-300 m, avspand snabbhet."),
]
print("\nTEMPOZONER (troskel 5:05/km)")
zj = []
for n, f1, f2 in [(z[0], z[1], z[2]) for z in zones]:
    zj.append({"name": n, "lo": mmss(LT * f1), "hi": mmss(LT * f2)})
for z, src in zip(zj, zones):
    print(f"  {z['name']:<26} {z['lo']}-{z['hi']} /km   {src[3]}")

# --- lopptider ---
D = 21.0975
print("\nMALTIDER")
scen = [("Programmets mal 1.40", 4 * 60 + 44), ("Coros-prognos", 5 * 60 + 27),
        ("Plan B - bra dag", 5 * 60 + 30), ("Plan A - kontrollerad", 5 * 60 + 45),
        ("Plan C - fullfolja tryggt", 6 * 60 + 0)]
sj = []
for n, p in scen:
    t = p * D
    h, rem = divmod(round(t), 3600); m, s = divmod(rem, 60)
    sj.append({"name": n, "pace": mmss(p), "time": f"{h}:{m:02d}:{s:02d}"})
    print(f"  {n:<28} {mmss(p)}/km  ->  {h}:{m:02d}:{s:02d}")

# 5 km-mellantider for Plan A (5:45) med lugn start
print("\nMELLANTIDER PLAN A (negativ split)")
segs = [("0-5 km", 5, 5 * 60 + 55), ("5-10 km", 5, 5 * 60 + 50), ("10-15 km", 5, 5 * 60 + 42),
        ("15-20 km", 5, 5 * 60 + 38), ("20-21,1 km", 1.0975, 5 * 60 + 30)]
cum = 0; splits = []
for n, km, p in segs:
    cum += km * p
    h, rem = divmod(round(cum), 3600); m, s = divmod(rem, 60)
    splits.append({"seg": n, "pace": mmss(p), "cum": f"{h}:{m:02d}:{s:02d}"})
    print(f"  {n:<12} {mmss(p)}/km   passering {h}:{m:02d}:{s:02d}")

json.dump({"weekly": rows, "zones": zj, "scen": sj, "splits": splits},
          open("/tmp/claude-0/-home-user-airfoil-vv/e0d67b19-fb3a-5005-9f31-03d2385f9eca/scratchpad/derived.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
