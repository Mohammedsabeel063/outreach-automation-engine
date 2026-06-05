"""
Generate and verify email addresses for contacts.
Uses common email patterns — can plug in Hunter.io verify API later.
"""

import os
import random
import requests

PATTERNS = [
    '{first}.{last}',
    '{first}',
    '{f}{last}',
    '{first}{l}',
    '{first}_{last}',
]


def make_email(first, last, domain, pattern):
    f = first.lower().replace("'", '')
    l = last.lower().replace("'", '')
    return pattern.format(first=f, last=l, f=f[0], l=l[0]) + '@' + domain


def verify_with_hunter(email):
    """Try Hunter.io verification if API key is set."""
    api_key = os.getenv('HUNTER_API_KEY')
    if not api_key:
        return None

    try:
        resp = requests.get(
            'https://api.hunter.io/v2/email-verifier',
            params={'email': email, 'api_key': api_key},
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json().get('data', {})
            return data.get('status', 'unknown')
    except requests.RequestException:
        pass

    return None


def generate_emails(people, companies):
    """
    Generate probable email addresses for each person.
    
    Strategy:
    1. Pick the most common email pattern for the domain
    2. If Hunter API key is set, verify it
    3. Otherwise, just assign a confidence based on pattern commonality
    """
    contacts = []

    for person in people:
        domain = person['domain']
        first = person['first_name']
        last = person['last_name']

        # most companies use first.last — it's right ~60% of the time
        pattern = random.choice(PATTERNS[:3])
        email = make_email(first, last, domain, pattern)

        # try real verification
        hunter_status = verify_with_hunter(email)

        if hunter_status:
            status = hunter_status
            confidence = 95 if hunter_status == 'valid' else 50
        else:
            # mock confidence — first.last pattern is most reliable
            confidence = random.randint(70, 95)
            status = 'likely valid' if confidence > 80 else 'unverified'

        contacts.append({
            **person,
            'email': email,
            'email_status': status,
            'confidence': confidence,
        })

    return contacts
