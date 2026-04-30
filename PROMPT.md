<!-- DATA2PROMPT_GENERATED_CONTENT -->

# codebase: Advanced-EDA

## purpose: 
This document is a structured representation of a codebase and data schema. It is designed to be consumed by a Large Language Model.
The output is organized into sections:
1. Directory Structure: List of all files in this project.
2. Files: The content of each file, clearly labeled with its path using '## File: {path}' headers.
For all standard files, content is wrapped in markdown code blocks using dynamic backtick depth to ensure robust nesting.
For notebooks, individual cells are clearly labeled with cell numbers, types, and their respective file paths.
For Excel files, individual sheets are clearly labeled with sheet names, numbers, and their respective file paths.

> Generated on: 2026-04-29 22:28
> Tokens: 2236 (est. via regex_fallback)

# Directory Structure
```text
.gitignore
README.md
data\appearances.csv
data\clubs.csv
data\competitions.csv
data\game_events.csv
data\games.csv
data\players.csv
notebooks\test.ipynb
utils\__init__.py
```

# Files

This section contains the contents of the repository's files.

## File: .gitignore
```text
.env

__pycache__/

```

## File: README.md
```markdown
# Advanced-EDA
```

## File: data\appearances.csv
-- [Sample - Random 15 rows] --
|   appearance_id |   game_id |   player_id |   yellow_cards |   red_cards |   goals |   assists |   minutes_played |
|----------------:|----------:|------------:|---------------:|------------:|--------:|----------:|-----------------:|
|  3451377_199369 |   3451377 |      199369 |              0 |           0 |       0 |         0 |               59 |
|  3613113_179184 |   3613113 |      179184 |              0 |           0 |       0 |         0 |               51 |
|  3886690_278359 |   3886690 |      278359 |              0 |           0 |       0 |         0 |               18 |
|   3845058_54906 |   3845058 |       54906 |              0 |           0 |       0 |         0 |               33 |
|  3860236_234189 |   3860236 |      234189 |              0 |           0 |       1 |         0 |               90 |
|  3415384_140786 |   3415384 |      140786 |              0 |           0 |       0 |         0 |               55 |
|  4094700_325223 |   4094700 |      325223 |              0 |           0 |       0 |         0 |                4 |
|  3415392_314137 |   3415392 |      314137 |              1 |           0 |       0 |         0 |               69 |
|  3852715_127573 |   3852715 |      127573 |              0 |           0 |       0 |         0 |               90 |
|  3851287_121570 |   3851287 |      121570 |              0 |           0 |       0 |         0 |               90 |
|  3451377_531829 |   3451377 |      531829 |              0 |           0 |       0 |         0 |               31 |
|  3614830_398808 |   3614830 |      398808 |              0 |           0 |       0 |         0 |               21 |
|  4103650_181136 |   4103650 |      181136 |              0 |           0 |       0 |         0 |               71 |
|  3621397_203348 |   3621397 |      203348 |              1 |           0 |       0 |         0 |               90 |
|  3844786_610442 |   3844786 |      610442 |              0 |           0 |       0 |         0 |               34 |
-- [CSV truncated: Showing random 15 rows to save context] --


## File: data\clubs.csv
-- [Sample - Random 15 rows] --
|   club_id | name                                           | domestic_competition_id   |   squad_size |   foreigners_number |   national_team_players | stadium_name              |   stadium_seats | net_transfer_record   |
|----------:|:-----------------------------------------------|:--------------------------|-------------:|--------------------:|------------------------:|:--------------------------|----------------:|:----------------------|
|       533 | TSG 1899 Hoffenheim Fußball-Spielbetriebs GmbH | L1                        |           28 |                  12 |                      12 | PreZero Arena             |           30150 | -6.55m                |
|     14589 | FC Orenburg                                    | RU1                       |           29 |                  14 |                       5 | Gazovik                   |           10046 | -3.08m                |
|        42 | Hannover 96                                    | L1                        |           28 |                   6 |                       1 | Heinz-von-Heiden-Arena    |           49000 | -300k                 |
|       336 | Sporting Clube de Portugal                     | PO1                       |           26 |                  14 |                       7 | Estádio José Alvalade XXI |           50095 | +62.05m               |
|      3725 | RFK Akhmat Grozny                              | RU1                       |           27 |                  13 |                       6 | Akhmat-Arena              |           30200 | -2.05m                |
|      9007 | Arsenal Kyiv                                   | UKR1                      |            0 |                   0 |                       0 | NSK Olimpisky             |           70050 | +-0                   |
|      1041 | Olympique Lyonnais                             | FR1                       |           28 |                  19 |                       9 | Groupama Stadium          |           59186 | +31.99m               |
|       825 | Eskisehirspor                                  | TR1                       |           41 |                   1 |                       0 | Eskişehir Yeni Stadyum    |           34930 | +-0                   |
|      4083 | FC Crotone                                     | IT1                       |           25 |                   6 |                       1 | Ezio Scida                |           16640 | +3.90m                |
|      1148 | Brentford Football Club                        | GB1                       |           30 |                  23 |                      18 | Gtech Community Stadium   |           17250 | -62.26m               |
|       290 | AJ Auxerre                                     | FR1                       |           26 |                  15 |                       6 | Stade de l'Abbé-Deschamps |           18541 | +-0                   |
|       995 | Football Club de Nantes                        | FR1                       |           25 |                  13 |                       9 | Stade de la Beaujoire     |           37463 | +10.85m               |
|       403 | Willem II Tilburg                              | NL1                       |           27 |                   7 |                       0 | Koning Willem II Stadion  |           14700 | +385k                 |
|        39 | 1. Fußball- und Sportverein Mainz 05           | L1                        |           27 |                  11 |                       6 | Mewa Arena                |           33305 | +13.55m               |
|       566 | Beerschot AC                                   | BE1                       |            0 |                   0 |                       0 | Olympisch Stadion         |           12771 | +-0                   |
-- [CSV truncated: Showing random 15 rows to save context] --


## File: data\competitions.csv
-- [Sample - Random 15 rows] --
| competition_id   | name                                        | type              | country_name   |
|:-----------------|:--------------------------------------------|:------------------|:---------------|
| EL               | europa-league                               | international_cup | nan            |
| POCP             | allianz-cup                                 | domestic_cup      | Portugal       |
| GBCS             | community-shield                            | other             | England        |
| USC              | uefa-super-cup                              | other             | nan            |
| DFB              | dfb-pokal                                   | domestic_cup      | Germany        |
| ECLQ             | uefa-europa-conference-league-qualifikation | international_cup | nan            |
| RUSS             | russian-super-cup                           | other             | Russia         |
| PO1              | liga-portugal-bwin                          | domestic_league   | Portugal       |
| FR1              | ligue-1                                     | domestic_league   | France         |
| POSU             | supertaca-candido-de-oliveira               | other             | Portugal       |
| DK1              | superligaen                                 | domestic_league   | Denmark        |
| RU1              | premier-liga-russia                         | domestic_league   | Russia         |
| DFL              | dfl-supercup                                | other             | Germany        |
| UKRS             | ukrainian-super-cup                         | other             | Ukraine        |
| FAC              | fa-cup                                      | domestic_cup      | England        |
-- [CSV truncated: Showing random 15 rows to save context] --


## File: data\games.csv
-- [Sample - Random 15 rows] --
|   game_id | competition_id   |   season | date       |   home_club_id |   away_club_id |   home_club_goals |   away_club_goals | stadium                                          |   attendance |
|----------:|:-----------------|---------:|:-----------|---------------:|---------------:|------------------:|------------------:|:-------------------------------------------------|-------------:|
|   4109526 | PO1              |     2023 | 2024-01-28 |           2424 |           2420 |                 1 |                 0 | Estádio Cidade de Barcelos                       |         7617 |
|   3860256 | TR1              |     2022 | 2022-10-07 |           2832 |           3840 |                 1 |                 1 | Kalyon Stadyumu                                  |         6697 |
|   3851107 | BE1              |     2022 | 2023-02-04 |            475 |            601 |                 1 |                 0 | Stayen                                           |         3200 |
|   3886642 | ES1              |     2022 | 2023-04-25 |            150 |            681 |                 0 |                 0 | Benito Villamarín                                |        42294 |
|   3427097 | TR1              |     2020 | 2021-03-21 |            114 |             36 |                 1 |                 1 | Vodafone Park                                    |          nan |
|   3427066 | TR1              |     2020 | 2021-03-04 |             36 |            589 |                 1 |                 1 | Ülker Stadyumu FB Şükrü Saraçoğlu Spor Kompleksi |          nan |
|   3432189 | PO1              |     2020 | 2021-04-22 |            720 |           2420 |                 1 |                 0 | Estádio do Dragão                                |          nan |
|   3394651 | FR1              |     2020 | 2020-11-01 |            618 |            969 |                 0 |                 1 | Stade Geoffroy-Guichard                          |          nan |
|   4129675 | TR1              |     2023 | 2024-02-24 |             36 |          10484 |                 2 |                 1 | Ülker Stadyumu FB Şükrü Saraçoğlu Spor Kompleksi |        40094 |
|   4095276 | GB1              |     2023 | 2024-01-21 |            989 |             31 |                 0 |                 4 | Vitality Stadium                                 |        11228 |
|   3589262 | FR1              |     2021 | 2021-12-01 |            583 |            417 |                 0 |                 0 | Parc des Princes                                 |        47502 |
|   3461712 | CL               |     2020 | 2020-10-21 |            418 |            660 |                 2 |                 3 | Estadio Alfredo Di Stéfano                       |          nan |
|   4096256 | L1               |     2023 | 2024-05-11 |              3 |             89 |                 3 |                 2 | RheinEnergieSTADION                              |        50000 |
|   3602569 | RU1              |     2021 | 2022-03-14 |           2698 |           1083 |                 1 |                 2 | Ak Bars Arena                                    |         3344 |
|   4113170 | ES1              |     2023 | 2023-09-16 |           1049 |             13 |                 3 |                 0 | Mestalla                                         |        45362 |
-- [CSV truncated: Showing random 15 rows to save context] --


## File: data\game_events.csv
-- [Sample - Random 15 rows] --
|   game_event_id |   game_id |   minute | type          |   player_id |   player_in_id |   player_assist_id |
|----------------:|----------:|---------:|:--------------|------------:|---------------:|-------------------:|
|         4930789 |   4120772 |       79 | Substitutions |      656172 |         212243 |                nan |
|         8592472 |   3607589 |       46 | Substitutions |      676318 |         341278 |                nan |
|         6482106 |   3890218 |       76 | Substitutions |      225744 |         334964 |                nan |
|         5391928 |   4096031 |       46 | Substitutions |      177779 |         188888 |                nan |
|         5962476 |   3589460 |       88 | Substitutions |       37647 |         127048 |                nan |
|         4794103 |   3851082 |       84 | Substitutions |      381963 |         909737 |                nan |
|         2491908 |   4094836 |       88 | Substitutions |      594997 |         354666 |                nan |
|         2557881 |   3464294 |       90 | Substitutions |      255451 |         333802 |                nan |
|         3493977 |   4120728 |       75 | Substitutions |       99863 |         892054 |                nan |
|         3078740 |   3886606 |       90 | Substitutions |      165007 |         570421 |                nan |
|         8853205 |   4098205 |       67 | Cards         |      314915 |            nan |                nan |
|         7484964 |   3651136 |        3 | Goals         |      355861 |            nan |                nan |
|         9850946 |   4113018 |       78 | Substitutions |      251876 |         245078 |                nan |
|         4455802 |   4112925 |       76 | Substitutions |      153238 |         537762 |                nan |
|         1080863 |   4062347 |       89 | Goals         |      251676 |            nan |                nan |
-- [CSV truncated: Showing random 15 rows to save context] --


## File: data\players.csv
-- [Sample - Random 15 rows] --
|   player_id |   current_club_id | player_code             | country_of_birth   | city_of_birth      | country_of_citizenship   | date_of_birth   | sub_position       | position   | foot   |   height_in_cm | contract_expiration_date   |
|------------:|------------------:|:------------------------|:-------------------|:-------------------|:-------------------------|:----------------|:-------------------|:-----------|:-------|---------------:|:---------------------------|
|      314371 |              2578 | jahmal-hector-ingram    | England            | London             | England                  | 1998-11-11      | Centre-Forward     | Attack     | right  |            180 | nan                        |
|      479634 |              3329 | saldanha                | Portugal           | Guimarães          | Portugal                 | 2001-03-19      | Right-Back         | Defender   | right  |            176 | 2025-06-30                 |
|      296802 |               383 | walter-benitez          | Argentina          | General San Martín | Argentina                | 1993-01-19      | Goalkeeper         | Goalkeeper | right  |            191 | 2025-06-30                 |
|      247555 |                39 | edimilson-fernandes     | Switzerland        | Sion               | Switzerland              | 1996-04-15      | Centre-Back        | Defender   | right  |            187 | 2026-06-30                 |
|      229857 |              3060 | bright-edomwonyi        | Nigeria            | Benin City         | Nigeria                  | 1994-07-24      | Centre-Forward     | Attack     | right  |            186 | 2024-06-30                 |
|      565017 |              2861 | louis-broche            | nan                | nan                | Belgium                  | 2001-05-04      | Left-Back          | Defender   | nan    |            nan | 2023-06-30                 |
|      522715 |              2424 | joao-caiado             | Portugal           | Viseu              | Portugal                 | 1999-04-20      | Attacking Midfield | Midfield   | right  |            178 | 2023-06-30                 |
|       63459 |               173 | alexander-juel-andersen | Denmark            | Viborg             | Denmark                  | 1991-01-29      | Centre-Back        | Defender   | right  |            190 | 2023-12-31                 |
|      876725 |              2832 | onur-basyigit           | Türkiye            | Denizli            | Türkiye                  | 2004-06-12      | Left-Back          | Defender   | left   |            177 | 2025-06-30                 |
|      226026 |               317 | xandro-schenk           | Netherlands        | Almere             | Netherlands              | 1993-04-28      | Centre-Back        | Defender   | left   |            187 | 2024-06-30                 |
|       94771 |                89 | andreas-voglsammer      | Germany            | Rosenheim          | Germany                  | 1992-01-09      | Centre-Forward     | Attack     | right  |            177 | 2024-06-30                 |
|      914046 |              2715 | noah-serwy              | nan                | nan                | Belgium                  | 2003-02-21      | Second Striker     | Attack     | right  |            168 | 2024-06-30                 |
|      422763 |               124 | nicolas-raskin          | Belgium            | Liège              | Belgium                  | 2001-02-23      | Central Midfield   | Midfield   | right  |            178 | 2027-05-31                 |
|      238084 |               202 | ramon-pascal-lundqvist  | Sweden             | Algutsrum          | Sweden                   | 1997-05-10      | Attacking Midfield | Midfield   | right  |            183 | 2023-12-31                 |
|      552425 |               331 | jon-moncayola           | Spain              | Garinoain          | Spain                    | 1998-05-13      | Central Midfield   | Midfield   | right  |            182 | 2031-06-30                 |
-- [CSV truncated: Showing random 15 rows to save context] --


## File: notebooks\test.ipynb
### Cell 1 (code) - notebooks\test.ipynb
```python
import psycopg2
from psycopg2 import sql
import pandas as pd

```

### Cell 2 (code) - notebooks\test.ipynb
```python
config = {
    'user': 'postgres',
    'password': 'root',
    'host': 'localhost',
    'port': 5432,
    'dbname': 'postgres'  
}
```


## File: utils\__init__.py
```py

```
