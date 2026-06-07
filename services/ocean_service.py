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

    # No Ocean.io key or request failed. Use alternative public API (Clearbit Autocomplete)
    logger.info("Using Clearbit Autocomplete as free alternative API")
    try:
        company_name = domain.split('.')[0]
        resp = requests.get(f'https://autocomplete.clearbit.com/v1/companies/suggest?query={company_name}', timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            companies = []
            for c in data[:limit]:
                # Clearbit returns { name, domain, logo }
                # Reformat to match the expected shape
                if c.get('domain'):
                    companies.append({
                        'name': c.get('name', ''),
                        'domain': c.get('domain', ''),
                        'industry': 'Unknown'
                    })
            if companies:
                return {'source': 'clearbit_alternative', 'companies': companies}
    except requests.RequestException as e:
        logger.error(f"Alternative API request failed: {e}")

    logger.info("Alternative API returned no results.")
    return {'source': 'api', 'companies': []}
