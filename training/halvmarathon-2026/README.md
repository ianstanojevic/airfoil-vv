# adidas Stockholm Halvmarathon 2026 — agentisk träningsplan

Personligt sidoprojekt, orelaterat till airfoil-vv:s kod. Ligger här bara för att
sessionen skapades från det här repot.

## Vad det är

En mobil dashboard som kopplar ihop två källor:

1. **Grundprogrammet** — marathon.se:s 20-veckorsprogram "adidas Stockholm
   Halvmarathon 1.40" (881 km), skrapat i sin helhet.
2. **Faktisk fysiologi** — COROS MCP: återhämtning, träningsbelastning, vilopuls,
   sömn och varje uppladdat pass.

Programmet körs som en 20-veckors uppbyggnad från **17 augusti 2026**, måldag
lördag 2 januari 2027. Loppet 29 augusti 2026 springs inte.

Grundprogrammet startar på 30 km/vecka och sätter "distans lätt" till 5:15/km.
Faktiskt utgångsläge är 7,4 km/vecka, längsta pass 10,8 km, tröskelfart 5:05/km
— alltså fyra gånger volymen i en fart som ligger vid tröskeln. Planen behåller
därför programmets struktur (passtyper, veckorytm, introduktionsordning) men

- skalar volymen till 15 → 48 km över 20 veckor (586 km, 67 % av originalet),
  med uppveckesteg på 4–15 % och nedvecka var fjärde,
- låter långpasset gå 7 → 20 km, förbi nuvarande rekord i vecka 7,
- översätter varje fartangivelse till zoner härledda ur uppmätt tröskelfart,
- justerar pass och veckovolym efter dagsform via ett explicit regelverk.

## Filer

| Fil | Vad den gör |
|---|---|
| `scrape.py` | Hämtar alla 20 veckor från trana.marathon.se → `program.json` |
| `program.json` | Hela grundprogrammet: 20 veckor, pass för pass |
| `plan20.py` | Bygger den anpassade 20-veckorskurvan → `plan20.json` |
| `plan20.json` | Veckovolym, långpass, antal pass, fas och fokus per vecka |
| `derive.py` | Veckovolym plan/faktisk, tempozoner ur tröskelfart, mellantider |
| `dashboard.html` | Dashboarden. Fristående — all data inbäddad, inga externa beroenden |

## Köra om

```bash
python3 scrape.py    # skriver program.json
python3 plan20.py    # skriver plan20.json + skriver ut progressionen
python3 derive.py    # skriver derived.json + sammanfattning av utgångsläget
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
