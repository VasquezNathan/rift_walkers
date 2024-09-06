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
    def __init__(self):
        self.rank: str = ''
        self.tier: str = ''
        self.league_points: str = ''
        self.icon_id: str = ''
        self.name: str = ''
        self.total_lp: int = 0
        self.wins: int = 0
        self.losses: int = 0
        self.previous_day_wins: int = 0
        self.previous_day_losses: int = 0

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