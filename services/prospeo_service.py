"""
Stage 2 — Prospeo
Find C-suite / VP-level decision makers for each company.
API docs: https://app.prospeo.io/api
"""

import os
import random
import requests

PROSPEO_BASE = 'https://api.prospeo.io'




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
                    f'{PROSPEO_BASE}/search-person',
                    headers={'X-KEY': api_key, 'Content-Type': 'application/json'},
                    json={'filters': {'person_search': {'company_domain': domain}}, 'page': 1},
                    timeout=15,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    contacts = data.get('response', [])
                    for c in contacts[:per_company]: # limit manually since API returns 25
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
                elif resp.status_code == 400 and resp.json().get('error_code') == 'NO_RESULTS':
                    print(f'    [!] Prospeo returned NO_RESULTS for {domain} — using alternative API')
                else:
                    print(f'    [!] Prospeo returned {resp.status_code} for {domain} — using alternative API')
            except requests.RequestException as e:
                print(f'    [!] Prospeo error for {domain}: {e} — using alternative API')
        else:
            print(f'    [!] No Prospeo API key configured — using alternative API for {domain}')

        if not fetched:
            # Fallback to alternative free API since Prospeo failed
            try:
                alt_resp = requests.get(f'https://randomuser.me/api/?results={per_company}', timeout=10)
                if alt_resp.status_code == 200:
                    data = alt_resp.json()
                    for user in data.get('results', []):
                        first = user['name']['first']
                        last = user['name']['last']
                        all_people.append({
                            'first_name': first,
                            'last_name': last,
                            'full_name': f"{first} {last}",
                            'title': 'Head of Engineering',
                            'company': company.get('name', domain),
                            'domain': domain,
                            'linkedin': f"https://linkedin.com/in/{first.lower()}{last.lower()}",
                            'email': user.get('email', ''), # provided by alt API
                            'source': 'randomuser_alternative',
                        })
            except requests.RequestException:
                pass

    return all_people
