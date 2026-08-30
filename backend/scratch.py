import re
from bs4 import BeautifulSoup

with open("backend/data/raw/hdfc_mid_cap_fund_2026-08-30.html", "r") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

for h2 in soup.find_all(['h2', 'h1', 'h3', 'div']):
    text = h2.get_text(strip=True)
    if len(text) < 100:
        if any(keyword in text for keyword in ['About', 'Fund Details', 'NAV', 'Tax', 'Exit Load', 'Expense Ratio']):
            print(f"Tag: {h2.name}, Class: {h2.get('class')}, Text: {text[:50]}")
