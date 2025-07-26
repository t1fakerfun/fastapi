import requests
import pickle

from match import MatchInfo
from field import BuilderAction

SERVER_PORT = "9001"
SERVER_ADDRESS = "127.0.0.1"

SERVER_SCHEME = "http://" + SERVER_ADDRESS + ":" + SERVER_PORT
ENDPOINT_MATCH = SERVER_SCHEME + "/match"
ENDPOINT_BUILDER = SERVER_SCHEME + "/builder"

def getMatches(token: str):
    """
    競技サーバから指定したプレイヤーの試合情報を取得します
    """
    res = requests.get(ENDPOINT_MATCH, params={
        "token": token
    })
    if res.status_code != 200:
        raise RuntimeError("server returned error code.")
    
    matches: dict[str, MatchInfo] = {}
    fieldpickles = res.json()["fields"]
    for pid in fieldpickles:
        picklebytes = bytes.fromhex(fieldpickles[pid])
        matches[pid] = pickle.loads(picklebytes)
    
    return matches

def setAction(token: str, match_id: str, turn_now: int, builder_id: str, builder_act: BuilderAction) -> BuilderAction | str:
    """
    指定したターンの職人の行動を決定する
    戻り値は、受理されたなら受理された職人の行動、そうでないならエラーの原因を表す文字列です
    """
    res = requests.post(ENDPOINT_BUILDER, params={
        "token": token
    }, json={
        "match_id": match_id,
        "turn_index": turn_now,
        "movements": {
            builder_id: int(builder_act)
        }
    })

    if res.status_code != 200:
        return str(res.content, encoding='utf-8')

    data = res.json()
    return data["movements"][builder_id]