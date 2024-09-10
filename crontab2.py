import os
import json
from urllib.parse import quote_plus
from datetime import date
import fcntl
import time

import requests
from dotenv import load_dotenv

from service import conf
from service.summoner import Summoner, TIERS, RANKS
# import sqlite3

load_dotenv()
API_KEY = os.getenv('RIOT_API_KEY')

class RiftWalkers:
    def __init__(self):
        self.summoners: dict[str, Summoner] = {} # gamename#tag : Summoner
        self.last_day = None
        try:
            with open(f'{os.path.dirname(os.path.abspath(__file__))}/day.dat', 'r') as file:
                self.last_day = int(file.read())
        except Exception as e:
            print(e)

        self.today = date.today().day

    def build_existing_summoners(self):
        with open(f'{os.path.dirname(os.path.abspath(__file__))}/summoners.json', 'r') as file:
            raw_summoners = json.loads(file.read())

            for summoner in raw_summoners:
                self.summoners[summoner['name']] = Summoner(**summoner)

    def query_summoner_info(self, username: str, tag: str) -> Summoner:
        summoner = self.summoners.get(username, Summoner())

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

        summoner.total_lp = (TIERS[summoner.tier] * 400) + (RANKS[summoner.rank] * 100) + int(summoner.league_points)

        self.summoners[summoner.name] = summoner


if __name__ == '__main__':
    # Get summoners
    rift_walkers = RiftWalkers()
    rift_walkers.build_existing_summoners()
    
    # Update Summoners
    for username, tag in conf.FRIEND_LIST.items():
        try:
            rift_walkers.query_summoner_info(username, tag)
        except Exception:
            pass
    
    # New day logic.
    if rift_walkers.last_day != rift_walkers.today:
        for _, summoner in rift_walkers.summoners.items():
            summoner.previous_day_losses = summoner.losses
            summoner.previous_day_wins = summoner.wins
        with open(f'{os.path.dirname(os.path.abspath(__file__))}/day.dat', 'w') as file:
            file.write(f'{rift_walkers.today}')

    # write to disk
    temp_summs: list[Summoner] = [s for _, s in rift_walkers.summoners.items()]
    temp_summs.sort(key=lambda s: s.total_lp, reverse=True)
    ret: list[Summoner] = []
    for s in temp_summs:
        ret.append({'name': s.name,
                    'rank': s.rank,
                    'tier': s.tier,
                    'leaguePoints': s.league_points,
                    'iconId': s.icon_id,
                    'wins': s.wins,
                    'losses': s.losses,
                    'pDayWins': s.previous_day_wins,
                    'pDayLosses': s.previous_day_losses})
    with open(f'{os.path.dirname(os.path.abspath(__file__))}/summoners.json', 'w') as file:
        retries, max_retries = 0, 3
        
        while retries < max_retries:
            try:
                fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                file.write(json.dumps(ret))
                retries = max_retries
            except IOError:
                retries += 1
                time.sleep(0.5)
