from constants import ALLOWED_RECORDS

bad_domain = '❗ Bad domain. Maybe you need some /help?'
domain_not_registred = 'Domain is not registred!'
unknown_tld = "❗ I don't know this second-level domain, but let's try some DIG 🌚"
wrong_request = '❗ You send the wrong request. Maybe you need some /help?'
help_text = (f'<b>How to use</b>\n\n ✅ '
             'Correct:\n '
             'example.com A\n '
             'http://example.com/ TXT\n '
             'site.ru\n\n '
             '❌ Wrong:\n'
             'A example.com\n '
             'example.com A TXT MX\n\n'
             f'Allowed <b>dig</b> records to check: {", ".join(ALLOWED_RECORDS)}')
error_log = 'User: {}. Input message: {}. Error: {}'
new_exception = 'New exception was happened. User: {}. Input message: {} Error: {}'