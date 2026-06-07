import os, requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('PROSPEO_API_KEY')

domains = ['prospeo.io', 'google.com', 'microsoft.com', 'hubspot.com', 'vocallabs.com', 'amazon.com', 'ycombinator.com', 'github.com']

for d in domains:
    resp = requests.post(
        'https://api.prospeo.io/search-person',
        headers={'X-KEY': api_key, 'Content-Type': 'application/json'},
        json={'filters': {'person_search': {'company_domain': d}}, 'page': 1}
    )
    print(f"Domain: {d} -> Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"  Found {len(data.get('response', []))} people.")
    else:
        print(f"  Error: {resp.text}")
