from json import dumps
from typing import Optional
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import Response
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
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/graph",{"amount"})
async def read_item(skip: int = 0, limit:int= ["amount"]):
    graphmax = request.json["graphMax"]
    record= MongoDsn.db.parameters.find({"temps":graphmax})
    return dumps(list(record))

@app.get("/api/states") #gets states of both the temp and sunset
async def get_states():

    

    temperature = await db["temps"].find().sort("date",-1).to_list(1)
    time = await db["time"].find().sort("date").to_list(1)
    pressence = await db["detected"].find().sort("date",-1).to_list(1)
    lamp=False
    fan = False

    res =  request.get("https://api.sunrise-sunset.org/json")
    resJson = res.json()
    sunSet_Time = resJson["sunset"]
    sunRise_Time = resJson["sunrise"]
    sunSetTime = datetime.datetime.strptisme(sunSet_Time["sunset"].split("T")[1],"%H:%M:%S.%f")
    sunRiseTime = datetime.datetime.strptime(sunRise_Time["sunrise"].split("T")[1],"%H:%M:%S.%f")
    currentTime= datetime.datetime.now().strftime("%H:%M:%S.%f")
    current_time = datetime.datetime.strptime(currentTime,"%H:%M:%S.%f")
    
    
    
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
        settemp=request.json["temps"]
        if temperature[0]["temps"] >= settemp:
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


@app.put("/api/temperature",status_code=204)
async def set_temp(request:Request):
    try:
        temp_obj = await request.json()
        temp_obj["date"]=datetime.datetime.now()
        new_temp=await db["temps"].insert_one(temp_obj)
        created_temp = await db["temps"].find_one({"_id": new_temp.inserted_id})

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