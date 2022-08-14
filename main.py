from ytstats import YTstats
import discord
from discord.ext.commands import has_permissions, MissingPermissions
from discord.ext.commands import Bot
from asyncio import sleep
import json


def getConfig():
    with open("config.json") as f:
        return json.load(f)


def human_format(num: float, force=None, ndigits=3):
    perfixes = ("p", "n", "u", "m", "", "k", "m", "g", "t")
    one_index = perfixes.index("")
    if force:
        if force in perfixes:
            index = perfixes.index(force)
            magnitude = 3 * (index - one_index)
            num = num / (10 ** magnitude)
        else:
            raise ValueError("force value not supported.")
    else:
        div_sum = 0
        if abs(num) >= 1000:
            while abs(num) >= 1000:
                div_sum += 1
                num /= 1000
        else:
            while abs(num) <= 1:
                div_sum -= 1
                num *= 1000
        temp = round(num, ndigits) if ndigits else num
        if temp < 1000:
            num = temp
        else:
            num = 1
            div_sum += 1
        index = one_index + div_sum
    return str(num).rstrip("0").rstrip(".") + perfixes[index]


client = Bot(command_prefix=getConfig()["bot-prefix"])


@client.event
async def on_ready():
    print("We have logged in as {0.user}".format(client))

    config = getConfig()
    if config["status"]["type"] == "playing":
        await client.change_presence(
            activity=discord.Game(name=config["status"]["value"])
        )
    elif config["status"]["type"] == "streaming":
        await client.change_presence(
            activity=discord.Streaming(
                name=config["status"]["value"], url="https://www.twitch.tv/"
            )
        )
    elif config["status"]["type"] == "watching":
        await client.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching, name=config["status"]["value"]
            )
        )
    elif config["status"]["type"] == "competing":
        await client.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.competing, name=config["status"]["value"]
            )
        )
    elif config["status"]["type"] == "listening":
        await client.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening, name=config["status"]["value"]
            )
        )

    while True:
        config = getConfig()
        python_engineer_id = config["youtube-channel-id"]
        channel_id = python_engineer_id

        yt = YTstats(config["google-api-key"], channel_id)
        yt.extract_all()
        yt.dump()

        with open("youtube.json") as f:
            data = json.load(f)
            stats = data[config["youtube-channel-id"]]["channel_statistics"]
            views = client.get_channel(config["channels"]["views"])
            subs = client.get_channel(config["channels"]["subs"])
            videos = client.get_channel(config["channels"]["videos"])
            await views.edit(
                name=config["formats"]["views"].format(
                    human_format(int(stats["viewCount"]))
                )
            )
            await subs.edit(
                name=config["formats"]["subs"].format(
                    human_format(int(stats["subscriberCount"]))
                )
            )
            await videos.edit(
                name=config["formats"]["videos"].format(
                    human_format(int(stats["videoCount"]))
                )
            )
        print("Updated")
        await sleep(60)


client.remove_command("help")


@client.command(name="help", pass_context=True)
async def help(ctx):
    embed = discord.Embed(title="YouTube Bot Help", color=0x6D9ED7)
    embed.add_field(
        name=f"{getConfig()['bot-prefix']}forceupdate",
        value="*Force updates cached channel data & channel names.",
        inline=False,
    )
    embed.add_field(
        name=f"{getConfig()['bot-prefix']}settings (category) [selection] [value]",
        value="*Alter bot settings.",
        inline=False,
    )
    embed.add_field(
        name=f"{getConfig()['bot-prefix']}stats",
        value="Displays YouTube statistics.",
        inline=False,
    )
    embed.add_field(
        name=f"{getConfig()['bot-prefix']}help",
        value="Displays this page.",
        inline=False,
    )
    embed.set_footer(text="Bot by jaa.am -  * requires the 'Manage Server' permission.")
    await ctx.reply(embed=embed)


@client.command(name="stats", pass_context=True)
async def stats(ctx):
    with open("youtube.json") as f:
        data = json.load(f)
        config = getConfig()
        embed = discord.Embed(title="YouTube Statistics", color=0x6D9ED7)
        embed.add_field(
            name="Views",
            value=f"{int(data[config['youtube-channel-id']]['channel_statistics']['viewCount']):,}",
            inline=True,
        )
        embed.add_field(
            name="Subs",
            value=f"{int(data[config['youtube-channel-id']]['channel_statistics']['subscriberCount']):,}",
            inline=True,
        )
        embed.add_field(
            name="Videos",
            value=f"{int(data[config['youtube-channel-id']]['channel_statistics']['videoCount']):,}",
            inline=True,
        )
        embed.set_footer(text="This data is cached and will update every 5 minutes.")
        await ctx.reply(embed=embed)


@client.command(name="forceupdate", pass_context=True)
@has_permissions(manage_guild=True)
async def forceupdate(ctx):
    config = getConfig()
    python_engineer_id = config["youtube-channel-id"]
    channel_id = python_engineer_id

    yt = YTstats(config["google-api-key"], channel_id)
    yt.extract_all()
    yt.dump()
    with open("youtube.json") as f:
        data = json.load(f)
        stats = data[config["youtube-channel-id"]]["channel_statistics"]
        views = client.get_channel(config["channels"]["views"])
        subs = client.get_channel(config["channels"]["subs"])
        videos = client.get_channel(config["channels"]["videos"])
        await views.edit(
            name=config["formats"]["views"].format(
                human_format(int(stats["viewCount"]))
            )
        )
        await subs.edit(
            name=config["formats"]["subs"].format(
                human_format(int(stats["subscriberCount"]))
            )
        )
        await videos.edit(
            name=config["formats"]["videos"].format(
                human_format(int(stats["videoCount"]))
            )
        )
    await ctx.reply("Updated channel names & cached data.")


@client.command(name="settings", pass_context=True)
@has_permissions(manage_guild=True)
async def settings(ctx, subcategory=None, selection=None, *, value=None):
    if subcategory == None and selection == None:
        embed = discord.Embed(
            title="Categories",
            description=f"Edit settings with ``{getConfig()['bot-prefix']}settings (category) [selection] [value]``",
            color=0x6D9ED7,
        )
        # config = getConfig()
        embed.add_field(name="Channels", value=f"Edit channels.", inline=True)
        embed.add_field(name="Formats", value=f"Edit formats.", inline=True)
        embed.add_field(name="Status", value=f"Edit bot status.", inline=True)
        await ctx.reply(embed=embed)
    elif subcategory.lower() == "channels" and selection == None:
        config = getConfig()["channels"]
        embed = discord.Embed(
            title="Channels",
            description="Edit channels that get edited.",
            color=0x6D9ED7,
        )
        embed.add_field(
            name="Views", value="<#{}>".format(config["views"]), inline=True
        )
        embed.add_field(name="Subs", value="<#{}>".format(config["subs"]), inline=True)
        embed.add_field(
            name="Videos", value="<#{}>".format(config["videos"]), inline=True
        )
        await ctx.reply(embed=embed)
    elif subcategory.lower() == "formats" and selection == None:
        config = getConfig()["formats"]
        embed = discord.Embed(
            title="Channels",
            description="Change the format of edits made by the bot.",
            color=0x6D9ED7,
        )
        embed.add_field(
            name="Views", value=f"``{config['views'].format('[Views]')}``", inline=True
        )
        embed.add_field(
            name="Subs", value=f"``{config['subs'].format('[Subs]')}``", inline=True
        )
        embed.add_field(
            name="Videos",
            value=f"``{config['videos'].format('[Videos]')}``",
            inline=True,
        )
        embed.set_footer(text="Tip: Use '{}' as a placeholder for numerical values.")
        await ctx.reply(embed=embed)
    elif subcategory.lower() == "status" and selection == None:
        config = getConfig()["status"]
        embed = discord.Embed(
            title="Status",
            description="Change the bot's Discord status.",
            color=0x6D9ED7,
        )
        embed.add_field(name="Type", value=f"{config['type']}", inline=True)
        embed.add_field(name="Value", value=f"``{config['value']}``", inline=True)
        await ctx.reply(embed=embed)
    elif (
        subcategory.lower() == "status"
        and selection.lower() == "type"
        and value != None
    ):
        if value.lower() not in [
            "playing",
            "streaming",
            "watching",
            "competing",
            "listening",
        ]:
            await ctx.reply(
                "Try again with a valid status type. (Playing, streaming, watching, competing, or listening)"
            )
            return
        with open("config.json", "r+") as f:
            data = json.load(f)
            data[subcategory.lower()][selection.lower()] = value
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
        config = getConfig()
        if config["status"]["type"] == "playing":
            await client.change_presence(
                activity=discord.Game(name=config["status"]["value"])
            )
        elif config["status"]["type"] == "streaming":
            await client.change_presence(
                activity=discord.Streaming(
                    name=config["status"]["value"], url="https://www.twitch.tv/"
                )
            )
        elif config["status"]["type"] == "watching":
            await client.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching, name=config["status"]["value"]
                )
            )
        elif config["status"]["type"] == "competing":
            await client.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.competing, name=config["status"]["value"]
                )
            )
        elif config["status"]["type"] == "listening":
            await client.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.listening, name=config["status"]["value"]
                )
            )
        embed = discord.Embed(
            title="Edited Settings",
            description=f"Successfully changed {subcategory.lower()} {selection.lower()} to {str(value)}.",
            color=0x6D9ED7,
        )
        await ctx.reply(embed=embed)
    elif (
        subcategory.lower() == "status"
        and selection.lower() == "value"
        and value != None
    ):
        if len(value) >= 128:
            await ctx.reply("Try again with a value less than 128 characters.")
            return
        with open("config.json", "r+") as f:
            data = json.load(f)
            data[subcategory.lower()][selection.lower()] = value
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
        config = getConfig()
        if config["status"]["type"] == "playing":
            await client.change_presence(
                activity=discord.Game(name=config["status"]["value"])
            )
        elif config["status"]["type"] == "streaming":
            await client.change_presence(
                activity=discord.Streaming(
                    name=config["status"]["value"], url="https://www.twitch.tv/"
                )
            )
        elif config["status"]["type"] == "watching":
            await client.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching, name=config["status"]["value"]
                )
            )
        elif config["status"]["type"] == "competing":
            await client.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.competing, name=config["status"]["value"]
                )
            )
        elif config["status"]["type"] == "listening":
            await client.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.listening, name=config["status"]["value"]
                )
            )
        embed = discord.Embed(
            title="Edited Settings",
            description=f"Successfully changed {subcategory.lower()} {selection.lower()} to {str(value)}.",
            color=0x6D9ED7,
        )
        await ctx.reply(embed=embed)

    elif (
        subcategory.lower() == "channels"
        and selection.lower() in ["views", "subs", "videos"]
        and value != None
    ):
        try:
            await client.fetch_channel(value)
        except:
            await ctx.reply("Please try again with a valid channel.")
            return
        with open("config.json", "r+") as f:
            data = json.load(f)
            data[subcategory.lower()][selection.lower()] = int(value)
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()

        embed = discord.Embed(
            title="Edited Settings",
            description=f"Successfully changed {subcategory.lower()} channel to <#{str(value)}>.",
            color=0x6D9ED7,
        )
        embed.set_footer(
            text="The channel's title will be updated within the next 5~ minutes."
        )
        await ctx.reply(embed=embed)
    elif (
        subcategory.lower() == "formats"
        and selection.lower() in ["views", "subs", "videos"]
        and value != None
    ):
        if "{}" not in value:
            await ctx.reply(
                "Make sure to include '{}', as it will be replaced with view/sub/video values."
            )
            return
        with open("config.json", "r+") as f:
            data = json.load(f)
            data[subcategory.lower()][selection.lower()] = value
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()

        embed = discord.Embed(
            title="Edited Settings",
            description=f"Successfully changed {subcategory.lower()} format to ``{value}``.",
            color=0x6D9ED7,
        )
        embed.set_footer(
            text="The channel's title will be updated within the next 5~ minutes."
        )
        await ctx.reply(embed=embed)


client.run(getConfig()["bot-token"])
