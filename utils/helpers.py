import re


def clean_domain(raw_input):
    """Take whatever the user typed and try to extract a clean domain."""
    text = raw_input.strip().lower()

    # strip protocol
    text = re.sub(r'^https?://', '', text)
    # strip www.
    text = re.sub(r'^www\.', '', text)
    # strip trailing slashes/paths
    text = text.split('/')[0]

    return text


def is_valid_domain(domain):
    """Basic check — does it look like something.something?"""
    pattern = r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z]{2,})+$'
    return bool(re.match(pattern, domain))


def get_domain_name(domain):
    """openai.com -> OpenAI, stripe.com -> Stripe"""
    name = domain.split('.')[0]
    return name.capitalize()


def truncate(text, length=100):
    if len(text) <= length:
        return text
    return text[:length].rsplit(' ', 1)[0] + '...'
