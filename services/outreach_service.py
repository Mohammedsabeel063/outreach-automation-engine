"""
Generate personalized outreach emails.
Tries OpenAI first, falls back to smart templates.
"""

import os
import json
from utils.helpers import get_domain_name


def generate_with_openai(sender_company, contact):
    """Try generating with OpenAI if key is available."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        prompt = f"""Write a short cold outreach email (under 120 words) from a startup 
to {contact['first_name']} {contact['last_name']}, {contact['title']} at {contact['company']}.

The sender is from {sender_company}. Keep it casual, specific, and human. 
No generic opener. One clear ask — a 15 min call.
End with just a first name sign-off.

Return JSON: {{"subject": "...", "body": "..."}}"""

        resp = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.8,
            max_tokens=300,
        )

        text = resp.choices[0].message.content.strip()
        # strip code fences if model wraps it
        if text.startswith('```'):
            text = text.split('```')[1].lstrip('json\n')
        return json.loads(text)

    except Exception:
        return None


def template_outreach(sender_company, contact):
    """Fallback — handwritten templates that sound human."""
    first = contact['first_name']
    company = contact['company']
    title = contact['title']

    templates = [
        {
            'subject': f'{first} — quick question about {company}',
            'body': (
                f"Hey {first},\n\n"
                f"Saw what {company} is building — really impressive stuff, especially "
                f"given how fast the space is moving.\n\n"
                f"I'm working on something at {sender_company} that might be relevant "
                f"for your team, specifically around outreach automation and pipeline generation.\n\n"
                f"Would love to get 15 min on your calendar this week to see if there's a fit. "
                f"No pressure either way.\n\n"
                f"Cheers"
            ),
        },
        {
            'subject': f'Idea for {company}\'s outreach',
            'body': (
                f"Hi {first},\n\n"
                f"I noticed {company} is scaling pretty quickly — congrats on the growth.\n\n"
                f"We've been helping teams like yours automate their outbound pipeline "
                f"(finding leads, generating personalized emails, the whole thing). "
                f"Given your role as {title}, figured this might be on your radar.\n\n"
                f"Happy to share a quick demo — would Thursday or Friday work?\n\n"
                f"Best"
            ),
        },
        {
            'subject': f'For {first} at {company}',
            'body': (
                f"Hey {first},\n\n"
                f"Not sure if this lands with you, but I think {company} could benefit from "
                f"what we're building at {sender_company}.\n\n"
                f"We automate the tedious parts of outbound — company research, contact finding, "
                f"personalized messaging. Basically the stuff that eats up your team's time.\n\n"
                f"Worth a quick chat? I promise to keep it under 15 min.\n\n"
                f"Talk soon"
            ),
        },
    ]

    import random
    return random.choice(templates)


def generate_outreach(sender_domain, contacts):
    """
    Generate personalized outreach for each contact.
    Tries OpenAI first, falls back to templates.
    """
    sender_company = get_domain_name(sender_domain)
    results = []

    for contact in contacts:
        # try AI generation first
        ai_result = generate_with_openai(sender_company, contact)

        if ai_result and 'subject' in ai_result:
            email_data = {
                'to': contact['email'],
                'to_name': f"{contact['first_name']} {contact['last_name']}",
                'company': contact['company'],
                'subject': ai_result['subject'],
                'body': ai_result['body'],
                'source': 'ai',
            }
        else:
            template = template_outreach(sender_company, contact)
            email_data = {
                'to': contact['email'],
                'to_name': f"{contact['first_name']} {contact['last_name']}",
                'company': contact['company'],
                'subject': template['subject'],
                'body': template['body'],
                'source': 'template',
            }

        results.append(email_data)

    return results
