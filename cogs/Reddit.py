from inspect import currentframe
import discord, asyncio, json, os, re
from discord import colour, client
from discord.errors import Forbidden
from discord.ext import commands, tasks

import praw
from prawcore import NotFound

import time
from datetime import datetime, timedelta

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER = os.getenv("REDDIT_USER")
REDDIT_PASS = os.getenv("REDDIT_PASS")

reddit = praw.Reddit(client_id = REDDIT_CLIENT_ID,
                     client_secret = REDDIT_CLIENT_SECRET,
                     username = REDDIT_USER,
                     password = REDDIT_PASS,
                     user_agent = 'cpuslavex86')

def get_database(file_name:str):
    with open('data/{}'.format(file_name), 'r') as f: return json.load(f)

def sub_exists(subreddit:str):
    exists = True
    try: reddit.subreddits.search_by_name(subreddit, exact=True)
    except NotFound: exists = False
    return exists

def human_format(num):
    if num < 1000 : return num
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    # add more suffixes if you need them
    return '%.1f%s' % (num, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])

class InvalidEntry(commands.CommandError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class Reddit(commands.Cog):
    """Get new posts or comments from any multiple specific subreddits, containing the keywords specified!"""
    def __init__(self, client):
        self.client = client
        self.embedColor = 16729344
        self.database = get_database('reddit.json')

        self._LOGS = get_database('_.log')
        self._SENT = []

    def get_section_dir(self, guild_id, channel_id):
        rslt = next(item for item in self.database[str(guild_id)]["sections"] if item["id"] == channel_id)
        return rslt, self.database[str(guild_id)]["sections"].index(rslt)
    def save_section(self, guild_id, SCTNS, INDX):
        self.database[str(guild_id)]['sections'][INDX] = SCTNS
    def ensure_guilds_data(self):
        for guild in self.client.guilds:
            if not str(guild.id) in self.database: self.database[str(guild.id)] = {"channels": [], "sections": []}

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, InvalidEntry): return await ctx.send(f"{ctx.author.mention}, {error}")

    @commands.Cog.listener()
    async def on_ready(self):
        self.ensure_guilds_data()
        self.check_new.start()
        self.update_values.start()
        self.save_data.start()

    @commands.Cog.listener()
    async def on_guild_join(self, guild): self.database[str(guild.id)] = {"channels": [], "sections": []}

    @commands.Cog.listener()
    async def on_guild_remove(self, guild): self.database.pop(str(guild.id))

    @tasks.loop(seconds=10)
    async def save_data(self):
        with open('data/reddit.json', 'w') as f: json.dump(self.database, f, indent=4)
        with open('data/reddit.json', 'r') as f: self.database = json.load(f)

    @tasks.loop(seconds=20)
    async def check_new(self):
        for guild in self.client.guilds:
            if not str(guild.id) in self._LOGS: self._LOGS[str(guild.id)] = []
            _CHECKED = ([] if not self._LOGS[str(guild.id)] else self._LOGS[str(guild.id)])
            if str(guild.id) in self.database:
                if self.database[str(guild.id)]["channels"]:
                    for _CHANNELID in self.database[str(guild.id)]["channels"]:
                        SCTN = next(item for item in self.database[str(guild.id)]["sections"] if item["id"] == _CHANNELID)
                        _SUBS, _KEYS, _FILTER = SCTN["subreddits"], SCTN["keywords"], SCTN["filter"]
                        if _SUBS:
                            _CHANNEL = self.client.get_channel(_CHANNELID)
                            for subreddit in _SUBS:
                                sb = reddit.subreddit(subreddit)
                                for submission in sb.new(limit=5):
                                    if not submission.stickied:
                                        if (submission.id not in _CHECKED) and (_FILTER in ['ALL', 'SUBMISSIONS']):
                                            _CHECKED.append(submission.id)
                                            if _KEYS:
                                                for phrase in _KEYS:
                                                    if (str(re.sub(r'([^\s\w]|_)+', '', phrase.lower())) in str(submission.title).lower()) or (str(re.sub(r'([^\s\w]|_)+', '', phrase.lower())) in str(submission.selftext).lower()):
                                                        _title = submission.title[:240]+'...' if len((submission.title).strip()) > 240 else submission.title
                                                        _desc = f'{submission.selftext[:1800]}... [Read more](https://www.reddit.com/r/{sb.display_name}/comments/{submission.id}/)' if len((submission.selftext).strip()) > 1800 else submission.selftext
                                                        emb = discord.Embed(title=_title, description=f"[[URL](https://www.reddit.com/r/{sb.display_name}/comments/{submission.id}/)] {_desc}", timestamp=datetime.now(), colour=self.embedColor)
                                                        emb.set_image(url=submission.url)
                                                        emb.set_author(name=f"r/{sb.display_name} • Posted by u/{submission.author.name}", icon_url=submission.author.icon_img)
                                                        num_likes = (0 if not submission.likes else submission.likes)
                                                        emb.set_footer(text=f"🔺{human_format(int(num_likes))} Upvotes • 💬{human_format(submission.num_comments)} Comments")
                                                        msg = await _CHANNEL.send(embed=emb)
                                                        self._SENT.append([msg, 'submission', submission.id, str(sb.display_name)])
                                                        break
                                            else: # I guess just using the simple way would do
                                                _title = submission.title[:240]+'...' if len((submission.title).strip()) > 240 else submission.title
                                                _desc = f'{submission.selftext[:1800]}... [Read more](https://www.reddit.com/r/{sb.display_name}/comments/{submission.id}/)' if len((submission.selftext).strip()) > 1800 else submission.selftext
                                                emb = discord.Embed(title=_title, description=f"[[URL](https://www.reddit.com/r/{sb.display_name}/comments/{submission.id}/)] {_desc}", timestamp=datetime.now(), colour=self.embedColor)
                                                emb.set_image(url=submission.url)
                                                emb.set_author(name=f"r/{sb.display_name} • Posted by u/{submission.author.name}", icon_url=submission.author.icon_img)
                                                num_likes = (0 if not submission.likes else submission.likes)
                                                emb.set_footer(text=f"🔺{human_format(int(num_likes))} Upvotes • 💬{human_format(submission.num_comments)} Comments")
                                                msg = await _CHANNEL.send(embed=emb)
                                                self._SENT.append([msg, 'submission', submission.id, str(sb.display_name)])
                                                break
                                        if _FILTER in ['ALL', 'COMMENTS']:
                                            for comment in submission.comments:
                                                if comment.id not in _CHECKED:
                                                    _CHECKED.append(comment.id)
                                                    if _KEYS:
                                                        for phrase in _KEYS:
                                                            if str(re.sub(r'([^\s\w]|_)+', '', phrase.lower())) in str(comment.body).lower():
                                                                _desc = comment.body[:1900]+'...' if len((comment.body).strip()) > 1900 else comment.body
                                                                emb = discord.Embed(description=f"[[URL](https://www.reddit.com/r/{sb.display_name}/comments/{submission.id}/)] "+_desc, timestamp=datetime.now(), colour=self.embedColor)
                                                                emb.set_author(name=f"r/{sb.display_name} • Commented by u/{comment.author.name}", icon_url=comment.author.icon_img)
                                                                await _CHANNEL.send(embed=emb)
                                                                break
                                                    else:
                                                        _desc = comment.body[:1900]+'...' if len((comment.body).strip()) > 1900 else comment.body
                                                        emb = discord.Embed(description=f"[[URL](https://www.reddit.com/r/{sb.display_name}/comments/{submission.id}/)] "+_desc, timestamp=datetime.now(), colour=self.embedColor)
                                                        emb.set_author(name=f"r/{sb.display_name} • Commented by u/{comment.author.name}", icon_url=comment.author.icon_img)
                                                        await _CHANNEL.send(embed=emb)
                                                        break
                self._LOGS[str(guild.id)] = _CHECKED
        
        with open('data/_.log', 'w') as f: json.dump(self._LOGS, f, indent=4)

    @tasks.loop(seconds=300)
    async def update_values(self):
        for chunk in self._SENT:
            if chunk[1] == 'submission':
                submission = reddit.submission(id=chunk[2])
                _msg = chunk[0]

                _title = submission.title[:240]+'...' if len((submission.title).strip()) > 240 else submission.title
                _desc = f'{submission.selftext[:1800]}... [Read more](https://www.reddit.com/r/{submission.subreddit.display_name}/comments/{submission.id}/)' if len((submission.selftext).strip()) > 1800 else submission.selftext
                emb = discord.Embed(title=_title, description=f"[[URL](https://www.reddit.com/r/{submission.subreddit.display_name}/comments/{submission.id}/)] {_desc}", timestamp=datetime.now(), colour=self.embedColor)
                emb.set_image(url=submission.url)
                emb.set_author(name=f"r/{chunk[3]} • Posted by u/{submission.author.name}", icon_url=submission.author.icon_img)
                num_likes = (0 if not submission.likes else submission.likes)
                emb.set_footer(text=f"🔺{human_format(int(num_likes))} Upvotes • 💬{human_format(submission.num_comments)} Comments")
                msg = await _msg.edit(embed=emb)

    @commands.group(name='reddit', invoke_without_command=True,
                    description="Get TOP, HOT or NEW submissions from any subreddit",
                    usage = "reddit <hot/new/top> <subreddit> <*limit> <*etc>", brief=['reddit new 15 r/all', 'reddit top 5 pics'])
    @commands.has_permissions(manage_guild=True)
    async def reddit(self, ctx): raise InvalidEntry("You should use a subcommand in order to receive something useful.")

    @reddit.command()
    @commands.has_permissions(manage_guild=True)
    async def hot(self, ctx, sb:str, _limit:int = None):
        _limit = 5 if not _limit else _limit
        if _limit > 30 or _limit < 1: raise InvalidEntry("Limit mentioned is either too high, or too low!")
        
        _subreddit = sb[2:] if sb.startswith('r/') else sb
        sub = reddit.subreddit(_subreddit)
        for submission in reddit.subreddit(_subreddit).hot(limit=_limit):
            _title = submission.title[:240]+'...' if len((submission.title).strip()) > 240 else submission.title
            _desc = f'{submission.selftext[:1800]}... [Read more](https://www.reddit.com/r/{sub.display_name}/comments/{submission.id}/)' if len((submission.selftext).strip()) > 1800 else submission.selftext
            emb = discord.Embed(title=_title, description=f"[[URL](https://www.reddit.com/r/{sub.display_name}/comments/{submission.id}/)] {_desc}", timestamp=datetime.now(), colour=self.embedColor)
            emb.set_image(url=submission.url)
            emb.set_author(name=f"r/{sub.display_name} • Posted by u/{submission.author.name}", icon_url=submission.author.icon_img)
            num_likes = (0 if not submission.likes else submission.likes)
            emb.set_footer(text=f"🔺{human_format(int(num_likes))} Upvotes • 💬{human_format(submission.num_comments)} Comments")
            await ctx.send(embed=emb)

    @reddit.command()
    @commands.has_permissions(manage_guild=True)
    async def new(self, ctx, sb:str, _limit:int = None):
        _limit = 5 if not _limit else _limit
        if _limit > 30 or _limit < 1: raise InvalidEntry("Limit mentioned is either too high, or too low!")
        
        _subreddit = sb[2:] if sb.startswith('r/') else sb
        sub = reddit.subreddit(_subreddit)
        for submission in sub.hot(limit=_limit):
            _title = submission.title[:240]+'...' if len((submission.title).strip()) > 240 else submission.title
            _desc = f'{submission.selftext[:1800]}... [Read more](https://www.reddit.com/r/{sub.display_name}/comments/{submission.id}/)' if len((submission.selftext).strip()) > 1800 else submission.selftext
            emb = discord.Embed(title=_title, description=f"[[URL](https://www.reddit.com/r/{sub.display_name}/comments/{submission.id}/)] {_desc}", timestamp=datetime.now(), colour=self.embedColor)
            emb.set_image(url=submission.url)
            emb.set_author(name=f"r/{sub.display_name} • Posted by u/{submission.author.name}", icon_url=submission.author.icon_img)
            num_likes = (0 if not submission.likes else submission.likes)
            emb.set_footer(text=f"🔺{human_format(int(num_likes))} Upvotes • 💬{human_format(submission.num_comments)} Comments")
            await ctx.send(embed=emb)

    @reddit.command()
    @commands.has_permissions(manage_guild=True)
    async def top(self, ctx, sb:str, _limit:int = None, timefilter:str = None):
        _limit = 5 if not _limit else _limit
        if _limit > 30 or _limit < 1: raise InvalidEntry("Limit mentioned is either too high, or too low!")
        timefilter = 'hour' if not timefilter else timefilter
        if timefilter.lower() in ['now', 'today']: timefilter = ['hour', 'day'][['now', 'today'].index(timefilter.lower())]
        # timefilter = 'hour' if timefilter == 'now' else timefilter
        # timefilter = 'day' if timefilter == 'today' else timefilter
        
        _subreddit = sb[2:] if sb.startswith('r/') else sb
        if timefilter.lower() in ['hour', 'week', 'month', 'day', 'year']:
            sub = reddit.subreddit(_subreddit)
            for submission in sub.top(time_filter=timefilter.lower(), limit=_limit):
                _title = submission.title[:240]+'...' if len((submission.title).strip()) > 240 else submission.title
                _desc = f'{submission.selftext[:1800]}... [Read more](https://www.reddit.com/r/{sub.display_name}/comments/{submission.id}/)' if len((submission.selftext).strip()) > 1800 else submission.selftext
                emb = discord.Embed(title=_title, description=f"[[URL](https://www.reddit.com/r/{sub.display_name}/comments/{submission.id}/)] {_desc}", timestamp=datetime.now(), colour=self.embedColor)
                emb.set_image(url=submission.url)
                emb.set_author(name=f"r/{sub.display_name} • Posted by u/{submission.author.name}", icon_url=submission.author.icon_img)
                num_likes = (0 if not submission.likes else submission.likes)
                emb.set_footer(text=f"🔺{human_format(int(num_likes))} Upvotes • 💬{human_format(submission.num_comments)} Comments")
                await ctx.send(embed=emb)
        else: raise InvalidEntry("Invalid time filter string.")
                    
    @commands.group(name="sections", invoke_without_command=True,
                    aliases=['channel'], description="Setup, modify or investigate a section (notify channel)",
                    usage="section <list/add/remove> *<args>", brief=["sections list", "sections add #memes"])
    async def sections(self, ctx):
        return await ctx.invoke(self.client.get_command('sections list'))

    @sections.command(name='list')
    async def _list(self, ctx):
        CHNLS = self.database[str(ctx.guild.id)]["channels"]
        if CHNLS:
            names = []
            for channel_id in CHNLS:
                channel = self.client.get_channel(channel_id)
                names.append(channel.name)
            
            _desc = ''.join('`#'+chnl+'` ' for chnl in names)
            emb = discord.Embed(title="This Guild's Channel Sections:", description='> '+_desc, colour=self.embedColor)
            emb.set_author(name=f'{ctx.guild.name} —', icon_url=ctx.guild.icon_url)
            await ctx.send(embed=emb)
        else: raise InvalidEntry("This guild did not assign any channel as a section yet")

    @sections.command()
    @commands.has_permissions(manage_guild=True)
    async def add(self, ctx, chnl:discord.TextChannel):
        # next(item for item in SCTS if item["id"] == chnl.id)
        if chnl.id not in self.database[str(ctx.guild.id)]["channels"]:
            self.database[str(ctx.guild.id)]["sections"].append({"id": chnl.id,
                                                                 "subreddits": [],
                                                                 "keywords": [],
                                                                 "filter": "ALL"})
            self.database[str(ctx.guild.id)]["channels"].append(chnl.id)
            await ctx.send(embed=discord.Embed(title=f"▸ Successfully created a section at #{chnl.name}", colour=self.embedColor).set_author(name=f'{ctx.author} —', icon_url=ctx.author.avatar_url))
        else: raise InvalidEntry("That channel is already assigned as a section!")

    @sections.command(description="Remove a channel from receiving Reddit submissions/comments", usage="remove <#channel>")
    @commands.has_permissions(manage_guild=True)
    async def remove(self, ctx, chnl:discord.TextChannel):  
        if chnl.id in self.database[str(ctx.guild.id)]["channels"]: pass
        else: raise InvalidEntry("That channel is not assigned as a notify section")

        self.database[str(ctx.guild.id)]["sections"].remove(next(item for item in self.database[str(ctx.guild.id)]["sections"] if item["id"] == chnl.id))
        self.database[str(ctx.guild.id)]["channels"].remove(chnl.id)
        await ctx.send(embed=discord.Embed(title=f"▸ Successfully removed the section at #{chnl.name}", colour=self.embedColor).set_author(name=f'{ctx.author} —', icon_url=ctx.author.avatar_url))

    @commands.command(description="Subscribe sectiom to a subreddit; to receive notifications from",
                      usage="addsubreddit <#channel> <subreddit>", brief=['addsubreddit #innersloth r/amongUs'],
                      aliases=['addsub','subadd','subredditadd','redditadd','subscribe','sub'])
    @commands.has_permissions(manage_guild=True)
    async def addsubreddit(self, ctx, chnl:discord.TextChannel, name:str):
        SCTNS, INDX = self.get_section_dir(ctx.guild.id, chnl.id)
        name = name[2:] if name.startswith('r/') else name
        if name.lower() not in SCTNS["subreddits"]:
            if sub_exists(name.lower()):
                SCTNS["subreddits"].append(name.lower())

                emb = discord.Embed(title="▸ Successfully subscribed to r/{}".format(name.capitalize()), colour=self.embedColor)
                emb.set_author(name=f'{ctx.author} —', icon_url=ctx.author.avatar_url)
                emb.set_footer(text=f"That channel will get notified of new posts & comments \nfrom in that subreddit that contain any of your keywords",
                            icon_url=ctx.guild.icon_url)
                await ctx.send(embed=emb)
            else: raise InvalidEntry("Couldn't find that subreddit!\n> Make sure that subreddit exists and you wrote the name correctly.")
        else: raise InvalidEntry("That channel is already subscribed to the mentioned subreddit.")
        self.save_section(ctx.guild.id, SCTNS, INDX)

    @commands.command(description="Unsubscribe a section from notifications of a subreddit",
                      usage="removesubreddit <#channel> <subreddit>", brief=['removesubreddit #gaming-news r/gaming'],
                      aliases=['unsubscribe','unsub','subredditremove','deletesubreddit'])
    @commands.has_permissions(manage_guild=True)
    async def removesubreddit(self, ctx, chnl:discord.TextChannel, name:str):
        SCTNS, INDX = self.get_section_dir(ctx.guild.id, chnl.id)
        sub = name[2:] if name.startswith('r/') else name
        if sub.lower() in SCTNS["subreddits"]:
            SCTNS["subreddits"].remove(sub.lower())

            emb = discord.Embed(title="▸ Successfully unsubscribed from r/{}".format(sub.capitalize()), colour=self.embedColor)
            emb.set_author(name=f'{ctx.author} —', icon_url=ctx.author.avatar_url)
            emb.set_footer(text="That channel will no longer receive notifications from that subreddit.", icon_url=ctx.guild.icon_url)
            await ctx.send(embed=emb)
        else: raise InvalidEntry("The mentioned channel is not subscribed to that subreddit!\n> Try making sure you wrote the name correctly.")
        self.save_section(ctx.guild.id, SCTNS, INDX)

    @commands.command(description="Get a list of each subreddit the specified channel subscribed to",
                      usage="listsubreddits <#channel>", aliases=['subslist','subredditslist','listsub','redditlist'])
    async def listsubreddits(self, ctx, chnl:discord.TextChannel):
        SCTNS, INDX = self.get_section_dir(ctx.guild.id, chnl.id)
        if SCTNS['subreddits']:
            _desc = ''.join('`r/'+sb.capitalize()+'` ' for sb in SCTNS['subreddits'])
            emb = discord.Embed(title="Subscribed Subreddits:", description='> '+_desc, colour=self.embedColor)
            emb.set_author(name=f'{ctx.guild.name} —', icon_url=ctx.guild.icon_url)
            await ctx.send(embed=emb)
        else: raise InvalidEntry("That channel is not subscribed to any subreddit yet")
    
    @commands.command(description="Add a word or phrase to a section's search-for keywords list",
                      usage="addkeyword <#channel> <phrase>..", brief=['addkeyword #minecraft Hardcore', 'addkeyword #eve The Wormhole Police'],
                      aliases=['addkey','keyadd','keywordadd','addword','wordadd','addphrase'])
    @commands.has_permissions(manage_guild=True)
    async def addkeyword(self, ctx, chnl:discord.TextChannel, *, phrase:str):
        SCTNS, INDX = self.get_section_dir(ctx.guild.id, chnl.id)
        phrase = re.sub(r'([^\s\w]|_)+', '', phrase)
        if phrase.lower() not in SCTNS["keywords"]:
            SCTNS["keywords"].append(phrase.lower())

            emb = discord.Embed(title="▸ Successfully added `{}` to the keywords list".format(phrase.upper()), colour=self.embedColor)
            emb.set_author(name=f'{ctx.author} —', icon_url=ctx.author.avatar_url)
            emb.set_footer(text="That channel will get notified if the subscribed subreddits\nposts or comments with that keyword", icon_url=ctx.guild.icon_url)
            await ctx.send(embed=emb)
        else: raise InvalidEntry("That word is already appended to that channel's keywords list!")
        self.save_section(ctx.guild.id, SCTNS, INDX)

    @commands.command(description="Remove a word or phrase from a section's search-for keywords list",
                      usage="removekeyword <#channel> <phrase>", aliases=['removeword','keywordremove','wordremove'])
    @commands.has_permissions(manage_guild=True)
    async def removekeyword(self, ctx, chnl:discord.TextChannel, phrase:str):
        SCTNS, INDX = self.get_section_dir(ctx.guild.id, chnl.id)
        phrase = re.sub(r'([^\s\w]|_)+', '', phrase)
        if phrase.lower() in SCTNS["keywords"]:
            SCTNS["keywords"].remove(phrase.lower())

            emb = discord.Embed(title="▸ Successfully removed `{}` from the keywords list".format(phrase.upper()), colour=self.embedColor)
            emb.set_author(name=f'{ctx.author} —', icon_url=ctx.author.avatar_url)
            emb.set_footer(text="This guild will no longer receive notifications of that keyword", icon_url=ctx.guild.icon_url)
            await ctx.send(embed=emb)
        else: raise InvalidEntry("That word is not stored in that channel's keywords list!")
        self.save_section(ctx.guild.id, SCTNS, INDX)

    @commands.command(description="Get a list of keywords i search for a specific channel",
                      usage="listkeywords <#channel>", aliases=['keyslist','wordslist','keywordslist','phrases','words','keywords'])
    async def listkeywords(self, ctx, chnl:discord.TextChannel):
        SCTNS, INDX = self.get_section_dir(ctx.guild.id, chnl.id)
        if SCTNS['keywords']:
            _desc = ''.join('`'+kw.upper()+'` ' for kw in SCTNS['keywords'])
            emb = discord.Embed(title="Search-For Keywords:", description='> '+_desc, colour=self.embedColor)
            emb.set_author(name=f'{ctx.guild.name} —', icon_url=ctx.guild.icon_url)
            await ctx.send(embed=emb)
        else: raise InvalidEntry("This guild did not set any keywords for that channel yet.")
    
    @commands.command(description="Apply a notifications filter, whether receiving submissons-only or comments-only, or both!\n<mode>s: `ALL`, `COMMENTS`, `SUBMISSIONS`",
                      usage="setfilter <#channel> <all/comments/submissions>", brief=['setfilter #art submissions'], aliases=['filter'])
    @commands.has_permissions(manage_guild=True)
    async def setfilter(self, ctx, chnl:discord.TextChannel, mode:str):
        SCTNS, INDX = self.get_section_dir(ctx.guild.id, chnl.id)
        if SCTNS["filter"] != mode.upper():
            if mode.lower() in ['all', 'comments', 'submissions']:
                SCTNS["filter"] = mode.upper()
                emb = discord.Embed(title=f"▸ Successfully that section's notifications filter to `{mode.upper()}`", colour=self.embedColor)
                emb.set_author(name=f'{ctx.author} —', icon_url=ctx.author.avatar_url)
                emb.set_footer(text="That channel will get notified if its subscribed subreddits\nposts only the filtered string", icon_url=ctx.guild.icon_url)
                await ctx.send(embed=emb)
            else: raise InvalidEntry("Invalid mode entry!\n> Available modes: `ALL`, `COMMENTS`, `SUBMISSIONS`")
        else: raise InvalidEntry(f"That channel's notifications is already filtered to `{mode.upper()}`")
        self.save_section(ctx.guild.id, SCTNS, INDX)

    @addsubreddit.before_invoke
    @removesubreddit.before_invoke
    @listsubreddits.before_invoke
    @addkeyword.before_invoke
    @removekeyword.before_invoke
    @listkeywords.before_invoke
    @setfilter.before_invoke
    async def ensure_assignment(self, ctx):
        chnl = ctx.args[2]   
        if chnl.id in self.database[str(ctx.guild.id)]["channels"]: pass
        else: raise InvalidEntry("That channel is not assigned as a notify section")

    @top.before_invoke
    @new.before_invoke
    @hot.before_invoke
    async def ensure_subreddit(self, ctx):
        sb = ctx.args[2]
        subreddit = sb[2:] if sb.startswith('r/') else sb
        if sub_exists(subreddit.lower()): pass
        else: raise InvalidEntry("Couldn't find that subreddit!\n> Make sure that subreddit exists and you wrote the name correctly.")


def setup(client):
    client.add_cog(Reddit(client))
