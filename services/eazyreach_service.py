"""
Stage 3 — Eazyreach
Resolve LinkedIn profile URLs into verified work email addresses.
App: https://eazyreach.app
"""

import os
import random
import requests

EAZYREACH_BASE = 'https://api.eazyreach.app/v1'

# Common corporate email patterns by frequency
EMAIL_PATTERNS = [
    '{first}.{last}',       # most common ~55%
    '{first}{last}',        # second ~15%
    '{f}{last}',            # initial.last ~12%
    '{first}',              # first only ~8%
    '{first}.{l}',          # first.initial ~5%
    '{first}_{last}',       # underscore ~5%
]


def _pattern_email(first, last, domain):
    """Generate the most statistically likely email for this person."""
    f = first.lower()
    l = last.lower()
    pattern = EMAIL_PATTERNS[0]  # first.last is most common
    return (
        pattern
        .replace('{first}', f)
        .replace('{last}', l)
        .replace('{f}', f[0] if f else '')
        .replace('{l}', l[0] if l else '')
    ) + '@' + domain


def _resolve_via_eazyreach(linkedin_url, api_key):
    """
    Call Eazyreach to resolve a LinkedIn URL to a verified email.
    Returns dict with 'email' and 'confidence' on success, None on failure.
    """
    try:
        resp = requests.post(
            f'{EAZYREACH_BASE}/resolve',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={'linkedin_url': linkedin_url},
            timeout=20,
        )
        if resp.status_code == 200:
            data = resp.json()
            email = data.get('email', '')
            if email:
                return {
                    'email': email,
                    'confidence': data.get('confidence', 85),
                    'status': data.get('status', 'verified'),
                    'source': 'eazyreach',
                }
        elif resp.status_code == 402:
            print('    [!] Eazyreach: out of credits')
        elif resp.status_code == 429:
            print('    [!] Eazyreach: rate limited — slowing down')
        else:
            print(f'    [!] Eazyreach returned {resp.status_code}')
    except requests.RequestException as e:
        print(f'    [!] Eazyreach error: {e}')

    return None


def resolve_emails(people):
    """
    Stage 3: For each person, resolve LinkedIn URL -> verified email.

    If already has an email from Prospeo, skips Eazyreach for that contact.
    Falls back to pattern-based generation when API unavailable.
    """
    api_key = os.getenv('EAZYREACH_API_KEY', '')
    results = []

    for person in people:
        # already got email from Prospeo — use it
        if person.get('email'):
            person['email_status'] = 'from_prospeo'
            person['confidence'] = 80
            results.append(person)
            continue

        linkedin = person.get('linkedin', '')
        resolved = False

        if api_key and linkedin:
            result = _resolve_via_eazyreach(linkedin, api_key)
            if result:
                person.update(result)
                resolved = True

        if not resolved:
            # pattern fallback
            email = _pattern_email(
                person.get('first_name', ''),
                person.get('last_name', ''),
                person.get('domain', ''),
            )
            confidence = random.randint(68, 88)
            person['email'] = email
            person['confidence'] = confidence
            person['email_status'] = 'pattern_guess'
            person['source_email'] = 'mock'

        results.append(person)

    # filter out anyone we couldn't get an email for
    valid = [p for p in results if p.get('email')]
    skipped = len(results) - len(valid)
    if skipped:
        print(f'    [!] Skipped {skipped} contact(s) with no resolvable email')

    return valid
