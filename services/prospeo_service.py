"""
Stage 2 — Prospeo
Find C-suite / VP-level decision makers for each company.
API docs: https://app.prospeo.io/api
"""

import os
import random
import requests

PROSPEO_BASE = 'https://app.prospeo.io/api'

TITLES = [
    'CEO', 'CTO', 'COO', 'VP of Sales', 'VP of Engineering',
    'Head of Growth', 'Head of Product', 'Chief Revenue Officer',
    'Director of Business Development', 'VP Marketing',
    'Head of Partnerships', 'VP of Operations',
]

FIRST_NAMES = [
    'Sarah', 'James', 'Priya', 'Michael', 'Emma', 'Carlos',
    'Alex', 'Rachel', 'David', 'Nina', 'Tom', 'Aisha',
    'Ryan', 'Lisa', 'Daniel', 'Mei', 'John', 'Fatima',
]

LAST_NAMES = [
    'Chen', 'Patel', 'Williams', 'Kim', 'Garcia', 'Mueller',
    'Johnson', 'Singh', 'Anderson', 'Nakamura', 'Thompson', 'Ali',
    'Brown', 'Lee', 'Martinez', 'Taylor', 'Khan', 'Rosenberg',
]


def _mock_people_for(company, count=2):
    """Generate realistic-looking mock contacts for a company."""
    used = set()
    titles = random.sample(TITLES, min(count, len(TITLES)))
    people = []

    for i in range(count):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        while f'{first}{last}' in used:
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
        used.add(f'{first}{last}')

        clean_last = last.lower().replace("'", '')
        people.append({
            'first_name': first,
            'last_name': last,
            'full_name': f'{first} {last}',
            'title': titles[i],
            'company': company['name'],
            'domain': company['domain'],
            'linkedin': f'https://linkedin.com/in/{first.lower()}-{clean_last}',
            'source': 'mock',
        })

    return people


def find_decision_makers(companies, per_company=2):
    """
    Stage 2: Get C-suite and VP contacts for each company.

    Prospeo API: POST /company-search
    Header: X-KEY: {api_key}
    Body: {"url": "https://company.com", "limit": 5}

    Falls back to mock data per company if key missing or call fails.
    """
    api_key = os.getenv('PROSPEO_API_KEY', '')
    all_people = []

    for company in companies:
        domain = company.get('domain', '')
        if not domain:
            continue

        fetched = False
        if api_key:
            try:
                resp = requests.post(
                    f'{PROSPEO_BASE}/company-search',
                    headers={'X-KEY': api_key, 'Content-Type': 'application/json'},
                    json={'url': f'https://{domain}', 'limit': per_company},
                    timeout=15,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    contacts = data.get('response', [])
                    for c in contacts:
                        all_people.append({
                            'first_name': c.get('first_name', ''),
                            'last_name': c.get('last_name', ''),
                            'full_name': f"{c.get('first_name', '')} {c.get('last_name', '')}".strip(),
                            'title': c.get('position', ''),
                            'company': company.get('name', domain),
                            'domain': domain,
                            'linkedin': c.get('linkedin', ''),
                            'email': c.get('email', {}).get('value', '') if isinstance(c.get('email'), dict) else c.get('email', ''),
                            'source': 'prospeo',
                        })
                    fetched = True
                else:
                    print(f'    [!] Prospeo returned {resp.status_code} for {domain}')
            except requests.RequestException as e:
                print(f'    [!] Prospeo error for {domain}: {e}')

        if not fetched:
            all_people.extend(_mock_people_for(company, per_company))

    return all_people
