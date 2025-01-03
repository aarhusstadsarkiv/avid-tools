---
title: search
layout: default
parent: Kommandoer
nav_order: 7
---

```shell
Usage: avid-tools search [OPTIONS] PATTERN...

  Søg PATTERN i tabel rækker i Tables.

  PATTERN skal være i SQL LIKE format (% til nul eller flere bogstaver og _
  til nul eller et bogstav). Flere PATTERN kan bruges og matches med "eller"
  logik (dvs. PATTERN et, eller PATTERN to, eller PATTERN tre, osv.).

  Som default søges PATTERN i alle tabeller og kolonner. --table kan bruges
  til at begrænse søgning til bestemte tabeller. --column kan bruges til at
  begrænse søgning til bestemte kolloner i bestemte tabeller. Både --table og
  --column kan bruges samtidig.

Options:
  -t, --table ID                  Vælg søgetabeller.  [x>=1]
  -c, --column TABLE_ID COLUMN_ID
                                  Vælg søgekolonner i tabeller.
  --limit INTEGER                 Begræns hvor mange resultater vises.  [x>=1]
  --show-columns / --show-rows    Vis alle kolonner i matchende rækker eller
                                  kun rækkenumre.
  -h, --help                      Vis denne besked og afslut.
```