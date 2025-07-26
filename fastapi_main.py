import api
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import time
import asyncio
import requests
from fastapi.responses import PlainTextResponse
from field import BuilderAction
from field import Board
from match import MatchInfo


app = FastAPI()


def accesstime_permit(token: str):
    matches_api = api.getMatches(token)
    now_time = time.time()
    for access in matches_api.values():
        if access.starttime <= now_time:
            return True
    return False


class Item(BaseModel):
    name: str
    price: float
    is_offer: bool = None


mydict = {}


@app.get("/")
def read_root():
    return {"Hello": "World"}


class match_model(BaseModel):
    match_id: str
    field_id: str
    is_first: bool
    turn_interval: int
    joheki: int
    jinchi: int
    shiro: int


@app.get("/match")
async def read_match(token: str):
    if not accesstime_permit(token):
        return PlainTextResponse("AccessTimeError")
    # Information for "token" player
    matches_api = api.getMatches(token)
    matches = []
    for match_info in matches_api.values():
        each_match = {
            "match_id": match_info.id,
            "field_id": match_info.fieldfile,
            "is_first": match_info.firstid == token,
            "turn_interval": match_info.field.turninterval,
            "joheki": match_info.field.johekifactor,
            "jinchi": match_info.field.jinchifactor,
            "shiro": match_info.field.shirofactor
        }
        matches.append(each_match)
    return {"matches": matches}


class field_model(BaseModel):
    turn_index: int
    movements: list[str]


@app.get("/field")
async def read_field(token: str, match: str):
    if not accesstime_permit(token):
        return PlainTextResponse("AccessTimeError")
    matches_api = api.getMatches(token)
    map_lst = [siaisu.id for siaisu in matches_api.values()]

    if match not in map_lst:
        return PlainTextResponse("MatchIdError", 200)
    
    matchInfo = matches_api[match]
    
    return {
        "turn_index": matchInfo.field.turn_now,
        "movements": matchInfo.field.log
    }


class Movement(BaseModel):
    match_id: str
    turn_index: int
    movements: dict[str, int]

@app.post("/answer")
async def answer(token: str, data: Movement):
    match_id = data.match_id
    turn_target = data.turn_index
    movements = data.movements

    matches = api.getMatches(token)
    if not match_id in matches:
        return PlainTextResponse("MatchIdError", 400)
    
    match = matches[match_id]
    if match.starttime > time.time():
        return PlainTextResponse("AccessTimeError", 400)
    
    if match.firstid != token and match.secondid != token:
        return PlainTextResponse("TokenError", 400)

    if match.firstid == token:
        turn_next_update = match.field.turn_now // 2 * 2 + 1
    else:
        turn_next_update = (match.field.turn_now - 1) // 2 * 2 + 2

    if turn_target != turn_next_update:
        return PlainTextResponse("TurnError", 400)
    
    moves_result = {}

    data_res = {}
    data_res["match_id"] = match_id
    data_res["turn_index"] = turn_target
    data_res["movements"] = moves_result

    for builder, action in movements.items():
        action_result = api.setAction(token, match_id, turn_target, builder, BuilderAction(action))
        if isinstance(action_result, str):
            return PlainTextResponse(action_result, 400)
        moves_result[builder] = action_result

    return data_res

@app.on_event("startup")
async def startup_event():
    pass
