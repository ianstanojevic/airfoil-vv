# adidas Stockholm Halvmarathon 2026 — agentisk träningsplan

Personligt sidoprojekt, orelaterat till airfoil-vv:s kod. Ligger här bara för att
sessionen skapades från det här repot.

## Vad det är

En mobil dashboard som kopplar ihop två källor:

1. **Programmet** — marathon.se:s 20-veckorsprogram "adidas Stockholm
   Halvmarathon 2.10" (483 km), skrapat i sin helhet. Övriga fyra nivåer är
   också skrapade, som underlag för nivåvalet nedan.
2. **Faktisk fysiologi** — COROS MCP: återhämtning, träningsbelastning, vilopuls,
   sömn och varje uppladdat pass.

Programmet är igång. Vecka 1 är **10–16 augusti 2026** och påbörjas torsdag
13 augusti — veckans tisdagspass ligger före startbeslutet och hoppas över, så
vecka 1 blir 9 km på två pass i stället för 13 km på tre. Vecka 2 börjar
måndag 17 augusti och därifrån följs programmet rakt av.

Måldag: **lördag 26 december 2026**, 21,1 km. Loppet 29 augusti 2026 springs inte.

## Nivåval

Marathon.se har fem nivåer. Jämförda mot utgångsläget (7,4 km/vecka i snitt,
bästa vecka 25,4 km, längsta pass 10,8 km, tröskelfart 5:05/km):

| Nivå | Fart | V1 | Snitt | Topp | Totalt | V1 mot snittet |
|---|---|---|---|---|---|---|
| 1.20 | 3:24 | 44 | 61,0 | 81 | 1220 | 5,9× |
| 1.30 | 4:16 | 40 | 56,2 | 79 | 1124 | 5,4× |
| 1.40 | 4:44 | 30 | 44,0 | 60 | 881 | 4,1× |
| **2.10** | **6:10** | **13** | **24,2** | **34** | **483** | **1,8×** |
| 2.45 | 7:49 | 8 | 20,0 | 32 | 401 | 1,1× |

**2.10 är vald nivå.** Vecka 1 på 13 km går att starta på, snittveckan (24 km)
motsvarar den bästa veckan hittills, och programmets "distans lätt" på
6:15–6:30/km ligger redan i den uppmätta lugna zonen — det körs alltså
oförändrat, utan omskalning. Alla fem nivåerna slutar ändå på samma långpass,
21,1 km.

Måltiden 2:10 är inte taket: Coros prognos är 1:55 i dag. Nivån väljs för
volymen, inte för tiden.

Enda ändringen mot programmet: vecka 1–4 anger "distans med gång" för
nybörjare — de springs hela, eftersom 10,8 km i sträck redan är gjort.

## Programmets faser

| Veckor | Fas | Volym | Innehåll |
|---|---|---|---|
| 1–4 | Grundvänjning | 13 → 19 km | Tre pass. Styrka från v2, koordinationslopp från v4. Långpass 5 → 7,5 km. |
| 5–8 | Löpning i sträck | 17 → 26 km | Gånginslagen bort. Intervaller, fartlek, snabbdistans. Långpass når 9 km. |
| 9–14 | Långpass och styrka | 22 → 34 km | Långpasset blir eget pass. Backlöpning, löpskolning. Volymtopp v13. |
| 15–18 | Tröskel och distans | 26 → 34 km | Tröskelpass från v15, långpass med fartökning från v17. Längsta passet 18 km i v18. |
| 19–20 | Nedtrappning | 22 → måldag | Volym ned, skärpa kvar. 26 december: 21,1 km. |

Långpasset går 5 → 18 km och passerar nuvarande rekord (10,8 km) i vecka 11.
Största enskilda steget är 3 km.

Vecka 20 landar 21–27 december, alltså måldag på annandag jul. En extra lugn
vecka i december flyttar den till 2 januari om det passar bättre.

`plan20.py` innehåller en tidigare omskalning av 1.40-programmet (15 → 48 km
över 20 veckor) och sparas som referens; den används inte.

## Filer

| Fil | Vad den gör |
|---|---|
| `scrape.py` | Hämtar 20 veckor för en nivå → `program.json` (1.40) |
| `scrape_all.py` | Hämtar alla fem nivåer → `all_levels.json` |
| `all_levels.json` | Samtliga fem program, pass för pass |
| `compare.json` | Nivåjämförelse: veckovolym, pass, långpass per nivå |
| `plan210.json` | 2.10 som 20-veckorsplan med datum från 10 aug |
| `plan20.py` / `plan20.json` | Tidigare omskalning av 1.40 — referens |
| `derive.py` | Tempozoner ur tröskelfart, plan mot faktiskt, mellantider |
| `body.html` / `app.js` | Dashboardens markup och logik |
| `dashboard.html` | Byggd dashboard. Fristående — all data inbäddad |

## Köra om

```bash
python3 scrape.py       # skriver program.json (1.40)
python3 scrape_all.py   # skriver all_levels.json (alla fem nivåer)
python3 derive.py       # tempozoner + utgångsläge
```

`dashboard.html` byggs genom att sätta ihop CSS, `body.html`, `app.js` och
JSON-datan; den incheckade filen är redan hopbyggd och öppnas direkt.

## Känt källfel

Marathon.se anger 211 km på 67 minuter för 1.20 vecka 4, måndag. Det är
uppenbart fel och räknas som 11 km i jämförelsen ovan.

## Begränsning

COROS-MCP:n är läsbehörig. Passen kan inte pushas ut till klockan automatiskt —
de får läggas in manuellt, eller så läses formen av och veckans pass skrivs
inför varje måndag.

## Datum

Coros-data avläst 12 augusti 2026: återhämtning 100 %, belastningskvot 0,40,
VO2max 53, tröskelfart 5:05/km. Tempozonerna är härledda ur tröskelfarten,
inte ur måltiden.
