"""
Try to find Prothom Alo's API or data endpoints
"""

import requests
import json
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Check if they have an API endpoint pattern
# Many modern news sites use patterns like /api/collection/ or /api/stories/

potential_apis = [
    "https://www.prothomalo.com/api/v1/collections/politics",
    "https://www.prothomalo.com/api/collections/politics",
    "https://www.prothomalo.com/api/v1/stories?section=politics",
    "https://www.prothomalo.com/api/stories/politics",
    "https://www.prothomalo.com/web-api/politics",
    "https://www.prothomalo.com/collection/politics",
]

print("=" * 80)
print("TESTING API ENDPOINTS")
print("=" * 80)

for api_url in potential_apis:
    print(f"\nTrying: {api_url}")
    try:
        response = requests.get(api_url, headers=headers, timeout=5)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"  ✓ Success!")
            print(f"  Content-Type: {response.headers.get('Content-Type', 'unknown')}")
            print(f"  Content Length: {len(response.content)} bytes")
            
            # Try to parse as JSON
            try:
                data = response.json()
                print(f"  ✓ Valid JSON!")
                print(f"  Keys: {list(data.keys())[:10]}")
                
                # Save the response
                filename = f"/tmp/prothomalo_api_{len(potential_apis)}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"  Saved to {filename}")
                
            except:
                # Maybe HTML
                if 'html' in response.headers.get('Content-Type', ''):
                    soup = BeautifulSoup(response.content, 'html.parser')
                    links = soup.find_all('a', href=True)
                    print(f"  Found {len(links)} links in HTML")
                    
                    # Look for article links
                    article_links = [l for l in links if '/politics/' in l.get('href', '')]
                    if article_links:
                        print(f"  ✓ Found {len(article_links)} article links!")
                        for link in article_links[:5]:
                            print(f"    - {link.get('href')}")
        
    except Exception as e:
        print(f"  ✗ Error: {e}")

# Try the collection endpoint which often exists
print("\n" + "=" * 80)
print("TRYING /collection/latest ENDPOINT")
print("=" * 80)

try:
    url = "https://www.prothomalo.com/collection/latest"
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Save for inspection
        with open('/tmp/prothomalo_collection.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print("Saved to /tmp/prothomalo_collection.html")
        
        # Look for script tags with data
        scripts = soup.find_all('script')
        print(f"\nFound {len(scripts)} script tags")
        
        for i, script in enumerate(scripts):
            text = script.string
            if text and ('politics' in text.lower() or 'article' in text.lower() or '"stories"' in text):
                print(f"\n  Script {i} contains relevant data (first 500 chars):")
                print(f"  {text[:500]}")
                
except Exception as e:
    print(f"Error: {e}")
