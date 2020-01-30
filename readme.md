# Triviamasters
Gemaakt door Nathan van Zeevenhoven, Max Nes en Luuk Bruins.

## Features:
De features op deze site zijn:
Om te beginnen kan je op de site een account aanmaken, inloggen en uitloggen.
Wanneer er verkeerde gegevens ingevuld worden hebben we doormiddel van javascript een popup toegevoegd. Dit zijn de check routes.
Deze zijn niet alleen voor de login en register pagina gemaakt maar ook voor alle games, dus wanneer je bijvoorbeeld geen code hebt
ingevuld bij het joinen van een online spel.
Qua spellen hebben we drie verschillende gamemodes op onze site:

 1: Singlesplayer mode: Speel in je eentje een trivia quiz van 10 vragen waarna je op het einde de score kan zien.
 2: Multiplayer mode with code: Speel op 2 verschillende beeldschermen tegen elkaar ZONDER dat je een account nodig hebt.
 De speler die het spel aanmaakt krijgt na het aanmaken van het spel een code te zien (dit wordt automatisch gegenereerd).
 Iemand anders kan deze code dan invullen en het spel meespelen Degene die het spel aanmaakt kan ook zelf het aantal vagen bepalen.
 Dit aantal ligt tussen de 1 en 100 vragen. Na het spelen van het spel komen de spelers op een result pagina die elke 5 seconden
 automatisch gerefresht wordt( Dit wordt gedaan in result.html). Op deze pagina kunnen zij zien wie er gewonnen heeft.
 3: Multiplayer with friend: Deze gamemode is zo gemaakt dat je niet op de site hoeft te blijven om een spel te bewaren.
 Je nodigt een vriend uit om een potje te spelen. Deze game bestaat uit 4 rondes van 10 vragen. Na elke ronde wordt je terug verwezen
 naar je persoonlijke userpage waar je er zelf voor kan kiezen om door te spelen. Je kan door naar de volgende ronde als de andere
 speler de ronde ook heeft gespeeld. Is dit niet het geval dan zal er een popup verschijnen.

 Multiplier:
 Om onze spellen unieker te maken hebben we een multiplier toegevoegd aan alle drie de gamemodes. Dit houdt in dat wanneer een speler,
 vanaf drie achter elkaar goed beantwoorde vragen in plaats van 1 punt per vraag 2 punten per vraag krijgt. Wanneer de speler een fout
 antwoord geeft is de streak weer 0 dus moet de speler eerst weer drie vragen achter elkaar goed beantwoorden.

 Vragen:
 De vragen worden uit een api gehaald. We hebben 4 verschillende categorieën waarover vragen zijn. Deze vragen worden steeds random
 gegenereert. Dus de ene vraag kan over dieren gaan en de andere over geschiedenis.

 Naast de gamemodes bevat Triviamasters nog een aantal gamemodes.
 userpage:
 1: hier worden je huidige games vertoond. Je kan hier de huidige ronde, jouw score en de score van de tegenstander zien.
 2: Ook kan je vanaf hier het spel doorspelen door op de play button te klikken. Je zal dan de volgende ronde van het spel kiezen.
 3: Naast het doorspelen van het spel kan er gekozen worden om een spel te verwijderen met de delete button.
 4: Naast de huidige games, worden ook de spellen weergegeven die beëindigd zijn. Je kan de tegenstander en de eindstand zien

 friendpage:
 1: Op deze pagina kan je vrienden toevoegen en vrienden verwijderen.
 2: Onder de forms van het toevoegen en verwijderen van vrienden staat een tabel met al je vrienden, hoeveel potten je met ze gespeeld
 hebt, en hoeveel je gewonnen en verloren heb van die vrienden.

 leaderboard:
 1: Op deze pagina wordt de all time leaderboard weergegeven van de top 10 hoogste scores die behaalt zijn met de friend game mode.

 How to play:
 Voor nieuwe gebruikers hebben we een gebruikshandleiding toegevoegd. Op deze manier is het voor nieuwe gebruikers makkelijker om de
 site te gebruiken.

Extra functies:
Onze vragen worden via een api opgehaald, Omdat dit op drie verschillende plekken wordt gedaan hebben wij er een helpersfunctie van
gemaakt in helpers.py, genaamd vragen().
Hier wordt uit 4 categorieën, één categorie gekozen en daarna een random vraag uit die categorie. De gegevens uit deze api worden
met return meegegeven.

Ook vragen we heel vaak de username uit de users database op d.m.v de session id. Hiervoor hebben wij ook een functie gemaakt
in helpers.py (user). Deze functie returnt de username.

Als laatste hebben we een functie gemaakt die de gegevens van een bepaalde user in de table users meegeeft. Dit wordt bijvoorbeeld
gebruikt om te kijken of username al bestaat. Aan de functie wordt de username meegegeven en de gehele rij van die username wordt
gereturnd.


Taakverdeling:
Deze taakverdeling is niet 100% juist, omdat we heel veel samen gewerkt hebben of meerdere mensen hebben aan een bepaald deel gewerkt.

checks: Max
Index: Luuk en Max
Userpage: Luuk
Style: Nathan
friendspage: Nathan
How to play: Nathan
SpelWithFriend: Luuk
Singleplayer: Luuk en Nathan
Spelmetcode: Max
Leaderbord: Luuk
login: Max
Registratie: Max
logout: Max


![Image of Homepage](https://github.com/Hetgithubaccount/triviamasters/blob/master/static/homepage.PNG)

![Link to Youtube video](https://youtu.be/bRA2KHD3bcI)



