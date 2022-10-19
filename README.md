### System requirements:

* Python: 3.7-3.10
* Operating system: Linux or MacOS

### How to install and use the bot:

Clone the repo and change directory to it:

```
git clone https://github.com/melax08/whois-and-dig.git
```

```
cd whois-and-dig
```

Create and activate a virtual environment:

```
python3 -m venv venv
```

```
source venv/bin/activate
```

Install python dependencies from the file requirements.txt:

```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Create .env file and add your telegram bot token to it (see .env_example):

```
echo 'TOKEN=HERE-IS-YOUR-TELEGRAM-TOKEN' > .env
```

Start the bot:

```
python3 wd_bot.py
```