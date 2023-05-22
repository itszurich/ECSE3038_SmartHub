import json 
from typing import Optional
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import Response, JSONResponse
from fastapi.encoders import jsonable_encoder
from bson import ObjectId
from httpx import request
import motor.motor_asyncio
import requests
import pydantic
import datetime
from dotenv import load_dotenv
from pydantic import BaseModel, MongoDsn
import os
import re
from datetime import timedelta
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("Mongo_DB"))
db = client.IOTProject

pydantic.json.ENCODERS_BY_TYPE[ObjectId]=str

origins=[
    "https://simple-smart-hub-client.netlify.app"
    "http://localhost:8000",
    "http://127.0.0.1:8000",
 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

res =  request.get("https://api.sunrise-sunset.org/json?lat=18.1096&lng=-77.2975&formatted=0")
resJson = res.json()
sunSet_Time = resJson["sunset"]
sunRise_Time = resJson["sunrise"]
sunSetTime = datetime.datetime.strptime(sunSet_Time["sunset"].split("T")[1],"%H:%M:%S.%f")
sunRiseTime = datetime.datetime.strptime(sunRise_Time["sunrise"].split("T")[1],"%H:%M:%S.%f")
currentTime= datetime.datetime.now().strftime("%H:%M:%S.%f")
current_time = datetime.datetime.strptime(currentTime,"%H:%M:%S.%f")


@app.get("/graph",status_code=200)
async def graph(request: Request, size: int):
    graph_obj = await db["Embedded"].find().sort('_id', -1).to_list(size)
    graphList = []

    for obj in graph_obj:
        temps = obj["temperature"]
        pres = obj["presence"]
        datetime = obj["created"]
        graphStuff = {"temperature": temps, "presence": pres, "datetime": datetime}
        await db["Graph"].insert_one(graphStuff)
        graphList.append(graphStuff)
    graphList = [{**data, "_id": str(data["_id"])} for data in graphList]
    return JSONResponse(content=graphList)

@app.get("/api/states",status_code=200) #gets states of both the temp and sunset
async def get_states():

    temperature = await db["temperature"].find().sort("date",-1).to_list(1)
    pressence = await db["presence"].find().sort("datetime",-1).to_list(1)
    lamp=False
    fan = False
    
    if len(temperature)==0:
        return{
            "fan":fan
        }
    
    if len(pressence)==0:
        return{
            "fan":fan,
            "lamp":lamp
        }

    if pressence == True:
        settemp=request.json["temperature"]
        if temperature[0]["temperature"] >= settemp:
            fan = True
        if (current_time >= sunSetTime) & (current_time<sunRiseTime):
            lamp = True
        elif (current_time < sunSetTime) & (current_time>sunRiseTime):
            lamp == False
    elif pressence == False:
        lamp=False
        fan = False
    return{
        "lamp": lamp,
        "fan":fan
    }


@app.put("/api/put",status_code=204)
async def set_temp_time(request:Request):
     info_obj = await request.json()
     if info_obj["user_light"] == "sunset" :
        info_obj["user_light"]= sunSetTime
        time_off= sunSetTime + parse_time(info_obj["light_duration"])
        info_obj["light_time_off"] = time_off.strftime("%H:%M:%S")
     else: 
        info_obj["user_light"]!="sunset"
        user_light = datetime.strptime(info_obj["user_light"], "%H:%M:%S").time()     #making TIME object from user_light parameter
        today = date.today()                                                                #fetching current date
        user_date_time = datetime.combine(today, user_light)                             #attaching current date to user light time
        time_off= user_date_time + parse_time(info_obj["light_duration"])
        info_obj["light_time_off"] = datetime.strftime(time_off_dto, "%H:%M:%S")
    try:
        temp_obj = await request.json()
        temp_obj["datetime"]=datetime.datetime.now()
        new_temp=await db["temperature"].insert_one(temp_obj)
        # created_temp = await db["temperature"].find_one({"_id": new_temp.inserted_id})
    except:
        raise HTTPException(status_code=400,detail="you goofed")
    
regex = re.compile(r'((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?')
def parse_time(time_str):
    parts = regex.match(time_str)
    if not parts:
        return
    parts = parts.groupdict()
    time_params = {}
    for name, param in parts.items():
        if param:
            time_params[name] = int(param)
    return timedelta(**time_params)