import discord, asyncio, json

from discord import colour
from discord.ext import commands

class Utilities(commands.Cog):
    """Server & bot essential commands :thumbs_up:"""
    def __init__(self, client):
        self.client = client
        self.embedColor = 5814783

    @commands.command(description="Displays information about all bot commands and modules",
                      usage="help (module/command)", aliases=['h'])
    @commands.has_permissions(embed_links=True)
    async def help(self, ctx, topic:str = None):
        if not topic:
            with open('data/servers.json', 'r') as f: db = json.load(f)
            await ctx.send("> The prefix for this guild is `"+db[str(ctx.guild.id)]['prefix']+'`')

            halp = discord.Embed(color = self.embedColor)
            halp.set_author(name="{}'s Commands & Modules".format(self.client.user.name), icon_url = self.client.user.avatar_url)
            halp.set_footer(text="Use [{}help <cmd>] for command usage.".format(db[str(ctx.guild.id)]['prefix']))
            for cog in self.client.cogs:
                _desc = ''
                for cmd in (self.client.get_cog(cog)).get_commands(): _desc += f'`{cmd.name}` '
                halp.add_field(name='— '+cog, value=_desc, inline=False)
            return await ctx.send(embed=halp)
        else:
            if self.client.get_cog(topic.title()):
                cog = self.client.get_cog(topic.title())
                halp = discord.Embed(title='— '+cog.qualified_name+' Module', description=cog.__doc__+'\n\nCommands:', color = self.embedColor)
                halp.set_author(name="{}'s Commands & Modules".format(self.client.user.name), icon_url = self.client.user.avatar_url)
                _desc = ''
                for cmd in cog.get_commands():
                    halp.add_field(name='`'+cmd.usage+'`', value='> '+cmd.description)
                return await ctx.send(embed=halp)
            elif self.client.get_command(topic.lower()):
                cmd = self.client.get_command(topic.lower())
                halp = discord.Embed(title=f'— `{ctx.prefix}'+cmd.name+'` Command', description='> '+cmd.description, color = self.embedColor)
                halp.set_author(name="{}'s Commands & Modules".format(self.client.user.name), icon_url = self.client.user.avatar_url)
                halp.add_field(name="Usage:", value=f'`{ctx.prefix}'+cmd.usage+'`')
                if cmd.aliases: halp.add_field(name="Aliases:", value=''.join(al+', ' for al in cmd.aliases))
                if cmd.brief: halp.add_field(name="Examples:", value=''.join(f'`{ctx.prefix}'+ex+'`\n' for ex in cmd.brief), inline=False)
                return await ctx.send(embed=halp)

    @commands.command(description="Change the bot's prefix for this guild", usage="prefix <PREFIX>", aliases=['setprefix'])
    async def prefix(self, ctx, PR:str):
        with open('data/servers.json', 'r') as f: db = json.load(f)
        if PR != db[str(ctx.guild.id)]['prefix']:
            db[str(ctx.guild.id)]['prefix'] = PR
            with open('data/servers.json', 'w') as f: json.dump(db, f, indent=4)
            await ctx.send(embed=discord.Embed(title="Successfully changed this guild's prefix to `"+PR+'`', timestamp=ctx.message.created_at, colour=self.embedColor).set_author(name=f'{ctx.author} —', icon_url=ctx.author.avatar_url))
        else: await ctx.send(ctx.author.mention+', The prefix for this guild is already set to `'+PR+'`')


def setup(client):
    client.add_cog(Utilities(client))