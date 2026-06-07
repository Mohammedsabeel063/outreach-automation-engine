"""
Flask web interface — wraps the same pipeline as the CLI.
Run: python app.py, then open http://localhost:5000
"""

import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from utils.helpers import clean_domain, is_valid_domain
from services.ocean_service import find_lookalike_companies
from services.prospeo_service import find_decision_makers
from services.prospeo_email_service import resolve_emails
from services.outreach_generator import generate_outreach

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/health')
def health():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'outreach-automation-engine'
    })


@app.route('/api/run', methods=['POST'])
def run():
    data = request.get_json()
    domain = clean_domain(data.get('domain', ''))

    logger.info(f"Received pipeline request for domain: {domain}")

    if not domain or not is_valid_domain(domain):
        logger.warning(f"Invalid domain received: {data.get('domain', '')}")
        return jsonify({'error': 'Enter a valid domain like openai.com'}), 400

    try:
        logger.info(f"Stage 1: Finding lookalike companies for {domain}")
        result = find_lookalike_companies(domain, limit=5)
        companies = result['companies']
        logger.info(f"Stage 1 complete: Found {len(companies)} companies (source: {result['source']})")

        if not companies:
            logger.warning(f"No companies found for domain: {domain}")
            return jsonify({'error': 'No similar companies found for this domain'}), 404

        logger.info(f"Stage 2: Finding decision makers for {len(companies)} companies")
        people = find_decision_makers(companies, per_company=2)
        logger.info(f"Stage 2 complete: Found {len(people)} contacts")

        logger.info(f"Stage 3: Resolving emails for {len(people)} contacts")
        contacts = resolve_emails(people)
        logger.info(f"Stage 3 complete: Resolved {len(contacts)} emails")

        logger.info(f"Stage 4: Generating outreach for {len(contacts)} contacts")
        contacts = generate_outreach(domain, contacts)
        logger.info(f"Stage 4 complete: Generated {len(contacts)} outreach emails")

        logger.info(f"Pipeline completed successfully for {domain}")
        return jsonify({
            'domain': domain,
            'companies': companies,
            'contacts': contacts,
        })

    except Exception as e:
        logger.error(f"Pipeline failed for {domain}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print('\n  Outreach Engine — Web UI')
    print('  http://localhost:5000\n')
    app.run(debug=True, port=5000)
