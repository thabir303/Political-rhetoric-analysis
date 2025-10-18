#!/usr/bin/env python3
"""
Verify categorization test results after fix
"""
import sys
import json
import requests

response = requests.get("http://localhost:8000/api/v1/parties/categorization-test?limit=50")
data = response.json()

print("=== Party Figure Breakdown (After Fix) ===")
print(json.dumps(data['party_figure_breakdown'], indent=2, ensure_ascii=False))

print("\n=== Verification ===")
incorrect = 0
for party, figures in data['party_figure_breakdown'].items():
    correct_figures = data['correct_mapping'].get(party, [])
    wrong = [f for f in figures if f not in correct_figures]
    
    if wrong:
        print(f"\n❌ {party} has incorrect figures: {wrong}")
        print(f"   Should only have: {correct_figures}")
        incorrect += 1
    else:
        print(f"✅ {party} - All figures correct ({len(figures)} figures)")

print(f"\n{'='*60}")
print(f"Total parties checked: {len(data['party_figure_breakdown'])}")
print(f"Parties with issues: {incorrect}")
print(f"Parties correct: {len(data['party_figure_breakdown'])-incorrect}")
print(f"{'='*60}")
