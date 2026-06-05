#!/usr/bin/env python3
"""
Outreach Automation Engine — CLI Pipeline
==========================================
One input. Four stages. Zero manual steps.

Usage:
  python pipeline.py openai.com
  python pipeline.py openai.com --dry-run      # skip actual sending
  python pipeline.py openai.com --limit 3      # fewer companies
"""

import sys
import argparse
from dotenv import load_dotenv

from utils.helpers import clean_domain, is_valid_domain
from services.ocean_service import find_lookalike_companies
from services.prospeo_service import find_decision_makers
from services.eazyreach_service import resolve_emails
from services.outreach_generator import generate_outreach
from services.brevo_service import send_emails

load_dotenv()


# ── CLI helpers ───────────────────────────────────────────────────────────────

def hr():
    print('  ' + '-' * 54)

def section(n, total, label):
    print(f'\n  [{n}/{total}] {label}')

def ok(msg):
    print(f'  [OK]  {msg}')

def warn(msg):
    print(f'  [!!]  {msg}')

def info(msg):
    print(f'        {msg}')


# ── Safety checkpoint ─────────────────────────────────────────────────────────

def safety_checkpoint(contacts, dry_run):
    """
    Show a summary of what will be sent and ask for confirmation.
    This is the one manual step in the pipeline.
    """
    hr()
    print(f'\n  SAFETY CHECKPOINT -- {len(contacts)} emails queued\n')

    for i, c in enumerate(contacts, 1):
        print(f'  {i}. {c["email"]:<35} {c.get("title", ""):<25} {c.get("company", "")}')

    print()

    # offer to preview one email
    preview = input('  Preview email for contact #1? [y/N] ').strip().lower()
    if preview == 'y' and contacts:
        c = contacts[0]
        print(f'\n  Subject: {c["subject"]}')
        print(f'  ─────────────────────────────────────')
        for line in c['body'].split('\n'):
            print(f'  {line}')
        print()

    if dry_run:
        print('  [DRY RUN] Skipping actual send.')
        return True

    confirm = input('  Send all emails now? [y/N] ').strip().lower()
    return confirm == 'y'


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run_pipeline(domain, limit=5, dry_run=False):
    print(f'\n  Outreach Automation Engine')
    print(f'  Seed domain: {domain}')
    hr()
    import sys
    sys.stdout.reconfigure(encoding='utf-8', errors='replace') if hasattr(sys.stdout, 'reconfigure') else None

    # ── Stage 1: Lookalike companies ──────────────────────────────────────────
    section(1, 4, 'Finding lookalike companies  [Ocean.io]')
    result = find_lookalike_companies(domain, limit=limit)
    companies = result['companies']

    if not companies:
        warn('No companies found. Try a different domain.')
        return

    ok(f'Found {len(companies)} companies  (source: {result["source"]})')
    for c in companies:
        info(f'{c["name"]:<22}  {c["domain"]:<25}  {c.get("industry", "")}')

    # ── Stage 2: Decision makers ──────────────────────────────────────────────
    section(2, 4, 'Finding decision makers  [Prospeo]')
    people = find_decision_makers(companies, per_company=2)

    if not people:
        warn('No decision makers found.')
        return

    ok(f'Found {len(people)} contacts across {len(companies)} companies')
    for p in people:
        info(f'{p["full_name"]:<22}  {p.get("title", ""):<28}  {p.get("company", "")}')

    # ── Stage 3: Resolve emails ───────────────────────────────────────────────
    section(3, 4, 'Resolving work email addresses  [Eazyreach]')
    contacts = resolve_emails(people)

    if not contacts:
        warn('Could not resolve any emails. Stopping.')
        return

    ok(f'Resolved {len(contacts)}/{len(people)} email addresses')
    for c in contacts:
        status = c.get('email_status', 'unknown')
        conf = c.get('confidence', 0)
        info(f'{c["email"]:<38}  {conf}% confidence  [{status}]')

    # ── Generate outreach copy ────────────────────────────────────────────────
    print(f'\n  Generating personalized outreach copy...')
    contacts = generate_outreach(domain, contacts)
    ok(f'Generated {len(contacts)} outreach emails')

    # ── Safety checkpoint ─────────────────────────────────────────────────────
    confirmed = safety_checkpoint(contacts, dry_run)
    if not confirmed:
        print('\n  Aborted. No emails sent.\n')
        return

    # ── Stage 4: Send via Brevo ───────────────────────────────────────────────
    section(4, 4, 'Sending emails  [Brevo]')
    summary = send_emails(contacts, dry_run=dry_run)

    if 'error' in summary:
        warn(summary['error'])
        return

    ok(f'Sent: {summary.get("sent", 0)}  '
       f'Failed: {summary.get("failed", 0)}  '
       f'Mode: {summary.get("mode", "unknown")}')

    # print any failures
    for detail in summary.get('details', []):
        if not detail['ok']:
            warn(f'{detail["email"]} — {detail["info"]}')

    hr()
    print(f'\n  Done! Pipeline complete for {domain}\n')

    return {
        'domain': domain,
        'companies': companies,
        'contacts': contacts,
        'send_summary': summary,
    }


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='End-to-end cold outreach pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Example: python pipeline.py openai.com --dry-run',
    )
    parser.add_argument('domain', help='Seed company domain (e.g. openai.com)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Run full pipeline but skip actual email sending')
    parser.add_argument('--limit', type=int, default=5,
                        help='Max number of lookalike companies (default: 5)')
    args = parser.parse_args()

    domain = clean_domain(args.domain)
    if not is_valid_domain(domain):
        print(f'\n  Error: "{args.domain}" doesn\'t look like a valid domain.')
        print('  Try something like: openai.com, stripe.com\n')
        sys.exit(1)

    run_pipeline(domain, limit=args.limit, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
