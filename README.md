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
* Docker (19.03.0+) with docker compose for easy run API

### Tech stack:
For bot: 
* python-telegram-bot as telegram API interface. 

For API: 
* FastAPI as API backend; 
* Uvicorn as ASGI server; 
* Nginx as web-server.

## Whois & Dig telegram bot

### How to install and use the bot manually:

<details>
<summary>
Instruction
</summary>

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
echo 'TOKEN=HERE-IS-YOUR-TELEGRAM-TOKEN' > src/.env
```

Start the bot:

```
python3 src/wd_telegram_bot.py
```

</details>


### How to run telegram bot via docker:

<details>
<summary>
Instruction
</summary>

Clone the repo and change directory to it:

```
git clone https://github.com/melax08/whois-and-dig.git
```

```
cd whois-and-dig
```

Create .env file and add your telegram bot token to it (see .env_example):

```
echo 'TOKEN=HERE-IS-YOUR-TELEGRAM-TOKEN' > src/.env
```

Build the image by Dockerfile.bot:
```
docker build -t wd_tg_bot -f Dockerfile.bot .
```
Create and run docker container:
```
docker run -it -d -v ${PWD}/logs:/app/logs --name wd_tg_bot wd_tg_bot
```

</details>


Example of tg bot conversation:

![bot_example.png](readme_imgs/bot_example.png)

## Whois & Dig REST API

### How to install WD REST API via docker

<details>
<summary>
Instruction
</summary>

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

</details>

### API usage:
With default nginx config, API runs on http://127.0.0.1.

If you want the api to work on a dedicated ip address, or on a domain, change the directive **server_name** in **api_docker/nginx/default.conf** file.

In a running application, you can find the **swagger documentation** along the path: http://127.0.0.1/docs

### Example of requests to the working API:

Get dig settings like default type or allowed records:
```shell
curl -X GET http://127.0.0.1/api/v1/dig/settings/
```

Get dig information about A-records on domain google.com on DNS-servers 1.1.1.1 and 8.8.8.8
```shell
curl -X POST http://127.0.0.1/api/v1/dig/ \
-H "Content-Type: application/json" \
-d '{"domain": "google.com", "record": "A", "dns": ["1.1.1.1", "8.8.8.8"]}'
```

Get whois information about domain google.com:
```shell
curl -X POST http://127.0.0.1/api/v1/whois/ \
-H "Content-Type: application/json" \
-d '{"domain": "google.com"}'
```