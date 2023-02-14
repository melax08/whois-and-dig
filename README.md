# Whois & dig telegram bot and API

## Information

### Description
This project contains various handy representations of domain analysis utilities such as whois and dig.
### Content
1. Whois & Dig telegram bot.
2. Whois & Dig REST API
3. Dockerfiles to easy create docker images for both of bot and API.

### System requirements:

* Python: 3.7+
* Operating system: Linux or MacOS
* Installed whois and dig (dnsutils) programs

## Whois & Dig telegram bot

### How to install and use the bot manually:

Clone the repo and change directory to it:

```
git clone https://github.com/melax08/whois-and-dig.git
```

```
cd whois-and-dig
```

Create and activate virtual environment:

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

### How to run telegram bot via docker:
Clone the repo and change directory to it:

```
git clone https://github.com/melax08/whois-and-dig.git
```

```
cd whois-and-dig
```

Create .env file and add your telegram bot token to it (see .env_example):

```
echo 'TOKEN=HERE-IS-YOUR-TELEGRAM-TOKEN' > .env
```

Build the image by Dockerfile.bot:
```
docker build -t wd_tg_bot -f Dockerfile.bot .
```
Create and run docker container:
```
docker run -it -d --name wd_tg_bot wd_tg_bot
```

Example of tg bot conversation:

![tg_bot_example](https://2241.ru/scr/example_of_bot.jpeg)

## Whois & Dig REST API

### How to install WD REST API via docker

1. Clone the repo and change directory to api_docker dir in it:

```
git clone https://github.com/melax08/whois-and-dig.git
```

```
cd whois-and-dig/api_docker
```
2. Fill up the .env file, like .env_example file:

```
mv .env_example .env
nano .env
```
3. Run docker-compose:
```
docker-compose up -d
```
4. Create the django superuser:
```
docker-compose exec backend python manage.py createsuperuser
```
5. Send POST-request to http://127.0.0.1/api/v1/get-token/ with JSON:
```json
{
    "username": "YOUR-USERNAME",
    "password": "YOUR-PASSWORD"
}
```

* YOUR-USERNAME - your superuser username;
* YOUR-PASSWORD - your superuser password;

You will obtain token, use it to all future requests to API:

- Specify the Authorization header with value: Token YOUR-TOKEN