import fcntl
import time
import os
import json
from urllib.parse import quote_plus
from concurrent import futures
from datetime import date

import requests
from dotenv import load_dotenv

from service import conf
from service.summoner import Summoner, RANKS, TIERS

load_dotenv()
API_KEY = os.getenv('RIOT_API_KEY')
NEW_DAY = False
with open('/home/natebuntu/workspace/rift_walkers/day.dat', 'r') as f:
    day = int(f.read())
    NEW_DAY = day != date.today().day

def query_summoner_info(username: str, tag: str) -> Summoner:
    ''''''

    summoner = Summoner()

    # Get information from username + tag.
    url = f'{conf.PUUID_BY_RIOT_ID}/{quote_plus(username)}/{quote_plus(tag)}'
    headers={
        'X-Riot-Token': API_KEY
    }
    r = requests.get(url=url, headers=headers)
    # print(r.json())
    print(r.status_code)
    print(r.json())
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


    if NEW_DAY:
        summoner.previous_day_losses = summoner.losses
        summoner.previous_day_wins =  summoner.wins

    summoner.total_lp = (TIERS[summoner.tier] * 400) + (RANKS[summoner.rank] * 100) + int(summoner.league_points)
    

    return summoner


if __name__ == '__main__':
    
    summoners: list[Summoner] = []

    with futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_summoners: list[futures.Future] = []

        for username, tag in conf.FRIEND_LIST.items():
            try:
                future_summoners.append(executor.submit(query_summoner_info, username, tag))
            except Exception as e:
                pass
        
        for fut in future_summoners:
            try:
                summoners.append(fut.result())
            except Exception as e:
                pass
    
    summoners.sort(key=lambda x: x.total_lp, reverse=True)
    
    ret = []
    for s in summoners:
        ret.append({'name': s.name,
                    'rank': s.rank,
                    'tier': s.tier,
                    'leaguePoints': s.league_points,
                    'iconId': s.icon_id,
                    'wins': s.wins,
                    'losses': s.losses,
                    'pDayWins': s.previous_day_wins,
                    'pDayLosses': s.previous_day_losses})
        
    with open('/home/natebuntu/workspace/rift_walkers/summoners.json', 'w') as f:
        retries, max_retries = 0, 3
        
        while retries < max_retries:
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                f.write(json.dumps(ret))
                retries = max_retries
            except IOError:
                retries += 1
                time.sleep(0.5)
    if NEW_DAY:           
        with open('/home/natebuntu/workspace/rift_walkers/day.dat', 'w') as f:
            f.write(f'{date.today().day}')
