import discord
from discord.ext import commands

import yaml

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", intents=intents)

def load_config():
    with open("config.yml", "r") as f:
        return yaml.load(f, Loader=yaml.FullLoader)

config = load_config()

bot.version = "v1.0"

@bot.event
async def on_ready():
    print(f"{bot.user} is ready!")
    
    # Load cogs
    await bot.load_extension("cogs.auto-thread")
    await bot.load_extension("cogs.keywords")
    await bot.load_extension("cogs.mod")

    await bot.tree.sync()
    
    print("All cogs loaded!")

if __name__ == "__main__":
    bot.run(config["token"])
