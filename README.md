# Installation and Usage
Clone recursively with 

```bash
git clone --recursive https://github.com/icyveins7/seoorderbot.git
```

If you have cloned it before and wish to pull updates, remember to update the submodules as well

```bash
git pull
git submodule update --remote
```

Install all requirements with

```bash
pip install -r requirements.txt
```

Run the main script with your token (here shown saved as an environment variable)
and your ID (as the admin of the bot, for some commands). Ask @userinfobot
for your ID if you don't know it.

```bash
python orderbot.py $TELEGRAM_BOT_TOKEN 12345678
```

