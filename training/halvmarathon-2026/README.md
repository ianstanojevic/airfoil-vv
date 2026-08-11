# adidas Stockholm Halvmarathon 2026 — agentisk träningsplan

Personligt sidoprojekt, orelaterat till airfoil-vv:s kod. Ligger här bara för att
sessionen skapades från det här repot.

## Vad det är

En mobil dashboard som kopplar ihop två källor:

1. **Grundprogrammet** — marathon.se:s 20-veckorsprogram "adidas Stockholm
   Halvmarathon 1.40" (13 apr – 29 aug 2026, 881 km), skrapat i sin helhet.
2. **Faktisk fysiologi** — COROS MCP: återhämtning, träningsbelastning, vilopuls,
   sömn och varje uppladdat pass.

Programmet förutsätter 30–60 km/vecka. Faktiskt utfall sedan vecka 8 är 96 av
612 km (16 %), snitt 7,4 km/vecka, längsta pass 10,8 km. Dashboarden skriver
därför om målet från 1:39:52 (4:44/km) till 2:01 (5:45/km) och ersätter
vecka 18–20 med en plan byggd för den formen — plus ett regelverk som justerar
varje pass efter dagsform.

## Filer

| Fil | Vad den gör |
|---|---|
| `scrape.py` | Hämtar alla 20 veckor från trana.marathon.se → `program.json` |
| `program.json` | Hela grundprogrammet: 20 veckor, pass för pass |
| `derive.py` | Räknar veckovolym plan/faktisk, tempozoner ur tröskelfart, mellantider |
| `dashboard.html` | Dashboarden. Fristående — all data inbäddad, inga externa beroenden |

## Köra om

```bash
python3 scrape.py    # skriver program.json
python3 derive.py    # skriver derived.json + skriver ut sammanfattning
```

`dashboard.html` har datan inbäddad och öppnas direkt i en webbläsare.

## Begränsning

COROS-MCP:n är läsbehörig. Passen kan inte pushas ut till klockan automatiskt —
de får läggas in manuellt, eller så läses formen av och planen skrivs om inför
varje pass.

## Datum

Data avläst 11 augusti 2026. Tempozoner är härledda ur uppmätt tröskelfart
(5:05/km), inte ur måltiden — det är skillnaden mot grundprogrammet, där
farterna är satta för någon som redan springer 1.40.
