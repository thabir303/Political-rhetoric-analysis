#!/usr/bin/env python3
import requests
import json

response = requests.get("http://localhost:8000/api/v1/parties/categorization-test?limit=10")
data = response.json()

print("Checking Articles 3-7:")
for i in range(2, 7):
    art = data['articles'][i]
    print(f"\nArticle {i+1}:")
    print(f"  Title: {art['title'][:60] if art['title'] else 'NO TITLE'}")
    print(f"  People: '{art['people']}'")
    print(f"  Parties: '{art['parties']}'")
    print(f"  Date: {art.get('date', 'NO DATE')}")
