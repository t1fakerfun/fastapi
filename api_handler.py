from http.server import BaseHTTPRequestHandler

import regex
import json
import pickle
import time

from server import mainServer
from field import BuilderAction

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        location, params = self.parseLocationAndParams()

        if location == '/match':
            self.handleMatch(params)
        else:
            self.handleUnknown(params)

    def do_POST(self):
        data = self.parseContentJson()
        location, params = self.parseLocationAndParams()

        if location == "/builder":
            self.handleBuilder(data, params)
        else:
            self.handleUnknown(params)

    def parseContentJson(self):
        data = json.loads(self.rfile.read(int(self.headers['content-length'])).decode('utf-8'))
        return data


    def parseLocationAndParams(self) -> tuple[str, dict[str, str]]:
        params = {}
        m = regex.match(r"(?P<location>/[\w.]*)(\?((?P<param>[\w]+=[^\?&]*)&?)*)?", self.path)

        if m == None:
            return ("/", {})

        location = m.group('location')
        for name, value in [x.split('=') for x in m.captures('param')]:
            params[name] = value

        return location, params

    def handleMatch(self, params):
        if not "token" in params:
            self.handleError("TokenError")
            return
        
        token = params['token']
        responseJson = {}
        fields = {}
        responseJson["fields"] = fields
        for match in mainServer.matchesByPlayer(token):
            fields[match.id] = pickle.dumps(match).hex()

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(bytes(json.dumps(responseJson) + "\r\n", encoding='utf-8'))

    def handleUnknown(self, params):
        self.send_response(404)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"NotFoundError\r\n")

    def handleBuilder(self, contentJson, params):
        if not "token" in params:
            self.handleError("TokenError")
            return
        
        if (not "match_id" in contentJson or
        not "turn_index" in contentJson or
        not "movements" in contentJson):
            self.handleError("ArgumentNotEnoughError")
            return
        
        try:
            token = params["token"]
            matchid = contentJson["match_id"]
            turnidx = int(contentJson["turn_index"])
            moves = contentJson["movements"]
        except:
            self.handleError("ArgumentInvalidError")
            return
        
        matchinfo = mainServer.matchById(matchid)
        resJson = {}
        resMoves = {}
        resJson["movements"] = resMoves

        if matchinfo == None:
            self.handleError("MatchIdError")
            return
        
        if matchinfo.firstid != token and matchinfo.secondid != token:
            self.handleError("TokenError")
        
        if matchinfo.firstid == token:
            update_turn = matchinfo.field.turn_now // 2 * 2 + 1
        else:
            update_turn = (matchinfo.field.turn_now - 1) // 2 * 2 + 2

        if turnidx != update_turn:
            self.handleError("TurnError")
            return

        for builderid, actionid in moves.items():
            if matchinfo.firstid == token and builderid not in matchinfo.firstbuilders:
                self.handleError("BuilderIdError")
                return
            if matchinfo.secondid == token and builderid not in matchinfo.secondbuilders:
                self.handleError("BuilderIdError")
                return
            if BuilderAction.parse(actionid) == None:
                self.handleError("BuilderActionError")
                return
        
        for builderid, actionid in moves.items():
            if token == matchinfo.firstid:
                matchinfo.firstbuilders[builderid].nextaction = BuilderAction(actionid)
            elif token == matchinfo.secondid:
                matchinfo.secondbuilders[builderid].nextaction = BuilderAction(actionid)
            resMoves[builderid] = actionid

        resJson["turn_index"] = turnidx + 1
        resJson["match_id"] = matchid
        resJson["accepted_at"] = int(time.time())

        self.send_response(200)
        self.send_header("content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(bytes(json.dumps(resJson) + "\r\n", encoding='utf-8'))
                               
    def handleError(self, error: str):
        self.send_response(400)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(bytes(error + "\r\n", encoding="utf-8"))
        
