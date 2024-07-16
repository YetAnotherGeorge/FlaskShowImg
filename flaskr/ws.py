import asyncio
import websockets
import time
import sqlite3
import base64
import json
import threading
from types import SimpleNamespace

from . import events
from . import consts

# WS SERVER
CONN_WS_CLIENTS = set()


async def handle_new_image_event(flask_appd):
   while True:
      print(f"NEW_IMG_EVENT: Waiting")
      events.NEW_IMG_EVENT.wait()
      print(f"NEW_IMG_EVENT: Triggered")
      
      for c in CONN_WS_CLIENTS.copy():
         print(f"WS BROADCAST: SEND EV SELECT_RESP")
         try:
            await c.send(json.dumps({"event": "UPDATE"}))
         except Exception as e:
            print(f"Error broadcasting to client: {e}; Removing")
            CONN_WS_CLIENTS.remove(c)
      
      events.NEW_IMG_EVENT.clear()
   
async def run_server(flask_appd):
   async def handler(websocket, path):
      print(f"Client connected: {websocket.remote_address} - {path}")
      CONN_WS_CLIENTS.add(websocket)
      try:
         async for message in websocket:
            try: 
               m = json.loads(message, object_hook=lambda d: SimpleNamespace(**d))
               print(f"WS: EV: {m.event}")
               
               if m.event == "SELECT":
                  # Request body: {
                  #    event: "SELECT",
                  #    data: { item: int } | null
                  # }
                  d = None
                  try:
                     d = m.data
                  except:
                     d = None
                     
                  (imgBase64, currentSelection) = flask_appd.serve_ws_select(d)
                  print(f"WS: SEND EV SELECT_RESP")
                  await websocket.send(json.dumps({
                     "event": "SELECT_RESP", 
                     "data": {
                        "imgBase64": imgBase64,
                        "currentSelection": currentSelection
                     }}))
                  
            except Exception as ex:
               print(f"WS: ERR: {ex}")
      except websockets.ConnectionClosed:
         print(f"Client disconnected: {websocket.remote_address}")
         CONN_WS_CLIENTS.remove(websocket)
              
   while True:
      try:
         async with websockets.serve(handler, "localhost", consts.WS_PORT):
            print(f"WebSocket server started on ws://localhost:{consts.WS_PORT}")
            await asyncio.Future()  # Run forever
         return
      except Exception as ex:
         print(f"Error running ws server: {ex}")
         time.sleep(4)
