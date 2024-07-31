import interactions
import json
from interactions import Intents, listen


def load_config():
    with open("config.json") as config_file:
        config_data = json.load(config_file)
    return config_data


config = load_config()
bot_token = config["token"]
client_id = config["client_id"]
guild_id = config["guild_id"]

bot = interactions.Client(
    intents=Intents.DEFAULT,
    status="online",
    activity="with checklists",
)


@listen()
async def on_startup():
    print(f"Logged in as {bot.user.tag}")


bot.load_extension("src.slashCommands")
bot.start(bot_token)
