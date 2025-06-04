# Statystyka-Projekt

Symulacja kolejki na stacji benzynowej

* 4 dystrybutory z możliwością obsługi paliwa typu A, B lub obydwu
* Każdy dystrybutor ma swoją mini kolejkę
* Gdy mini kolejki się zapełnią twoży się jedna wspólna kolejka która potem rozkłada się na mniejsze (w zależności o typu paliwa)
* Samochody przyjeższają w losowym interwale
* Samochód losowo (z określonym prawdopowobieństwem) potrzebuje paliwa typu A lub B
* Samochód dostaje losowy czas obsługi przy dystrybutorze
* Samochody automatycznie jadą do dystrybutora z odpowienim dla nich paliwe
* istnieje 10% szansy że kierowca się pomyli i przyjedzie do złego dystrybutora - w tedy wraca na koniec kolejki
* do zmiennej `stats` zapisywane są różne dane o symulacji
* w stałych na początku pliku `main.py` można dostosować wiele parametrów symulacji 

### Uruchomienie

- Wybierz parametry w pliku `main.py`

#### a) Proste uruchomienie symulacji i wyniki w formie csv:

- uruchom skrypt `main.py`

#### b) Uruchomienie z ładną wizualizacją jako backend + frontend

- uruchom skrypt `app.py`
- wejdź na stronę z frontendem: [https://g.co/gemini/share/cb943b49a9ca](https://g.co/gemini/share/cb943b49a9ca)
- powinno się od razu połączyć, jeśli nie - upewnij się że backend leci naporcie :5000


### TODO:

hipoteza zerowa i alternatywna, np: dotycząca czasu oczekiwania a rozkładu typu dystrybutorów
