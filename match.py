import time
from field import Board, BuilderAction
from threading import Timer

class BuilderInfo:
    def __init__(self, matchid, symbol, isfirstattacker):
        self.matchid = matchid
        self.symbol = symbol
        self.isfirstattacker = isfirstattacker
        self.nextaction = BuilderAction.Wait

class MatchInfo:
    def __init__(self, id, firstattackerid, secondattackerid, fieldfile, starttime):
        self.field = Board(fieldfile)
        self.id = id
        self.firstid = firstattackerid
        self.secondid = secondattackerid
        self.started = False
        self.nextupdatetime = starttime + self.field.turninterval
        self.fieldfile = fieldfile
        self.starttime = starttime

        self.firstbuilders: dict[str, BuilderInfo] = {}
        self.secondbuilders: dict[str, BuilderInfo] = {}
        for builderid in self.field.firstbuilders:
            self.firstbuilders[builderid] = BuilderInfo(self.id, builderid, True)
        for builderid in self.field.secondbuilders:
            self.secondbuilders[builderid] = BuilderInfo(self.id, builderid, False)


    def start(self):
        if self.started:
            return
        self.started = True

        print(self.id, "started")

    def update(self):
        if self.field.turn_now > self.field.turncount:
            return
        
        if not self.started:
            return
        
        isfirstattacker = self.field.turn_now % 2 == 0
        if isfirstattacker:
            actdict = {self.firstbuilders[x].symbol: self.firstbuilders[x].nextaction for x in self.firstbuilders}
            for builder in self.firstbuilders:
                self.firstbuilders[builder].nextaction = BuilderAction.Wait
        else:
            actdict = {self.secondbuilders[x].symbol: self.secondbuilders[x].nextaction for x in self.secondbuilders}
            for builder in self.secondbuilders:
                self.secondbuilders[builder].nextaction = BuilderAction.Wait

        self.field.game(actdict)
        print("%s is updated to %d" % (self.id, self.field.turn_now))

        if self.field.turn_now != self.field.turncount + 1:
            self.nextupdatetime = self.nextupdatetime + self.field.turninterval

    def getactionstr(actid):
        actions = {
            BuilderAction.Wait: "stay",
            BuilderAction.BuildUp: "wu",
            BuilderAction.BuildDown: "wd",
            BuilderAction.BuildLeft: "wl",
            BuilderAction.BuildRight: "wr",
            BuilderAction.BreakUp: "bu",
            BuilderAction.BreakDown: "bd",
            BuilderAction.BreakLeft: "bl",
            BuilderAction.BreakRight: "br",
            BuilderAction.MoveUp: "su",
            BuilderAction.MoveDown: "sd",
            BuilderAction.MoveLeft: "sl",
            BuilderAction.MoveRight: "sr",
            BuilderAction.MoveUpLeft: "sul",
            BuilderAction.MoveUpRight: "sur",
            BuilderAction.MoveDownLeft: "sdl",
            BuilderAction.MoveDownRight: "sdr"
        }

        return actions[actid]