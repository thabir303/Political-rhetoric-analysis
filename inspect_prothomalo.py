"""
Inspect actual HTML structure of Prothom Alo
"""

import requests
from bs4 import BeautifulSoup

url = "https://www.prothomalo.com/politics"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

print(f"Fetching: {url}\n")
response = requests.get(url, headers=headers)

print(f"Status Code: {response.status_code}")
print(f"Content Length: {len(response.content)} bytes\n")

soup = BeautifulSoup(response.content, 'html.parser')

# Save HTML for inspection
with open('/tmp/prothomalo_page.html', 'w', encoding='utf-8') as f:
    f.write(soup.prettify())
print("✓ Saved HTML to /tmp/prothomalo_page.html\n")

# Look for all divs with classes
print("=" * 80)
print("ALL DIV CLASSES (first 50):")
print("=" * 80)
divs = soup.find_all('div', class_=True)
unique_classes = set()
for div in divs[:100]:
    classes = div.get('class', [])
    if classes:
        for cls in classes:
            unique_classes.add(cls)

for cls in sorted(list(unique_classes))[:50]:
    print(f"  - {cls}")

print(f"\nTotal unique classes: {len(unique_classes)}")

# Look for article/story related classes
print("\n" + "=" * 80)
print("ARTICLE/STORY RELATED CLASSES:")
print("=" * 80)
keywords = ['story', 'article', 'card', 'news', 'item', 'post', 'headline', 'title']
for cls in sorted(unique_classes):
    if any(keyword in cls.lower() for keyword in keywords):
        print(f"  - {cls}")

# Look for all links
print("\n" + "=" * 80)
print("ALL LINKS (first 30):")
print("=" * 80)
links = soup.find_all('a', href=True)
for i, link in enumerate(links[:30], 1):
    href = link.get('href')
    text = link.get_text(strip=True)[:50]
    print(f"{i:2}. {href[:80]}")
    if text:
        print(f"    Text: {text}")

# Look for specific patterns in links
print("\n" + "=" * 80)
print("LINKS WITH /politics/ OR /opinion/ PATTERN:")
print("=" * 80)
political_links = [link for link in links if '/politics/' in link.get('href', '') or '/opinion/' in link.get('href', '')]
for i, link in enumerate(political_links[:20], 1):
    print(f"{i}. {link.get('href')}")
    text = link.get_text(strip=True)
    if text:
        print(f"   {text[:80]}")
