import whois

from wd_bot import di, who, TOKEN, domain_fixer, domain_encode


def t_whois(domain):
    domain = whois.query(domain)
    print(domain.__dict__)


def t_message():
    """Test function, don't use it in production."""
    from telegram import Bot
    bot = Bot(token=TOKEN)
    chat_id = '159956275'
    text = di('google.com', 'TXT')
    # text = who('google.com')
    print(text)
    bot.send_message(chat_id,
                     text,
                     disable_web_page_preview=True,
                     parse_mode='HTML')
