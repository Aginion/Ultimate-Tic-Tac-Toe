# Ultimate Tic-Tac-Toe Bot 

Rozwiązanie algorytmiczne zadania **Tic-Tac-Toe** (Ultimate Tic-Tac-Toe) dostępnego na platformie [CodinGame](https://www.codingame.com/ide/puzzle/tic-tac-toe).

Celem projektu było stworzenie bota, który potrafi pokonać wbudowane AI przeciwnika, wykorzystując zaawansowane algorytmy przeszukiwania drzewa gry.

## Opis Zadania

Gra to **Ultimate Tic-Tac-Toe** (Strategiczne Kółko i Krzyżyk). Rozgrywka toczy się na dużej planszy 9x9, która podzielona jest na 9 mniejszych plansz 3x3.
* Wygrywając małą planszę, przejmujesz odpowiednie pole na dużej planszy.
* Kluczowa zasada: Twój ruch na małej planszy determinuje, na której z 9 małych plansz musi zagrać przeciwnik w następnej turze.
* Celem jest ułożenie linii z trzech wygranych małych plansz.

## Zastosowane Algorytmy

Bot został napisany w języku **Python** i opiera się na klasycznych algorytmach sztucznej inteligencji dla gier bez losowości z pełną informacją:

### 1. Minimax
Podstawą działania bota jest algorytm **Minimax**, który rekurencyjnie analizuje drzewo możliwych ruchów. Algorytm zakłada, że przeciwnik zawsze gra optymalnie (stara się zminimalizować nasz zysk), a my staramy się go zmaksymalizować.

### 2. Alpha-Beta Pruning (Przycinanie Alfa-Beta)
Aby przyspieszyć działanie Minimaxa, zastosowano optymalizację **Alpha-Beta**. Pozwala ona na odcinanie gałęzi drzewa gry, które na pewno nie zostaną wybrane (ponieważ znaleziono już lepszą alternatywę w innej gałęzi). Dzięki temu bot może przeszukać głębiej w tym samym czasie.

### 3. Iterative Deepening (Pogłębianie Iteracyjne)
Ze względu na limity czasowe na CodinGame (zazwyczaj 100ms na ruch), bot nie może przeszukać drzewa do końca. Zastosowano **Iterative Deepening**:
* Bot najpierw szuka najlepszego ruchu na głębokości 1.
* Następnie na głębokości 2, 3 itd.
* Jeśli czas się kończy (`TIME_LIMIT`), obliczenia są przerywane, a bot zwraca najlepszy wynik z ostatniej w pełni obliczonej głębokości.

### 4. Funkcja Heurystyczna (Evaluation Function)
Ponieważ bot rzadko widzi "mat" (koniec gry) w kilku ruchach, stan planszy jest oceniany heurystycznie:
* Punkty za wygrane małe plansze.
* Punkty za posiadanie 2 znaków w linii (szansa na wygraną).
* Punkty za blokowanie przeciwnika.
* Strategiczne pozycjonowanie (bonusy za środek i rogi małych plansz).
* Bonusy za kierowanie gry na nieukończone plansze (utrzymywanie inicjatywy).

## Struktura Kodu

* `Config`: Klasa konfiguracyjna (czasy, głębokość, nagrody).
* `GameBoard`: Logika pojedynczej planszy 3x3.
* `UltimateBoard`: Logika całej planszy 9x9 oraz mechanika wymuszania ruchu ("next board").
* `minimax`: Główna funkcja rekurencyjna.
* `game_loop`: Pętla obsługująca wejście/wyjście zgodne ze standardem CodinGame.

## Jak użyć

1.  Skopiuj cały kod z pliku głównego (`main.py` / `solution.py`).
2.  Wejdź na stronę zadania: [CodinGame Tic-Tac-Toe](https://www.codingame.com/ide/puzzle/tic-tac-toe).
3.  Wklej kod do edytora online.
4.  Wybierz język **Python 3**.
5.  Uruchom testy ("Play all testcases") lub wyślij rozwiązanie.

## Dowody na awans do ligi brązowej i srebrnej

<img width="834" height="793" alt="Screenshot 2026-01-16 at 09 50 03" src="https://github.com/user-attachments/assets/f02ab6c0-ca76-403d-aed1-824a218146ac" />
<img width="843" height="793" alt="Screenshot 2026-01-16 at 10 17 07" src="https://github.com/user-attachments/assets/84d0f837-5d48-4121-a7cf-9f4e172185b5" />

---
*Autorzy: Agata "Aginion" Poprawka, Ignacy "Inowaq" Nowak*
