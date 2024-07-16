from flask import Flask, session, redirect, url_for, render_template, request
import typing
import sqlite3
import asyncio
import threading
import base64

from . import ws
from . import events
from . import consts


class FlaskApplication:
   flask_app: Flask
   db_connection: sqlite3.Connection
   available_image_count: int # 0 - newest, available_image_count - 1 oldest
   def __init__(self, db_schema_path: str, db_path: str):
      # DB
      self.db_connection = sqlite3.connect(db_path, check_same_thread=False)
      print(f"DB: Connected {db_path!r}")
      with open(db_schema_path, "r", encoding="utf-8") as f:
         self.db_connection.cursor().executescript(f.read())
      self.available_image_count = int(self.db_connection.cursor().execute("""SELECT count() FROM history""").fetchone()[0])
      self.db_connection.commit()
      print(f"DB: Initialized")
      
      # Flask
      self.flask_app = Flask(__name__)
      self.flask_app.config.from_mapping(
         SECRET_KEY="dev"
      )
      print(f"FLASK: App created")
      
   def serve_ws_select(self, request) -> typing.Tuple[str, int]: 
      """
      request: {item: int} | null
      """
      if request == None:
         print(f"REQ IMG: LATEST")
  
      rid = int(request.item if request != None else 0)
      print(f"REQ IMG: {rid}")
      
      if rid >= self.available_image_count:
         print(f"REQ: No images present")
         return ("", 0)
      
      # FETCH image number {request.item} from db
      cursor = self.db_connection.cursor()
      img_query = cursor.execute("""
                                 SELECT img FROM history
                                 ORDER BY id DESC
                                 LIMIT 1 OFFSET ?;
                                 """, (rid,) ).fetchone()[0]
      if type(img_query) != bytes:
         raise Exception(f"Invalid db response. Expected bytes but got {type(img_query)}")
      return (base64.b64encode(img_query).decode("ascii"), rid)
   
def create_app(test_config=None) -> Flask: 
   appd = FlaskApplication(db_schema_path="./historydb.schema.sql", db_path="./historydb.sqlite")
   
   threading.Thread(target=asyncio.run, args=(ws.run_server(appd),) ).start()
   threading.Thread(target=asyncio.run, args=(ws.handle_new_image_event(appd),) ).start()
   # asyncio.get_event_loop().run_forever(ws.run_server()) 
   # print(f"WS: Running")

   @appd.flask_app.route("/")
   def f_root():
      return redirect(url_for("f_index_1"))
   
   @appd.flask_app.route("/index")
   def f_index_1():
      print(f"FLASK: /index/0")
      return render_template("index.html", available_image_count=appd.available_image_count, image_to_request=0)
   
   @appd.flask_app.route("/index/<int:img_to_request>")
   def f_index_2(img_to_request):
      print(f"FLASK: /index/{img_to_request}")
      return render_template("index.html", 
                             available_image_count=appd.available_image_count, 
                             image_to_request=img_to_request,
                             ws_host=consts.WS_HOST,
                             ws_port=consts.WS_PORT)
   
   
   @appd.flask_app.route("/ingest/new-image", methods=["POST"])
   def f_ingest_image():
      if type(request.data) is bytes:
         print(f"FLASK: /ingest/new-image Recv {len(request.data)} bytes")
         # DB: Add image
         cursor = appd.db_connection.cursor()
         cursor.execute(""" INSERT INTO history (img) VALUES (?) """, (request.data,))
         # DB: Cap at 10 images max
         img_count = cursor.execute(""" SELECT count() FROM history""").fetchone()[0]
         if type(img_count) != int: 
            raise TypeError(f"Expected int, but got {type(img_count)}")
         if img_count > consts.MAX_DB_IMAGE_COUNT:
            print(f"DB: Image count: {img_count} - {consts.MAX_DB_IMAGE_COUNT} => rem {img_count - consts.MAX_DB_IMAGE_COUNT}")
            cursor.execute(""" 
                           DELETE FROM history
                           WHERE id IN (
                              SELECT id FROM history
                              ORDER BY id
                              LIMIT ?
                           );
                           """, (img_count - consts.MAX_DB_IMAGE_COUNT,))
            img_count = consts.MAX_DB_IMAGE_COUNT
         
         appd.db_connection.commit()
         print(f"DB: added image - new count: {img_count}")
         appd.available_image_count = img_count
         events.NEW_IMG_EVENT.set()
         return "OK"
      else:
         print(f"FLASK: /ingest/new-image invalid data: {type(request.data)}")
         return "INVALID DATA"
   
   return appd.flask_app