from constants import ALLOWED_RECORDS

# Information messages
WRONG_REQUEST = '❗ You send the wrong request. Maybe you need some /help?'
HELP_TEXT = (
    '<b>How to use</b>\n\n ✅ '
    'Correct:\n'
    'example.com A\n'
    'http://example.com/ TXT\n'
    'site.ru\n\n'
    '❌ Wrong:\n'
    'A example.com\n'
    'example.com A TXT MX\n\n'
    f'Allowed <b>dig</b> records to check: {", ".join(ALLOWED_RECORDS)}'
)

# Domain problems
BAD_DOMAIN = '❗ Bad domain. Maybe you need some /help?'
DOMAIN_NOT_REGISTERED = 'Domain is not registered!'
UNKNOWN_TLD = (
    "❗ I don't know this second-level domain, but let's try some DIG 🌚"
)

# Dig messages
DIG_TG_LABEL = '🔍 Here is DIG {}:'
DIG_EMPTY_RESPONSE = '- empty -'
DIG_RECORD_AT_NS = '\n▫ {} at {}:'

# Whois messages
WHOIS_TG_LABEL = '🔍 Here is whois information:'
NO_QUERY = 'No entries found for the selected source'
WHOIS_ERROR = '❗ Whois error: {}. Trying to dig...'

# Logging messages
SOMEONE_STARTS_BOT = 'Someone starts bot: {}, {} {}, {}'
ERROR_LOG = 'User: {}. Input message: {}. Error: {}'
NEW_EXCEPTION = (
    'New exception was happened. User: {}. Input message: {} Error: {}'
)
BAD_DOMAIN_LOG = 'Bad domain'
