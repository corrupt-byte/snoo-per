import discord
import json, asyncio, os
from discord.errors import Forbidden

from discord.ext import tasks, commands
from keep_alive import keep_alive
from itertools import cycle
from datetime import datetime


# If you are using a local .env file, and are having trouble getting it to load, try uncommenting the following lines:
# from pathlib import Path
# from dotenv import load_dotenv
# env_path = Path('.') / '.env'
# load_dotenv(dotenv_path=env_path)

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_SECRET")
DEFAULT_PREFIX = os.getenv("BOT_DEFAULT_PREFIX")

def get_prefix(client, message):
    with open('data/servers.json', 'r') as f: options = json.load(f) # Opens up the servers data file
    return commands.when_mentioned_or(*options[str(message.guild.id)]["prefix"])(client, message) # Returns the current guild's prefix

client = commands.Bot(command_prefix = get_prefix, case_insensitive=True)
client.remove_command('help')
status = cycle([[2, "Reddit Threads"],
                [2, "Reddit Comments"],
                [3, "your DMs ;D"]
              ]) # [0] Playing — [1] Streaming — [2] Listening to — [3] Watching

def is_me(ctx): # Helps when adding commands that only the bot owner could use
    return ctx.author.id == 436093214613831684 # Your Discord user ID, change if you don't want cpuslavex86#4663 to be the registered author and have bot ownership.

def get_database(): # A function to return the database into a variable
    with open('data/servers.json', 'r') as f: return json.load(f)

def save_database(data): # A function to save the data from a variable
    with open('data/servers.json', 'w') as f: json.dump(data, f, indent=4)

@tasks.loop(seconds=120)
async def change_status():
    nxt = next(status)
    await client.change_presence(status=discord.Status.online, activity=discord.Activity(name=nxt[1], type=nxt[0]))

@client.event
async def on_ready():
    change_status.start() # Starts the [change_status] loop above
    ensure_guilds() # Checks if all joined guilds are saved to the bot's database
    print("> Operator, I'm Alive.\n") # Prints this message in the console, just to make sure everything is working

def ensure_guilds():
    db = get_database()
    for guild in client.guilds:
        if not str(guild.id) in db: db[str(guild.id)] = {"prefix": DEFAULT_PREFIX}
    save_database(db)

@client.event
async def on_guild_join(guild):
    welcome_embed = discord.Embed(title="Thanks for inviting me to your server :wave:",
                                  description="> Get notifications of new submissions or comments from any subreddit, whether specifying keywords or just get all releases!",
                                  colour=16729344, timestamp=datetime.now())
    welcome_embed.set_author(name=f"{client.user.name} 💬", icon_url=client.user.avatar_url)
    welcome_embed.set_footer(text="by: cpuslavex86#4663, Shizuka#2100")
    for chnl in guild.text_channels:
        try: await chnl.send(embed=welcome_embed)
        except Forbidden: continue
        else: break

    db = get_database()
    db[str(guild.id)] = {"prefix": DEFAULT_PREFIX}
    save_database(db)

@client.event
async def on_guild_remove(guild):
    db = get_database()
    db.pop(str(guild.id))
    save_database(db)
    
@client.command()
@commands.check(is_me) # Check for the defined function [is_me] that we created before
async def shutdown(ctx): # Utility command for shutting down the bot more easily
    await ctx.send(f'> Shutting Down...')
    await ctx.bot.logout()

path = "./cogs"
for filename in os.listdir(path):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}') # This loads extentions form the "cogs" file

@client.event
async def on_command_error(ctx, error): # Additional touch of mine :D (you are not gonna really find this anywhere)
    if isinstance(error, commands.MissingRequiredArgument):
        emb = discord.Embed(description="`⚠`  Please pass in all required arguments",
         colour = discord.Colour.red(),
         timestamp = ctx.message.created_at)
        emb.set_footer(text="Check {}help for command usages.".format(ctx.prefix))
        return await ctx.send(embed=emb)
    if isinstance(error, commands.MissingPermissions):
        emb = discord.Embed(description="`⚠` You don't have the permissions to perform this command!",
         colour = discord.Colour.red(),
         timestamp = ctx.message.created_at)
        emb.set_footer(text="error, commands.MissingPermissions")
        return await ctx.send(embed=emb)
    if isinstance(error, commands.CommandNotFound): return await ctx.message.add_reaction('❔')
    if isinstance(error, commands.BadArgument): return await ctx.send(error)
    if isinstance(error, commands.UserInputError):
        return await ctx.send('> Something went wrong.. Make sure you assigned the command arguments correctly.\nUsage: `{}{}`'.format(ctx.prefix, ctx.command.usage))

@client.event
async def on_message(message):
    if message.author.bot or not message.guild: return # Checks if the message sent in DM, or the sender is a bot. if yes, it cancels em
    await client.process_commands(message) # proceed. do not delete this or else your bot wont read commands

keep_alive()
client.run(DISCORD_BOT_TOKEN)
