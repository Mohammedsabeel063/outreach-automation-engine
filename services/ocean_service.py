"""
Stage 1 — Ocean.io
Find lookalike companies from a seed domain.
Docs: https://ocean.io/api
"""

import os
import random
import requests
import logging

logger = logging.getLogger(__name__)

OCEAN_BASE = 'https://ocean.io/api/v1'

# Curated fallback data — mirrors Ocean.io response shape
MOCK_DB = {
    'ai': [
        {'name': 'Anthropic',   'domain': 'anthropic.com',   'industry': 'AI Research',       'employee_count': '500-1000'},
        {'name': 'Cohere',      'domain': 'cohere.com',       'industry': 'AI / NLP',          'employee_count': '200-500'},
        {'name': 'Mistral AI',  'domain': 'mistral.ai',       'industry': 'AI Research',       'employee_count': '50-200'},
        {'name': 'Hugging Face','domain': 'huggingface.co',   'industry': 'AI / ML Platform',  'employee_count': '200-500'},
        {'name': 'Perplexity',  'domain': 'perplexity.ai',    'industry': 'AI Search',         'employee_count': '50-200'},
        {'name': 'Adept AI',    'domain': 'adept.ai',         'industry': 'AI Agents',         'employee_count': '50-200'},
    ],
    'fintech': [
        {'name': 'Brex',    'domain': 'brex.com',    'industry': 'Corporate Finance', 'employee_count': '500-1000'},
        {'name': 'Ramp',    'domain': 'ramp.com',    'industry': 'Corporate Cards',   'employee_count': '500-1000'},
        {'name': 'Mercury', 'domain': 'mercury.com', 'industry': 'Banking',           'employee_count': '200-500'},
        {'name': 'Deel',    'domain': 'deel.com',    'industry': 'Global Payroll',    'employee_count': '1000+'},
        {'name': 'Plaid',   'domain': 'plaid.com',   'industry': 'Banking API',       'employee_count': '500-1000'},
    ],
    'saas': [
        {'name': 'Notion',   'domain': 'notion.so',   'industry': 'Productivity',    'employee_count': '500-1000'},
        {'name': 'Linear',   'domain': 'linear.app',  'industry': 'Project Mgmt',    'employee_count': '50-200'},
        {'name': 'Loom',     'domain': 'loom.com',    'industry': 'Video / Async',   'employee_count': '200-500'},
        {'name': 'Airtable', 'domain': 'airtable.com','industry': 'Database',        'employee_count': '500-1000'},
        {'name': 'Coda',     'domain': 'coda.io',     'industry': 'Documents',       'employee_count': '200-500'},
    ],
    'devtools': [
        {'name': 'Vercel',      'domain': 'vercel.com',     'industry': 'Cloud Platform', 'employee_count': '500-1000'},
        {'name': 'Supabase',    'domain': 'supabase.com',   'industry': 'Backend-as-a-Service', 'employee_count': '100-300'},
        {'name': 'PlanetScale', 'domain': 'planetscale.com','industry': 'Database',       'employee_count': '100-300'},
        {'name': 'Railway',     'domain': 'railway.app',    'industry': 'Cloud Hosting',  'employee_count': '20-50'},
        {'name': 'Fly.io',      'domain': 'fly.io',         'industry': 'Edge Compute',   'employee_count': '20-50'},
    ],
    'default': [
        {'name': 'Zapier',    'domain': 'zapier.com',    'industry': 'Automation',    'employee_count': '500-1000'},
        {'name': 'Calendly',  'domain': 'calendly.com',  'industry': 'Scheduling',    'employee_count': '500-1000'},
        {'name': 'Intercom',  'domain': 'intercom.com',  'industry': 'Support',       'employee_count': '500-1000'},
        {'name': 'Mixpanel',  'domain': 'mixpanel.com',  'industry': 'Analytics',     'employee_count': '200-500'},
        {'name': 'Amplitude', 'domain': 'amplitude.com', 'industry': 'Analytics',     'employee_count': '500-1000'},
    ],
}

DOMAIN_MAP = {
    'openai.com': 'ai', 'anthropic.com': 'ai', 'cohere.com': 'ai',
    'mistral.ai': 'ai', 'huggingface.co': 'ai', 'perplexity.ai': 'ai',
    'stripe.com': 'fintech', 'plaid.com': 'fintech', 'brex.com': 'fintech',
    'notion.so': 'saas', 'linear.app': 'saas', 'figma.com': 'saas',
    'vercel.com': 'devtools', 'supabase.com': 'devtools', 'github.com': 'devtools',
}


def _guess_category(domain):
    if domain in DOMAIN_MAP:
        return DOMAIN_MAP[domain]
    name = domain.split('.')[0]
    if any(k in name for k in ['ai', 'ml', 'llm', 'gpt', 'neural']):
        return 'ai'
    if any(k in name for k in ['pay', 'fin', 'bank', 'cash', 'money']):
        return 'fintech'
    if any(k in name for k in ['dev', 'code', 'git', 'deploy', 'cloud']):
        return 'devtools'
    return 'default'


def find_lookalike_companies(domain, limit=5):
    """
    Call Ocean.io to get companies similar to the seed domain.
    Falls back to curated mock data if key is missing or API fails.
    """
    api_key = os.getenv('OCEAN_API_KEY', '')

    if api_key:
        logger.info(f"Attempting Ocean.io API call for {domain}")
        try:
            resp = requests.post(
                f'{OCEAN_BASE}/companies/similar',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                },
                json={'domain': domain, 'limit': limit},
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                # Ocean.io may return 'companies' or 'data' key — handle both
                companies = data.get('companies', data.get('data', []))
                if companies:
                    logger.info(f"Ocean.io returned {len(companies)} companies")
                    return {'source': 'ocean', 'companies': companies[:limit]}
            else:
                logger.warning(f"Ocean.io returned {resp.status_code} — using fallback")
        except requests.RequestException as e:
            logger.error(f"Ocean.io request failed: {e} — using fallback")
    else:
        logger.info("Ocean.io API key not set — using mock data")

    # fallback
    logger.info(f"Using mock fallback for {domain}")
    category = _guess_category(domain)
    pool = MOCK_DB.get(category, MOCK_DB['default'])
    picked = random.sample([c for c in pool if c['domain'] != domain],
                           min(limit, len(pool)))
    for c in picked:
        c.setdefault('match_score', random.randint(71, 95))

    logger.info(f"Mock fallback returned {len(picked)} companies")
    return {'source': 'mock', 'companies': picked}
