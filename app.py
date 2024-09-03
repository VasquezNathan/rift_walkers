import os
import requests
from urllib.parse import quote_plus
from concurrent import futures
from datetime import datetime, timedelta

from flask import Flask, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

from service import conf
from service.summoner import Summoner, SummonerCache, RANKS, TIERS

load_dotenv()
API_KEY = os.getenv('RIOT_API_KEY')
summoner_cache  = SummonerCache()

app = Flask(__name__)
origins = [
    'http://localhost:5000',
    'http://localhost:5173',
    'http://localhost:5174',
    'https://natevasquez.com'
]
CORS(app, origins=origins)

@app.route('/ranks/<rank>')
def rank(rank):
    try:
        return send_from_directory('ranks', f'{rank}')
    except:
        return 404

@app.route('/profileicons/<id>')
def profile_icon(id):
    try:
        return send_from_directory('profileicons', f'{id}')
    except:
        return 404


@app.route('/')
def home():
    ret = []

    summoners: list[Summoner] = []

    with futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_summoners: list[futures.Future] = []

        for username, tag in conf.FRIEND_LIST.items():
            future_summoners.append(executor.submit(query_summoner_info, username, tag))
        
        
        for fut in future_summoners:
            summoners.append(fut.result())
        
    summoners.sort(key=lambda x: x.total_lp, reverse=True)

    for s in summoners:
        ret.append({'name': s.name,
                    'rank': s.rank,
                    'tier': s.tier,
                    'leaguePoints': s.league_points,
                    'iconId': s.icon_id,
                    'wins': s.wins,
                    'losses': s.losses})
    
    summoner_cache.set_expires(datetime.now() + timedelta(seconds=30))

    return ret

def query_summoner_info(username: str, tag: str) -> Summoner:
    ''''''
    summoner_name_tag = f'{username}#{tag}'
    if summoner_name_tag  in summoner_cache.summoners and not summoner_cache.expired:
        return summoner_cache.summoners[summoner_name_tag]

    summoner = Summoner()

    # Get information from username + tag.
    url = f'{conf.PUUID_BY_RIOT_ID}/{quote_plus(username)}/{quote_plus(tag)}'
    headers={
        'X-Riot-Token': API_KEY
    }
    r = requests.get(url=url, headers=headers)
    # print(r.json())
    print(r.status_code)
    summoner.name = r.json()['gameName']
    
    # Get summoner ID from PUUID
    puuid = r.json()['puuid']
    url = f'{conf.SUMMONER_BY_PUUID}/{puuid}'
    r = requests.get(url=url, headers=headers)
    print(r.status_code)
    summoner_id = r.json()['id']
    summoner.icon_id = r.json()['profileIconId']

    # Get League information by summoner ID
    url = f'{conf.ENTRIES_BY_SUMMONER_ID}/{summoner_id}'
    r = requests.get(url=url, headers=headers)
    print(r.status_code)

    for league in r.json():
        if league['queueType'] == 'RANKED_SOLO_5x5':
            summoner.rank = league['rank']
            summoner.tier = league['tier']
            summoner.league_points = league['leaguePoints']
            summoner.wins = league['wins']
            summoner.losses = league['losses']
     
    summoner.total_lp = (TIERS[summoner.tier] * 400) + (RANKS[summoner.rank] * 100) + int(summoner.league_points)

    summoner_cache.summoners[summoner_name_tag] = summoner
    return summoner
