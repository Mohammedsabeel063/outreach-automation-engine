"""
Find decision makers at target companies.
Mock data for now — plug in Apollo/Hunter People Search later.
"""

import random

TITLES = [
    'Head of Growth', 'VP of Sales', 'CTO', 'VP of Engineering',
    'Head of Partnerships', 'Chief Revenue Officer', 'Director of BD',
    'Head of Product', 'VP Marketing', 'CEO',
]

FIRST_NAMES = [
    'Sarah', 'James', 'Priya', 'Michael', 'Emma', 'Carlos',
    'Alex', 'Rachel', 'David', 'Nina', 'Tom', 'Aisha',
    'Ryan', 'Lisa', 'Daniel', 'Mei', 'John', 'Fatima',
]

LAST_NAMES = [
    'Chen', 'Patel', 'Williams', 'Kim', 'Garcia', 'Mueller',
    'Johnson', 'Singh', 'Anderson', 'Nakamura', 'Thompson', 'Ali',
    'Brown', 'Lee', 'Martinez', 'O\'Brien', 'Taylor', 'Khan',
]


def find_decision_makers(companies, per_company=2):
    """
    Find key people at each company.
    
    In production: call Apollo People API or LinkedIn Sales Nav.
    For now: generates realistic-looking mock contacts.
    """
    people = []

    for company in companies:
        # pick random names/titles, avoid duplicates
        used_names = set()
        titles = random.sample(TITLES, min(per_company, len(TITLES)))

        for i in range(per_company):
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)

            # avoid duplicate names within same company
            while f'{first} {last}' in used_names:
                first = random.choice(FIRST_NAMES)
                last = random.choice(LAST_NAMES)
            used_names.add(f'{first} {last}')

            clean_last = last.lower().replace("'", '')
            people.append({
                'first_name': first,
                'last_name': last,
                'title': titles[i],
                'company': company['name'],
                'domain': company['domain'],
                'linkedin': f"linkedin.com/in/{first.lower()}-{clean_last}",
            })

    return people
