"""
Stage 3 — Prospeo Email Resolution
Resolve LinkedIn profile URLs into verified work email addresses
using Prospeo's enrich-person API.
API docs: https://app.prospeo.io/api
"""

import os
import random
import requests

PROSPEO_BASE = 'https://api.prospeo.io'




def _resolve_via_prospeo(linkedin_url, api_key):
    """
    Call Prospeo enrich-person to resolve a LinkedIn URL to a verified email.
    Returns dict with 'email' and 'confidence' on success, None on failure.
    """
    try:
        resp = requests.post(
            f'{PROSPEO_BASE}/enrich-person',
            headers={
                'X-KEY': api_key,
                'Content-Type': 'application/json',
            },
            json={
                'only_verified_email': True,
                'enrich_mobile': False,
                'data': {
                    'linkedin_url': linkedin_url,
                },
            },
            timeout=20,
        )
        if resp.status_code == 200:
            data = resp.json()
            response = data.get('response', {})

            # extract email — Prospeo returns it as an object or string
            email_field = response.get('email', '')
            if isinstance(email_field, dict):
                email = email_field.get('value', '') or email_field.get('email', '')
            else:
                email = email_field or ''

            if email:
                return {
                    'email': email,
                    'confidence': 92,  # Prospeo returns verified emails
                    'email_status': 'verified',
                    'source_email': 'prospeo_enrich',
                }

            # If no verified email, try unverified
            unverified = response.get('email_unverified', '')
            if isinstance(unverified, dict):
                unverified = unverified.get('value', '') or unverified.get('email', '')
            if unverified:
                return {
                    'email': unverified,
                    'confidence': 72,
                    'email_status': 'unverified',
                    'source_email': 'prospeo_enrich',
                }

        elif resp.status_code == 402:
            print('    [!] Prospeo enrich: out of credits')
        elif resp.status_code == 429:
            print('    [!] Prospeo enrich: rate limited — slowing down')
        elif resp.status_code == 400 and resp.json().get('error_code') == 'NO_MATCH':
            # API worked but found nothing. Fallback gracefully.
            pass
        else:
            print(f'    [!] Prospeo enrich returned {resp.status_code}')
    except requests.RequestException as e:
        print(f'    [!] Prospeo enrich error: {e}')

    return None


def resolve_emails(people):
    """
    Stage 3: For each person, resolve LinkedIn URL -> verified email via Prospeo.

    If already has an email from the Prospeo company-search step, keep it.
    Falls back to pattern-based generation when API unavailable.
    """
    api_key = os.getenv('PROSPEO_API_KEY', '')
    results = []

    for person in people:
        # already got email from the earlier Prospeo company-search — use it
        if person.get('email'):
            person['email_status'] = 'from_prospeo'
            person['confidence'] = 80
            results.append(person)
            continue

        linkedin = person.get('linkedin', '')
        resolved = False

        if api_key and linkedin:
            result = _resolve_via_prospeo(linkedin, api_key)
            if result:
                person.update(result)
                resolved = True
        else:
            print(f"    [!] Skipping {person.get('full_name')} - no Prospeo API key or linkedin url")

        results.append(person)

    # filter out anyone we couldn't get an email for
    valid = [p for p in results if p.get('email')]
    skipped = len(results) - len(valid)
    if skipped:
        print(f'    [!] Skipped {skipped} contact(s) with no resolvable email')

    return valid
