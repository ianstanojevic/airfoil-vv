import json, datetime as dt

prog = json.load(open("/tmp/claude-0/-home-user-airfoil-vv/e0d67b19-fb3a-5005-9f31-03d2385f9eca/scratchpad/program.json", encoding="utf-8"))
START = dt.date(2026, 8, 17)

#      v:  1   2   3   4*  5   6   7   8   9*  10  11  12  13* 14  15  16  17* 18  19  20
KM   = [15, 17, 19, 14, 20, 23, 26, 29, 22, 31, 34, 37, 27, 40, 43, 46, 33, 48, 36, 26]
LONG = [ 7,  8,  9,  7,  9, 10, 11, 12, 10, 13, 14, 15, 12, 16, 17, 18, 14, 20, 16, 21.1]
SESS = [ 3,  3,  3,  3,  3,  4,  4,  4,  4,  4,  4,  4,  4,  5,  5,  5,  5,  5,  4,  3]
DOWN = [i for i in range(20) if i in (3, 8, 12, 16)]

PHASE = [(0,5,"Grundbygge"),(6,12,"Uppbyggnad"),(13,17,"Specifik"),(18,19,"Nedtrappning")]
FOCUS = ["Bara lugn löpning. Vänja kroppen vid att springa ofta.",
         "Lugnt + första fartinslaget sist i ett pass.",
         "Långpasset når 9 km — nära ditt längsta någonsin.",
         "Nedvecka. Volym ned, ingen fart.",
         "Långpasset 9 km. Volymen tillbaka uppåt efter nedveckan.",
         "Fjärde passet in. Stegrad fart introduceras.",
         "Långpass 11 km — nytt rekord. Backlöpning som styrka.",
         "Första riktiga tröskelpasset.",
         "Nedvecka. Tröskeln vilar.",
         "Tröskel + långpass i samma vecka.",
         "Intervaller kort. Farthållfasthet.",
         "Största volymen hittills. Långpass 15 km.",
         "Nedvecka före specifik fas.",
         "Femte passet. Tävlingsfart introduceras.",
         "Långpass med tävlingsfart i slutet.",
         "Toppvolym närmar sig. Långpass 18 km.",
         "Nedvecka. Skärpan behålls, volymen halveras.",
         "Toppvecka. Längsta passet 20 km.",
         "Nedtrappning. Volym ned 25 %, farten kvar.",
         "Måldag lördag 2 januari: 21,1 km."]

def phase(i):
    for a, b, n in PHASE:
        if a <= i <= b: return n
    return ""

rows, prev_up = [], None
print(" v  datum          orig  anpassad  %   pass  långpass  fas")
for i in range(20):
    mon = START + dt.timedelta(weeks=i); sun = mon + dt.timedelta(days=6)
    down = i in DOWN
    rows.append({"w": i+1, "mon": mon.isoformat(), "sun": sun.isoformat(),
                 "label": f"{mon.strftime('%-d/%-m')}–{sun.strftime('%-d/%-m')}",
                 "orig": round(prog[i]["km"], 1), "km": KM[i], "long": LONG[i],
                 "sess": SESS[i], "down": down, "phase": phase(i), "focus": FOCUS[i],
                 "pct": round(100 * KM[i] / prog[i]["km"])})
    print(f"{i+1:2d} {mon.strftime('%d/%m')}-{sun.strftime('%d/%m')} {prog[i]['km']:6.1f}  "
          f"{KM[i]:5d}  {100*KM[i]/prog[i]['km']:3.0f}%  {SESS[i]:3d}  {LONG[i]:7}  "
          f"{phase(i)}{'  (ned)' if down else ''}")

up = [(i+1, KM[i]) for i in range(20) if i not in DOWN and i < 18]
print("\nUppveckornas progression (det som faktiskt räknas):")
print("  " + " → ".join(f"{k}" for _, k in up))
steps = [100*(up[j][1]/up[j-1][1]-1) for j in range(1, len(up))]
print(f"  steg: min {min(steps):+.0f} %, max {max(steps):+.0f} %, snitt {sum(steps)/len(steps):+.1f} %")
print(f"\nTotal: {sum(KM)} km + måldag 21,1  (originalet {sum(w['km'] for w in prog):.0f} km = "
      f"{100*sum(KM)/sum(w['km'] for w in prog):.0f} %)")
print(f"Snitt: {sum(KM)/20:.1f} km/v   Topp: {max(KM)} km (v{KM.index(max(KM))+1})")
rec=[i+1 for i,v in enumerate(LONG) if v>10.8][0]
print(f"Långpass: {LONG[0]} → {LONG[-2]} km, passerar rekordet 10,8 km i vecka {rec}")
print(f"Vecka 1: {START}  ·  Måldag: {START+dt.timedelta(weeks=19, days=5)}")

json.dump(rows, open("/tmp/claude-0/-home-user-airfoil-vv/e0d67b19-fb3a-5005-9f31-03d2385f9eca/scratchpad/plan20.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
