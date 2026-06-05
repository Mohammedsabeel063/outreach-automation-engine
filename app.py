"""
Flask web interface — wraps the same pipeline as the CLI.
Run: python app.py, then open http://localhost:5000
"""

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from utils.helpers import clean_domain, is_valid_domain
from services.ocean_service import find_lookalike_companies
from services.prospeo_service import find_decision_makers
from services.eazyreach_service import resolve_emails
from services.outreach_generator import generate_outreach

load_dotenv()
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/run', methods=['POST'])
def run():
    data = request.get_json()
    domain = clean_domain(data.get('domain', ''))

    if not domain or not is_valid_domain(domain):
        return jsonify({'error': 'Enter a valid domain like openai.com'}), 400

    try:
        result = find_lookalike_companies(domain, limit=5)
        companies = result['companies']

        if not companies:
            return jsonify({'error': 'No similar companies found for this domain'}), 404

        people = find_decision_makers(companies, per_company=2)
        contacts = resolve_emails(people)
        contacts = generate_outreach(domain, contacts)

        return jsonify({
            'domain': domain,
            'companies': companies,
            'contacts': contacts,
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print('\n  Outreach Engine — Web UI')
    print('  http://localhost:5000\n')
    app.run(debug=True, port=5000)
