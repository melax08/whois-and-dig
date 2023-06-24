from http import HTTPStatus

from flask import Flask, jsonify, request
import whois

from constants import ALLOWED_RECORDS, DEFAULT_TYPE, DNS_SERVERS
from exceptions import BadDomain
from wd import Domain

app = Flask(__name__)


class InvalidAPIUsage(Exception):
    """Error class for API exceptions."""
    status_code = 400

    def __init__(self, message, status_code=None):
        super().__init__()
        self.message = message
        if status_code is not None:
            self.status_code = status_code

    def to_dict(self):
        return dict(message=self.message, result=False)


@app.errorhandler(InvalidAPIUsage)
def invalid_api_usage(error):
    """Handler for API exceptions."""
    return jsonify(error.to_dict()), error.status_code


@app.route('/api/v1/whois/', methods=['POST'])
def whois_api():
    """
    Allows to get WHOIS information about domain.
    Allowed POSt JSON field:
    - domain (string, required).
    """
    data = request.get_json(silent=True)
    if not data:
        raise InvalidAPIUsage('Request data is empty or invalid')

    domain = data.get('domain')
    if not domain:
        raise InvalidAPIUsage('"Domain" field is required')

    try:
        dom = Domain(domain)
        whois_output = dom.whois_json()
    except BadDomain:
        raise InvalidAPIUsage('Bad domain', HTTPStatus.OK)
    except (
            whois.exceptions.WhoisCommandFailed,
            whois.exceptions.WhoisPrivateRegistry,
            whois.exceptions.FailedParsingWhoisOutput,
            whois.exceptions.UnknownTld,
            whois.exceptions.UnknownDateFormat
    ) as error:
        raise InvalidAPIUsage(str(error), HTTPStatus.OK)
    return jsonify(whois_output), HTTPStatus.OK


@app.route('/api/v1/dig/', methods=['POST'])
def dig_api():
    """
    Allows to get DIG information about domain.
    Allowed POST JSON fields:
    - domain (string, required);
    - record (string, non required);
    - dns (list, non required).
    """
    data = request.get_json(silent=True)
    if not data:
        raise InvalidAPIUsage('Request data is empty or invalid')

    domain = data.get('domain')
    if not domain:
        raise InvalidAPIUsage('"Domain" field is required')

    record = data.get('record')

    dns = data.get('dns')
    if not dns:
        dns = DNS_SERVERS
    else:
        if not isinstance(dns, list):
            raise InvalidAPIUsage('"DNS" field must be a list')

    try:
        dom = Domain(domain)
        dig_output = dom.dig(record, dns)
    except BadDomain:
        raise InvalidAPIUsage('Bad domain', HTTPStatus.OK)
    return jsonify(dig_output), HTTPStatus.OK


@app.route('/api/v1/dig/settings/', methods=['GET'])
def dig_settings():
    """Allows to get information about current
    DIG settings (default type and allowed records to dig)."""
    data = {
        "default_type": DEFAULT_TYPE,
        "allowed_records": ALLOWED_RECORDS
    }
    return jsonify(data), HTTPStatus.OK


if __name__ == '__main__':
    app.run()
