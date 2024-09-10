from datetime import datetime, date

TIERS = {'IRON': 0,
         'BRONZE': 1,
         'SILVER': 2,
         'GOLD': 3,
         'PLATINUM': 4,
         'EMERALD': 5,
         'DIAMOND': 6,
         'MASTER': 7,
         'GRANDMASTER': 8,
         'CHALLENGER': 9}

RANKS = {
    'IV': 0,
    'III': 1,
    'II': 2,
    'I': 3
}

class Summoner:
    def __init__(self, **kwargs):
        self.rank: str = kwargs.get('rank', '')
        self.tier: str = kwargs.get('tier', '')
        self.league_points: str = kwargs.get('leaguePoints', '')
        self.icon_id: str = kwargs.get('iconId', '')
        self.name: str = kwargs.get('name', '')
        self.total_lp: int = kwargs.get('leaguePoints', 0)
        self.wins: int = kwargs.get('wins', 0)
        self.losses: int = kwargs.get('losses', 0)
        self.previous_day_wins: int = kwargs.get('pDayWins', 0)
        self.previous_day_losses: int = kwargs.get('pDayLosses', 0)
    

class SummonerCache:
    def __init__(self):
        self._expires: datetime | None = None
        self.summoners: dict[str, Summoner] = {}
        self._day: int | None = None

    @property
    def expired(self) -> bool:
        if self._expires is None:
            return True
        
        return self._expires <= datetime.now()
    
    def set_expires(self, new_expires: datetime):
        self._expires = new_expires

    @property
    def new_day(self) -> bool:
        if self._day is None:
            return True
        
        return self._day != date.today().day
    
    def set_day(self, new_day: int):
        self._day = new_day