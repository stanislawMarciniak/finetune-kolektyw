"""Klasyfikator zakresu zadania bez modelu: historia Polski czy powszechna (router T3, bramka RAG, statystyki)."""

import re

CITATION = re.compile(r"(?:Za|Na podstawie|Źródło)\s*:[^\n]{0,250}|"
                      r"(?:Warszawa|Kraków|Wrocław|Poznań|Lublin|Łódź|Gdańsk|Katowice|Toruń|Olsztyn|Białystok|Rzeszów|"
                      r"Kielce|Opole|Londyn|Paryż|Berlin|Wiedeń|Oxford|London|Paris|New York|Bydgoszcz|Częstochowa)"
                      r"[\s,]*(?:\d{4}(?:[–-]\d{2,4})?)|\bs\.\s*\d+(?:[–-]\d+)?|\bt\.\s*[IVX\d]+|https?://\S+|dostęp[^\n]{0,40}")
POLAND = re.compile(r"Polsk|Polak|Polacy|Rzeczpospolit|Piast|Jagiell|Krak|Warszaw|sejm|szlacht|PRL|Solidarno|"
                    r"Piłsud|Gomułk|Gierk|Mieszk|Chrobr|Kościuszk|zabor|Galicj|Litw", re.I)


def scope_of(text):
    """'Polska' albo 'powszechna'; przypisy (miasto i rok wydania, adresy) są pomijane, bo „Warszawa 2004” nic nie mówi o treści."""
    return "Polska" if POLAND.search(CITATION.sub(" ", text)) else "powszechna"


def item_scope(item):
    return scope_of(f"{item.get('question', '')} {item.get('source_text', '')}")
