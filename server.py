from time import time, sleep
from threading import Timer
import copy

from match import MatchInfo

class Server:
    def __init__(self):
        self.matches: dict[str, MatchInfo] = {}
        self._stopped = False
        self.updatetimers = dict[str, Timer]()

    def matchesByPlayer(self, playerid: str) -> filter:
        return filter(lambda x: x.firstid == playerid or x.secondid == playerid,
                      [self.matches[x] for x in self.matches])

    def matchById(self, matchid: str) -> MatchInfo | None:
        if not matchid in self.matches:
            return None
        return self.matches[matchid]
    
    def addMatch(self, matchid: str, firstid: str, secondid: str, fieldfile: str, starttime: float = 9e100):
        if matchid in self.matches:
            raise ValueError("match id duplicated")

        self.matches[matchid] = MatchInfo(matchid, firstid, secondid, fieldfile, starttime)

    def update(self, match_id):
        match = self.matches[match_id]
        if not match.started:
            match.start()
        else:
            match.update()

        self.updatetimers[match_id] = Timer(match.nextupdatetime - time(), self.update, [match_id])
        self.updatetimers[match_id].start()

    def loopForever(self):
        for match_id, match in self.matches.items():
            self.updatetimers[match_id] = Timer(match.starttime - time(), self.update, [match_id])
            self.updatetimers[match_id].start()

        try:
            while not self._stopped:
                sleep(0.5)
        finally:
            for t in self.updatetimers:
                t.cancel()
    
    def shutdown(self):
        self._stopped = True

mainServer = Server()