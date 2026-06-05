"""
Find similar/lookalike companies given a target domain.
Right now uses curated mock data — can swap in Apollo, Crunchbase, etc.
"""

import random
from utils.helpers import get_domain_name

# mock database of companies by rough industry
COMPANY_DB = {
    'ai': [
        {'name': 'Anthropic', 'domain': 'anthropic.com', 'industry': 'AI Research', 'size': '500-1000'},
        {'name': 'Cohere', 'domain': 'cohere.com', 'industry': 'AI/NLP', 'size': '200-500'},
        {'name': 'Mistral AI', 'domain': 'mistral.ai', 'industry': 'AI Research', 'size': '50-200'},
        {'name': 'Hugging Face', 'domain': 'huggingface.co', 'industry': 'AI/ML Platform', 'size': '200-500'},
        {'name': 'Stability AI', 'domain': 'stability.ai', 'industry': 'Generative AI', 'size': '200-500'},
        {'name': 'Perplexity', 'domain': 'perplexity.ai', 'industry': 'AI Search', 'size': '50-200'},
    ],
    'saas': [
        {'name': 'Notion', 'domain': 'notion.so', 'industry': 'Productivity', 'size': '500-1000'},
        {'name': 'Linear', 'domain': 'linear.app', 'industry': 'Project Management', 'size': '50-200'},
        {'name': 'Figma', 'domain': 'figma.com', 'industry': 'Design Tools', 'size': '1000+'},
        {'name': 'Loom', 'domain': 'loom.com', 'industry': 'Video Communication', 'size': '200-500'},
        {'name': 'Airtable', 'domain': 'airtable.com', 'industry': 'Database/No-code', 'size': '500-1000'},
        {'name': 'Coda', 'domain': 'coda.io', 'industry': 'Documents', 'size': '200-500'},
    ],
    'fintech': [
        {'name': 'Stripe', 'domain': 'stripe.com', 'industry': 'Payments', 'size': '5000+'},
        {'name': 'Plaid', 'domain': 'plaid.com', 'industry': 'Banking API', 'size': '500-1000'},
        {'name': 'Ramp', 'domain': 'ramp.com', 'industry': 'Corporate Cards', 'size': '500-1000'},
        {'name': 'Mercury', 'domain': 'mercury.com', 'industry': 'Banking', 'size': '200-500'},
        {'name': 'Brex', 'domain': 'brex.com', 'industry': 'Corporate Finance', 'size': '500-1000'},
        {'name': 'Deel', 'domain': 'deel.com', 'industry': 'Global Payroll', 'size': '1000+'},
    ],
    'devtools': [
        {'name': 'Vercel', 'domain': 'vercel.com', 'industry': 'Cloud Platform', 'size': '500-1000'},
        {'name': 'Supabase', 'domain': 'supabase.com', 'industry': 'Backend-as-a-Service', 'size': '100-300'},
        {'name': 'Railway', 'domain': 'railway.app', 'industry': 'Cloud Hosting', 'size': '50-100'},
        {'name': 'PlanetScale', 'domain': 'planetscale.com', 'industry': 'Database', 'size': '100-300'},
        {'name': 'Render', 'domain': 'render.com', 'industry': 'Cloud Hosting', 'size': '100-300'},
        {'name': 'Fly.io', 'domain': 'fly.io', 'industry': 'Edge Computing', 'size': '50-200'},
    ],
    'default': [
        {'name': 'Slack', 'domain': 'slack.com', 'industry': 'Communication', 'size': '1000+'},
        {'name': 'Zapier', 'domain': 'zapier.com', 'industry': 'Automation', 'size': '500-1000'},
        {'name': 'Calendly', 'domain': 'calendly.com', 'industry': 'Scheduling', 'size': '500-1000'},
        {'name': 'Intercom', 'domain': 'intercom.com', 'industry': 'Customer Support', 'size': '500-1000'},
        {'name': 'HubSpot', 'domain': 'hubspot.com', 'industry': 'CRM/Marketing', 'size': '5000+'},
        {'name': 'Mixpanel', 'domain': 'mixpanel.com', 'industry': 'Analytics', 'size': '200-500'},
    ],
}

# rough mapping — which known domains belong to which category
DOMAIN_HINTS = {
    'openai.com': 'ai', 'anthropic.com': 'ai', 'deepmind.google': 'ai',
    'cohere.com': 'ai', 'mistral.ai': 'ai', 'huggingface.co': 'ai',
    'stripe.com': 'fintech', 'plaid.com': 'fintech', 'ramp.com': 'fintech',
    'notion.so': 'saas', 'linear.app': 'saas', 'figma.com': 'saas',
    'vercel.com': 'devtools', 'supabase.com': 'devtools', 'github.com': 'devtools',
    'netlify.com': 'devtools', 'railway.app': 'devtools',
}


def guess_category(domain):
    """Try to figure out what kind of company this is."""
    if domain in DOMAIN_HINTS:
        return DOMAIN_HINTS[domain]

    # simple keyword matching on domain name
    name = domain.split('.')[0]
    if any(kw in name for kw in ['ai', 'ml', 'deep', 'neural', 'llm']):
        return 'ai'
    if any(kw in name for kw in ['pay', 'fin', 'bank', 'money', 'cash']):
        return 'fintech'
    if any(kw in name for kw in ['dev', 'code', 'git', 'cloud', 'deploy']):
        return 'devtools'

    return 'default'


def find_similar_companies(domain, count=4):
    """
    Find companies that are similar to the given domain.
    
    In production: call Apollo/Crunchbase API here.
    For now: uses curated mock data organized by industry.
    """
    category = guess_category(domain)
    pool = COMPANY_DB.get(category, COMPANY_DB['default'])

    # don't return the input company itself
    filtered = [c for c in pool if c['domain'] != domain]

    # pick a random subset so the demo feels dynamic
    results = random.sample(filtered, min(count, len(filtered)))

    # add a confidence score for UI display
    for i, company in enumerate(results):
        company['match_score'] = random.randint(72, 96)

    return results
