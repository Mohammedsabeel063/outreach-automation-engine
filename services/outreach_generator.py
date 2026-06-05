"""
Email copy that sounds like a real startup person wrote it.
Not generic — references company, role, and keeps it short.
"""

import os
import json
import random
from utils.helpers import get_domain_name


def _openai_email(sender_company, person):
    api_key = os.getenv('OPENAI_API_KEY', '')
    if not api_key:
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        prompt = f"""Write a short B2B cold email (under 100 words) from {sender_company} to:
- Name: {person['first_name']}
- Title: {person.get('title', 'decision maker')}
- Company: {person.get('company', 'their company')}

The email should:
- Open with something specific (not "I hope this finds you well")
- Mention their role naturally
- Have one clear ask: 15-min call
- Sound like a real person at an early-stage startup wrote it
- End with first name only

Return JSON: {{"subject": "...", "body": "..."}}"""

        resp = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.9,
            max_tokens=300,
        )
        text = resp.choices[0].message.content.strip()
        if text.startswith('```'):
            text = text.split('```')[1].lstrip('json\n')
        parsed = json.loads(text)
        if parsed.get('subject') and parsed.get('body'):
            return parsed
    except Exception:
        pass
    return None


def _template_email(sender_company, person):
    first = person.get('first_name', 'there')
    company = person.get('company', 'your company')
    title = person.get('title', '')

    # pull the role keyword for subject line personalization
    role_short = (
        'growth' if 'growth' in title.lower() else
        'eng' if 'engineer' in title.lower() or 'cto' in title.lower() else
        'sales' if 'sales' in title.lower() or 'revenue' in title.lower() else
        'product' if 'product' in title.lower() else
        'ops' if 'operat' in title.lower() or 'coo' in title.lower() else
        'biz dev' if 'partner' in title.lower() or 'bd' in title.lower() else
        'leadership'
    )

    templates = [
        {
            'subject': f'{first} — {company}\'s outbound workflow',
            'body': (
                f'Hey {first},\n\n'
                f'Came across {company} while researching the space — '
                f'looks like you\'re scaling fast.\n\n'
                f'I\'m building {sender_company}, which automates the outbound pipeline: '
                f'finding the right companies, surfacing decision makers, and getting them '
                f'a personalized message without the manual work.\n\n'
                f'Given your {role_short} background, thought this might be on your radar. '
                f'Worth a 15-min call this week?\n\n'
                f'{sender_company.split()[0]}'
            ),
        },
        {
            'subject': f'GTM question for {company}',
            'body': (
                f'Hi {first},\n\n'
                f'Not sure if this lands with you directly, '
                f'but we\'re working on something that might save your team a lot of time '
                f'on the outbound side.\n\n'
                f'{sender_company} handles the research + outreach automation piece — '
                f'the stuff that usually takes your team hours each week. '
                f'We\'ve been talking to a few {role_short} leads at similar companies.\n\n'
                f'Happy to give you a quick walkthrough if useful — 15 min max.\n\n'
                f'Best'
            ),
        },
        {
            'subject': f'Scaling outreach at {company}',
            'body': (
                f'Hey {first},\n\n'
                f'Quick one — I\'ve been thinking about how teams like {company} handle '
                f'outbound prospecting at scale, and I think there\'s a more efficient way '
                f'to do it.\n\n'
                f'We built {sender_company} to automate exactly that: '
                f'lookalike company discovery, contact finding, email resolution, and '
                f'personalized outreach — one input, all automated.\n\n'
                f'Would love to show you what it looks like. Open to a call this week?\n\n'
                f'Cheers'
            ),
        },
    ]

    return random.choice(templates)


def generate_outreach(sender_domain, contacts):
    """Generate personalized outreach for each contact. Tries OpenAI, falls back to templates."""
    sender = get_domain_name(sender_domain)
    result = []

    for person in contacts:
        ai = _openai_email(sender, person)
        if ai:
            person['subject'] = ai['subject']
            person['body'] = ai['body']
            person['copy_source'] = 'ai'
        else:
            tmpl = _template_email(sender, person)
            person['subject'] = tmpl['subject']
            person['body'] = tmpl['body']
            person['copy_source'] = 'template'

        result.append(person)

    return result
