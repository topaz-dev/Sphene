import discord
from discord.ext import commands
from discord.ext.commands import Bot
import asyncio
import aiohttp
import json
import re
from datetime import datetime
from core import gestion as ge
from languages import lang
from database import SQLite as sql
from apscheduler.schedulers.asyncio import AsyncIOScheduler


PREFIX = open("core/prefix.txt", "r").read().replace("\n", "")
client = Bot(command_prefix = "{0}".format(PREFIX))

############# Notification variables ################
TWITCH_CLIENT_ID = open("multimedia/twitch_client_id.txt", "r").read().replace("\n", "")
TWITCH_SECRET_ID = open("multimedia/twitch_secret_id.txt", "r").read().replace("\n", "")
unresolved_ids = 0

# Reset all sent key values to false
global local
with open('multimedia/local.json', 'r') as fp:
    reset_values = json.load(fp)

for streams_index in reset_values['streams']:
    streams_index['sent'] = 'false'
with open('multimedia/local.json', 'w') as fp:
    json.dump(reset_values, fp, indent=2)

with open('multimedia/local.json', 'r') as fp:
    local = json.load(fp)

api = {}

global counter
global first_startup
first_startup = 1
scheduler = AsyncIOScheduler()


async def load(C):
    tuple = [C]
    await asyncio.sleep(1)
    scheduler.add_job(looped_task, trigger='interval', args=tuple, id='NotifLoop', name='NotifLoop', seconds=3)
    scheduler.start()


# ---------------------------------------------------------------
# ---------------------------------------------------------------
# Task runs all the time, important to keep the asyncio.sleep at the end to avoid
# Function checks response from get_streams() and sends a message to joined discord channels accordingly.
async def looped_task(client):
    # await client.wait_until_ready()
    global api
    global first_startup
    global counter
    global users_url
    global token
    global users_response
    global local

    c_id = TWITCH_CLIENT_ID  # Client ID from Twitch Developers App
    c_secret = TWITCH_SECRET_ID  # Client Secret from Twitch Developers App

    # Loads json file containing information on channels and their subscribed streams as well as the last recorded
    # status of the streams

    # Check response from fecth() and messages discord channels
    if first_startup or unresolved_ids:
        users_url = await make_users_url()
        await asyncio.sleep(2)

        # Fill in missing stream IDs from api to local JSON
        token = await make_token(c_id, c_secret)  # Token to get twitch ID from all the added twitch usernames
        async with aiohttp.ClientSession() as session:
            users_response = await get_users(token, session, users_url, 'json')
        await fill_ids(users_response)
        # print(users_response)

        await asyncio.sleep(2)  # Wait enough for login to print to console
        first_startup = 0
        scheduler.reschedule_job('NotifLoop', trigger='interval', seconds=3)

    else:
        try:
            counter = counter + 1
        except:
            counter = 1
        live_counter = 0
        live_streams = []
        async with aiohttp.ClientSession() as session:
            users_response = await get_users(token, session, users_url, 'json')
        await asyncio.sleep(2)
        print("\n------\nCheck #{0}\nTime: {1}".format(counter, datetime.now()))

        with open('multimedia/local.json', 'r') as fp:
            local = json.load(fp)

        streams_url = await make_streams_url()
        async with aiohttp.ClientSession() as session:
            api = await get_streams(c_id, session, streams_url, 'json')

        # Check for streams in local['streams'] that are not in any of the channels' subscriptions and remove those
        all_subscriptions = []
        for channel_index in local['channels']:
            for subscribed in channel_index['subscribed']:
                if subscribed not in all_subscriptions:
                    all_subscriptions.append(subscribed)

        for i, stream in enumerate(local['streams']):
            if stream['login'] not in all_subscriptions:
                # print('\nTime: ' + str(datetime.now()) + '\nAucun channel souscrit pour diffuser:\nSUPPRESSION: ' +
                #       stream['login'] + ' de local["streams"]\n')
                stream_list = local['streams']
                stream_list.pop(i)

                await dump_json()

        # Check for streams in channel subscriptions that are not in the user_response
        for channel in local['channels']:
            channel_id = channel['id']
            for subscription in channel['subscribed']:
                exists = 0
                for user in users_response['data']:
                    if subscription == user['login']:
                        exists = 1

                if exists == 0:
                    sub_list = channel['subscribed']
                    sub_list.remove(subscription)

                    print('\nTime: ' + str(datetime.now()))
                    print("Le flux Twitch n'existe pas: ")
                    print('SUPPRESSION STREAM: ' + subscription + '\nCHANNEL ID: ' + str(channel_id))
                    msg = subscription + " n'existe pas, suppression du channel de la liste de notification."

                    channel_to_send = client.get_channel(channel_id)
                    await channel_to_send.send(msg)

                    await dump_json()

        # Loop through api response and set offline stream's 'sent' key value to false
        # If stream is offline, set 'sent' key value to false, then save and reload the local JSON file
        for index in local['streams']:

            # print('\nSTREAM NAME: ' + index['login'])
            # print('STREAM ID: ' + index['id'])

            found_match = 0
            for api_index in api['data']:
                if api_index['user_id'] == index['id']:
                    # print("ID CORRESPONDANT DE L'API: " + api_index['user_id'])
                    found_match = 1
                    live_counter += 1
                    live_streams.append(index['login'])

            if found_match == 0:
                # print('ID CORRESPONDANT NON TROUVÉ')
                index['sent'] = 'false'
                index['status'] = 'offline'
                await dump_json()

            else:
                index['status'] = 'live'
                await dump_json()

            # print('')

        streams_sent = []

        # Loop through channels and send out messages
        for channel in local['channels']:
            channel_id = channel['id']
            for subscribed_stream in channel['subscribed']:

                # Get correct id from local JSON
                for stream_index in local['streams']:
                    local_id = ''
                    if stream_index['login'] == subscribed_stream:
                        local_id = stream_index['id']

                    for api_index in api['data']:
                        if api_index['user_id'] == local_id:

                            status = api_index['type']

                            # If live, checks whether stream is live or vodcast, sets msg accordingly
                            # Sends message to channel, then saves sent status to json
                            if status == 'live' and (stream_index['sent'] == 'false' or stream_index['game'] != api_index['game_id']):
                                for user in users_response['data']:
                                    if user['display_name'] == api_index['user_name']:
                                        user_data = user

                                # NewStreams_url = "https://api.twitch.tv/helix/streams?user_login=" + stream_index['login']
                                # async with aiohttp.ClientSession() as session:
                                #     NewAPI = await notif.get_streams(c_id, session, NewStreams_url, 'json')
                                # for NewAPI_index in NewAPI['data']:
                                #     NewIndex = NewAPI_index

                                game_url = "https://api.twitch.tv/helix/games?id={0}".format(api_index['game_id'])
                                async with aiohttp.ClientSession() as session:
                                    game_response = await get_game(c_id, session, game_url, 'json')
                                for temp in game_response['data']:
                                    game = temp['name']
                                    box_art_url = temp['box_art_url'].replace("{width}", "138").replace("{height}", "190")

                                msg = "======= LIVE =======\n:regional_indicator_s: :regional_indicator_t: :regional_indicator_r: :regional_indicator_e: :regional_indicator_a: :regional_indicator_m:"

                                e = discord.Embed(title = api_index['title'], color= 6824352, description = "", url="https://www.twitch.tv/{0}".format(api_index['user_name']))
                                e.set_author(name=api_index['user_name'], icon_url=user_data['profile_image_url'])
                                e.set_thumbnail(url=box_art_url)
                                # e.set_image(url=NewIndex['thumbnail_url'].replace("{width}", "320").replace("{height}", "180"))
                                e.add_field(name="Game", value=game, inline=True)
                                e.add_field(name="Viewers", value=api_index['viewer_count'], inline=True)

                                channel_to_send = client.get_channel(channel_id)
                                try:
                                    await channel_to_send.send(msg)
                                    await channel_to_send.send(embed = e)
                                except:
                                    pass

                            elif status == 'vodcast' and stream_index['sent'] == 'false':
                                msg = stream_index['login'] + ' VODCAST est en LIVE!\nhttps://www.twitch.tv/' + stream_index['login']
                                try:
                                    await client.send_message(client.get_channel(channel_id), msg)
                                except:
                                    pass

                            # Loop through streams_sent[], if stream is not there, then add it
                            add_sent = 1
                            for stream in streams_sent:
                                if stream[0] == stream_index['login']:
                                    add_sent = 0
                            if add_sent:
                                streams_sent.append([stream_index['login'], api_index['game_id']])
                            elif stream_index['game'] == api_index['game_id']:
                                streams_temp = streams_sent
                                for stream in streams_temp:
                                    if stream[0] == stream_index['login']:
                                        streams_sent.append([stream_index['login'], api_index['game_id']])
                                    else:
                                        streams_sent.append(stream)

        for login in local['streams']:
            for stream in streams_sent:
                if login['login'] == stream[0]:
                    login['sent'] = 'true'
                    login['status'] = 'live'
                    login['game'] = stream[1]

        await dump_json()

        print('Live Channels: ' + str(live_counter))
        for stream in live_streams:
            print(stream)

        scheduler.reschedule_job('NotifLoop', trigger='interval', seconds=30)
# ---------------------------------------------------------------
# ---------------------------------------------------------------


async def dump_json():
    global local
    with open('multimedia/local.json' , 'w') as fp:
        json.dump(local, fp, indent=2)
    with open('multimedia/local.json', 'r') as fp:
        local = json.load(fp)


# Retourne la réponse de twitch api
async def get_streams(c_id, session, url, response_type):
    # Param qui contient l'ID client
    headers = {
        'Client-ID': '{}'.format(c_id)
    }

    # Obtient et retourne la réponse de twitch api, en utilisant l'en-tête défini ci-dessus.
    async with session.get(url, headers=headers, timeout=10) as response:
        if response_type == 'text':
            return await response.text()
        elif response_type == 'json':
            return await response.json()


async def get_game(c_id, session, url, response_type):
    # Param qui contient l'ID client
    headers = {
        'Client-ID': '{}'.format(c_id)
    }

    # Obtient et retourne la réponse de twitch api, en utilisant l'en-tête défini ci-dessus.
    async with session.get(url, headers=headers, timeout=10) as response:
        if response_type == 'text':
            return await response.text()
        elif response_type == 'json':
            return await response.json()


# Retourne la réponse de twitch api
async def get_users(token, session, url, response_type):

    # Param qui contient l'ID client
    headers = {
        'Authorization': 'Bearer {}'.format(token)
    }

    # Obtient et retourne la réponse de twitch api, en utilisant l'en-tête défini ci-dessus.
    async with session.get(url, headers=headers, timeout=10) as response:
        if response_type == 'text':
            return await response.text()
        elif response_type == 'json':
            return await response.json()


async def make_token(client_id, client_secret):
    print('\nObtention du token TWITCH...')
    token_url = 'https://id.twitch.tv/oauth2/token?client_id={}&client_secret={}&grant_type=client_credentials'.format(
        client_id, client_secret)
    async with aiohttp.ClientSession() as session:
        async with session.post(token_url) as response:
            response = await response.json()
            token = response['access_token']
            print('Token: ' + token + '\n------')
            return token


# Créer et renvoyer l'URL de l'API des flux Twitch avec les user_logins dans local.json
async def make_streams_url():
    streams = local['streams']

    url = 'https://api.twitch.tv/helix/streams?user_login='

    for index, login in enumerate(streams):
        if index == 0:
            url = url + login['login']
        else:
            url = url + '&user_login=' + login['login']

    return url


# Créer et renvoyer l'URL de l'API des flux Twitch avec les user_logins dans local.json
async def make_users_url():
    stream = local['streams']

    url = 'https://api.twitch.tv/helix/users?login='

    for index, login in enumerate(stream):
        if index == 0:
            url = url + login['login']
        else:
            url = url + '&login=' + login['login']

    return url


async def fill_ids(users_response):
    global unresolved_ids
    global local
    counter = 0

    print('\nRemplir les identifiants manquants ...')
    for local_user in local['streams']:
        if local_user['id'] == "":
            for user in users_response['data']:
                if local_user['login'] == user['login']:
                    counter += 1
                    print("ID manquant rempli pour l'utilisateur: " + local_user['login'] + " : " + user['id'])
                    local_user['id'] = user['id']

    if counter == 0:
        print('Aucun identifiant manquant.')
    else:
        print('\n' + str(counter) + ' ID remplis.')

    unresolved_ids = 0
    await dump_json()


class Notification(commands.Cog):

    def __init__(self, ctx):
        return(None)

    @commands.command(pass_context=True)
    async def notif_list(self, ctx):
        """0"""
        langue = sql.valueAtNumber(ctx.guild.id, "Lang", "Guild")
        channel_id = ctx.message.channel.id
        channel_exists = 0
        has_subscriptions = 0

        msg = lang.forge_msg(langue, "Notification", None, False, 0)
        for channel in local['channels']:

            # Vérifiez si le channel a été ajouté à local.json
            if channel['id'] == channel_id:
                channel_exists = 1
                for stream in channel['subscribed']:
                    has_subscriptions = 1
                    msg = msg + '\n' + stream

        # Si le channel n'existe pas, envoyez un message à ctx et retournez
        if channel_exists == 0:
            msg = lang.forge_msg(langue, "Notification", None, False, 1)
            await ctx.channel.send(msg)
            return

        elif not has_subscriptions:
            msg = lang.forge_msg(langue, "Notification", None, False, 2)
            await ctx.channel.send(msg)
            return

        else:
            await ctx.channel.send(msg)

    @commands.command(pass_context=True)
    async def checklive(self, ctx):
        """1"""
        langue = sql.valueAtNumber(ctx.guild.id, "Lang", "Guild")
        c_id = ctx.message.channel.id
        streams_live = []

        for channel in local['channels']:
            if c_id == channel['id']:
                if len(channel['subscribed']) == 0:
                    msg = lang.forge_msg(langue, "Notification", None, False, 2)
                    await ctx.channel.send(msg)
                    return

        for stream in local['streams']:
            if stream['status'] == 'live':
                streams_live.append(stream['login'])

        if len(streams_live) == 1:
            msg = lang.forge_msg(langue, "Notification", None, False, 3)
            for login in streams_live:
                msg = msg + '{}\n'.format(login)

        elif len(streams_live) > 0:
            msg = lang.forge_msg(langue, "Notification", [len(streams_live)], False, 4)
            for login in streams_live:
                msg = msg + '{}\n'.format(login)

        else:
            msg = lang.forge_msg(langue, "Notification", None, False, 5)

        await ctx.channel.send(msg)

    @commands.command(pass_context=True)
    async def removestream(self, ctx, arg):
        """2"""
        langue = sql.valueAtNumber(ctx.guild.id, "Lang", "Guild")
        channel_id = ctx.message.channel.id
        channel_exists = 0
        arg = str(arg.lower())
        global local

        with open('multimedia/local.json', 'r') as fp:
            local = json.load(fp)
        # Vérifiez si le channel a été ajouté à local.json
        for channel in local['channels']:
            if channel['id'] == channel_id:
                channel_exists = 1

        # Si le channel n'existe pas, envoyez un message à ctx et retournez
        if channel_exists == 0:
            msg = lang.forge_msg(langue, "Notification", None, False, 1)
            await ctx.channel.send(msg)
            return

        if not re.match('^[a-zA-Z0-9_]+$', arg):
            msg = lang.forge_msg(langue, "Notification", None, False, 6)
            await ctx.channel.send(msg)
            return

        # Vérifiez la liste des chaînes dans local.json pour éviter les doublons.
        for i, channel in enumerate(local['channels']):
            subscription_exists = 0

            if channel['id'] == channel_id:
                for stream in channel['subscribed']:
                    if stream == arg:
                        subscription_exists = 1

                if subscription_exists:
                    subscriptions = channel['subscribed']
                    subscriptions.remove(arg)
                    await dump_json()

                    msg = lang.forge_msg(langue, "Notification", [arg], False, 14)
                    await ctx.channel.send(msg)

                else:
                    msg = lang.forge_msg(langue, "Notification", [arg], False, 7)
                    await ctx.channel.send(msg)

    @commands.command(pass_context=True)
    async def addstream(self, ctx, arg):
        """3"""
        langue = sql.valueAtNumber(ctx.guild.id, "Lang", "Guild")
        global unresolved_ids
        channel_id = ctx.message.channel.id
        stream_exists = 0
        channel_exists = 0
        subscription_exists = 0
        arg = str(arg.lower())
        global local
        new_stream = {
            "login": arg,
            "sent": "false",
            "id": "",
            "status": "",
            "game": ""
        }
        with open('multimedia/local.json', 'r') as fp:
            local = json.load(fp)

        print('\n------\n\nTime: ' + str(datetime.now()))
        print('Ajouter une demande du channel ' + str(channel_id) + ' pour le flux ' + arg)

        if not re.match('^[a-zA-Z0-9_]+$', arg):
            msg = lang.forge_msg(langue, "Notification", None, False, 6)
            await ctx.channel.send(msg)
            return

        # Vérifiez la liste des flux dans local.json pour éviter les doublons
        for index in local['streams']:
            if index['login'] == arg:
                stream_exists = 1

        # Vérifiez la liste des chaînes dans local.json pour éviter les doublons.
        for channel in local['channels']:

            # Vérifiez si le channel a été ajouté à local.json
            if channel['id'] == channel_id:
                channel_exists = 1

                for stream in channel['subscribed']:

                    # Vérifier si le flux est déjà dans les abonnements de la chaîne
                    if stream == arg:
                        subscription_exists = 1

        # Si le channel n'existe pas, envoyez un message à ctx et retournez
        if channel_exists == 0:
            msg = lang.forge_msg(langue, "Notification", None, False, 1)
            await ctx.channel.send(msg)
            return

        # Agit sur les contrôles ci-dessus
        if subscription_exists == 0 and stream_exists == 0:
            local.setdefault('streams', []).append(new_stream)
            unresolved_ids = 1

            for channel in local['channels']:
                if channel['id'] == channel_id:
                    change = channel['subscribed']
                    change.append(arg)

            await dump_json()

            msg = lang.forge_msg(langue, "Notification", [arg], False, 8)
            await ctx.channel.send(msg)

        elif subscription_exists == 1 and stream_exists == 0:
            local.setdefault('streams', []).append(new_stream)
            unresolved_ids = 1

            await dump_json()

            msg = lang.forge_msg(langue, "Notification", [arg], False, 9)
            await ctx.channel.send(msg)

        elif subscription_exists == 0 and stream_exists == 1:
            for channel in local['channels']:
                if channel['id'] == channel_id:
                    change = channel['subscribed']
                    change.append(arg)

            await dump_json()

            msg = lang.forge_msg(langue, "Notification", [arg], False, 8)
            await ctx.channel.send(msg)

        elif subscription_exists == 1 and stream_exists == 1:
            msg = lang.forge_msg(langue, "Notification", [arg], False, 9)
            await ctx.channel.send(msg)

        c_id = TWITCH_CLIENT_ID  # Client ID from Twitch Developers App
        c_secret = TWITCH_SECRET_ID  # Client Secret from Twitch Developers App

        users_url = await make_users_url()
        await asyncio.sleep(2)

        # Fill in missing stream IDs from api to local JSON
        token = await make_token(c_id, c_secret)  # Token to get twitch ID from all the added twitch usernames
        async with aiohttp.ClientSession() as session:
            users_response = await get_users(token, session, users_url, 'json')
        await fill_ids(users_response)

    @commands.command(pass_context=True)
    async def addchannel(self, ctx):
        """4"""
        langue = sql.valueAtNumber(ctx.guild.id, "Lang", "Guild")
        s_name = ctx.message.guild.name
        c_name = ctx.message.channel.name
        c_id = ctx.message.channel.id
        u_id = ctx.message.author.id
        u_name = ctx.message.author.name
        global local

        verified = 0
        duplicate = 0
        if ge.permission(ctx):
            verified = 1

        # Si l'utilisateur peut être vérifié, recherchez les doublons, puis ajoutez le channel
        if verified:
            with open('multimedia/local.json', 'r') as fp:
                local = json.load(fp)
            # Vérifier les ID de channel en double
            for channel in local['channels']:
                if channel['id'] == c_id:
                    duplicate = 1

            # Act on duplicate check
            if not duplicate:
                new_channel = {
                    "id": c_id,
                    "guild_name": s_name,
                    "channel_name": c_name,
                    "added_by_name": u_name,
                    "added_by_id": u_id,
                    "subscribed": []
                }

                local['channels'].append(new_channel)
                await dump_json()

                msg = lang.forge_msg(langue, "Notification", None, False, 10)
                await ctx.channel.send(msg)

            else:
                msg = lang.forge_msg(langue, "Notification", None, False, 11)
                await ctx.channel.send(msg)

        else:
            msg = lang.forge_msg(langue, "WarningMsg", None, False, 1)
            await ctx.channel.send(msg)

    @commands.command(pass_context=True)
    async def removechannel(self, ctx):
        """5"""
        langue = sql.valueAtNumber(ctx.guild.id, "Lang", "Guild")
        c_id = ctx.message.channel.id

        verified = 0
        channel_exists = 0
        global local
        if ge.permission(ctx):
            verified = 1

        # If user can be verified, try remove channel with correct id
        if verified:
            with open('multimedia/local.json', 'r') as fp:
                local = json.load(fp)
            channel_list = local['channels']
            for channel in channel_list:
                if channel['id'] == c_id:
                    channel_exists = 1
                    channel_list.remove(channel)
                    await dump_json()

            if channel_exists:
                msg = lang.forge_msg(langue, "Notification", None, False, 12)
                await ctx.channel.send(msg)

            else:
                msg = lang.forge_msg(langue, "Notification", None, False, 13)
                await ctx.channel.send(msg)

        else:
            msg = lang.forge_msg(langue, "WarningMsg", None, False, 1)
            await ctx.channel.send(msg)


def setup(bot):
    bot.add_cog(Notification(bot))
    open("help/cogs.txt", "a").write("Notification\n")
