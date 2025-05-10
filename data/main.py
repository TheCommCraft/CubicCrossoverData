from flask import Flask, redirect
from .files import Content, Collection
from threading import Thread
from dotenv import load_dotenv
import os, time, random
from .exceptions import *
from scratchattach import login_by_id, TwCloud
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

app = Flask("")

@app.route("/")
def home():
  return redirect("https://turbowarp.org/824262326/embed?autoplay")
@app.route("/tw/")
def tw():
  a = redirect("https://turbowarp.org/824262326/embed?autoplay")
  return a

def run():
  app.run(host='0.0.0.0', port=6278)

def keep_alive():
  t = Thread(target=run)
  t.start()

keep_alive()

def get_account(user):
  if not user in data["users"]:
    data["users"][user] = {"levels": []}
  return data["users"][user]

data = Collection("data", loadcontents=True)
logs = Content("logs", load=True)

PID = 824262326

session = login_by_id(os.environ["SESSION_ID"], username="StrangeIntensity")
project = session.connect_project(PID)
conn = session.connect_cloud(project_id = PID) 
tw_conn = TwCloud(project_id = PID)  

#events = conn.events()
client = conn.requests(used_cloud_vars=["1", "2", "3"])
twclient = tw_conn.requests(used_cloud_vars=["1", "2", "3"])

def find_comment(name: str, __id: str) -> str:
    return [i.author_name for i in project.comments() if i.content == f"{name} at {__id}"][0]

'''@events.event
def on_set(event): #Called when a cloud var is set
    print(f"{event.user} set the variable {event.var} to the value {event.value} at {event.timestamp}")'''

def add_level(id=None, *, ldata=None, output=None):
  if id is None and ldata is None:
    raise TypeError("add_level expected 1 argument got 0")
  if not id in (_l := data["levels"]):
    raise InvalidLevelError
  (ldata := _l[id].data.copy() if ldata is None else ldata.copy()).pop("content")
  lviews = ldata["views"] + len(ldata.get("likes", [])) * 5
  output = data["tabs"]["popular"]["content"] if output is None else output
  for i in output.copy():
    if i["id"] == ldata["id"]:
      output.remove(i)
  idx = 0
  for idx, i in enumerate(output):
    if i["views"] + len(i.get("likes", [])) * 5 < lviews:
      output.insert(idx, ldata)
      break
  else:
    idx += 1
    output.append(ldata)
  print(idx)
  while len(output) > 50:
    output.pop(-1)

#events.start(thread=True)

@client.event
def on_request(request):
  print("Received request")
  if request.request in ["loadlevel", "loadtab", "random", "like", "unlike"]:
    return
  logs["logs"].append([request.requester, request.request.name, request.arguments, request.timestamp])
  logs.write()

@client.request(name="loadtab")
def load_tab(tab):
  tab = int(tab)
  print(f"Loading tab {tab}...")
  if tab == 0:
    tab = []
    for i in data["tabs"]["popular"]["content"][:10]:
      tab.extend((
        i["name"],
        (level_id := i["id"]),
        i["creator"],
        str(data["levels"][level_id]["views"]),
        str(len(i.get("likes", []))),
        ""
      ))
    return tab
  if tab == 1:
    tab = []
    for i in list(reversed(data["tabs"]["new"]["content"]))[:10]:
      tab.extend((
        data["levels"][i]["name"],
        i,
        data["levels"][i]["creator"],
        str(data["levels"][i]["views"]),
        str(len(data["levels"][i].data.get("likes", []))),
        ""
      ))
    return tab
  if tab == 2:
    tab = []
    for i in reversed(get_account(client.get_requester())["levels"]):
      tab.extend((
        data["levels"][i]["name"],
        i,
        data["levels"][i]["creator"],
        str(data["levels"][i]["views"]),
        str(len(data["levels"][i].data.get("likes", []))),
        ""
      ))
    return tab
  return ["Nothing here", "none", "", "", "", ""]
  
@twclient.request(name="loadtab")
def tw_load_tab(tab):
  tab = int(tab)
  print(f"Loading tab {tab}...")
  if tab == 0:
    tab = []
    for i in data["tabs"]["popular"]["content"]:
      tab.extend((
        i["name"],
        (level_id := i["id"]),
        i["creator"],
        str(data["levels"][level_id]["views"]),
        str(len(i.get("likes", []))),
        ""
      ))
    return tab
  if tab == 1:
    tab = []
    for i in list(reversed(data["tabs"]["new"]["content"]))[:100]:
      tab.extend((
        data["levels"][i]["name"],
        i,
        data["levels"][i]["creator"],
        str(data["levels"][i]["views"]),
        str(len(data["levels"][i].data.get("likes", []))),
        ""
      ))
    return tab
  return ["Nothing here", "none", "", "", "", ""]
  
@client.request(name="like")
def like_level(level_id):
  if not level_id in (_l := data["levels"]):
    raise InvalidLevelError
  if not "likes" in _l[level_id]:
    _l[level_id]["likes"] = []
  if not client.get_requester() in _l[level_id]["likes"]:
    _l[level_id]["likes"].append(client.get_requester())
  add_level(level_id)
  return _l[level_id]["content"]

@client.request(name="unlike")
def unlike_level(level_id):
  if not level_id in (_l := data["levels"]):
    raise InvalidLevelError
  if not "likes" in _l[level_id]:
    _l[level_id]["likes"] = []
  if client.get_requester() in _l[level_id]["likes"]:
    _l[level_id]["likes"].remove(client.get_requester())
  add_level(level_id)
  return _l[level_id]["content"]

@twclient.request(name="like")
def tw_like_level(level_id):
  if not level_id in (_l := data["levels"]):
    raise InvalidLevelError
  if not "likes" in _l[level_id]:
    _l[level_id]["likes"] = []
  _l[level_id]["likes"].append("twuser")
  add_level(level_id)
  return _l[level_id]["content"]

@twclient.request(name="unlike")
def tw_unlike_level(level_id):
  if not level_id in (_l := data["levels"]):
    raise InvalidLevelError
  if not "likes" in _l[level_id]:
    _l[level_id]["likes"] = []
  if "twuser" in _l[level_id]["likes"]:
    _l[level_id]["likes"].remove("twuser")
  add_level(level_id)
  return _l[level_id]["content"]

@client.request(name="random")
def random_level():
  level_id = random.choice(list((_l := data["levels"]).data.keys()))
  if not level_id in _l:
    raise InvalidLevelError
  _l[level_id]["views"] += 1
  add_level(level_id)
  return [level_id, _l[level_id]["content"]]
  
@twclient.request(name="random")
def tw_random_level():
  level_id = random.choice(list((_l := data["levels"]).data.keys()))
  if not level_id in _l:
    raise InvalidLevelError
  _l[level_id]["views"] += 1
  add_level(level_id)
  return [level_id, _l[level_id]["content"]]

@client.request(name="loadlevel")
def load_level(level_id):
  if not level_id in (_l := data["levels"]):
    raise InvalidLevelError
  _l[level_id]["views"] += 1
  add_level(level_id)
  return _l[level_id]["content"]

@twclient.request(name="loadlevel")
def tw_load_level(level_id):
  if not level_id in (_l := data["levels"]):
    raise InvalidLevelError
  _l[level_id]["views"] += 1
  add_level(level_id)
  return _l[level_id]["content"]

@client.request(name="savelevel")
def save_level(level_id, level_name, *content):
  content = "&".join(content)
  if level_id in data["levels"]:
    if client.get_requester() != data["levels"][level_id]["creator"]:
      return "No"
    #try:
    #  if not level_id in data["users"][client.get_requester()]["levels"]:
    #    return "No"
    #except:
    #  return "No"
    if level_name != "none":
      data["levels"][level_id]["name"] = level_name
    if content != "none":
      data["levels"][level_id]["content"] = content
  else:
    data["levels"][level_id] = {"name": level_name, "id": level_id, "views": 0, "creator": client.get_requester(), "content": content}
    data["tabs"]["new"]["content"].append(level_id)
    if len(data["tabs"]["new"]["content"]) > 1000:
      data["tabs"]["new"]["content"] = data["tabs"]["new"]["content"][-1000:]
    get_account(client.get_requester())["levels"].append(level_id)
  data["levels"][level_id].write()
  print("saved level")
  return "Yes"

@twclient.request(name="savelevel")
def save_level(level_id, level_name, *content):
  content = "&".join(content)
  try:
        author = find_comment(level_name, level_id)
  except IndexError:
    return "No"
  if level_id in data["levels"]:
    if author != data["levels"][level_id]["creator"]:
      return "No"
    #try:
    #  if not level_id in data["users"][client.get_requester()]["levels"]:
    #    return "No"
    #except:
    #  return "No"
    if level_name != "none":
      data["levels"][level_id]["name"] = level_name
    if content != "none":
      data["levels"][level_id]["content"] = content
  else:
    data["levels"][level_id] = {"name": level_name, "id": level_id, "views": 0, "creator": author, "content": content}
    data["tabs"]["new"]["content"].append(level_id)
    if len(data["tabs"]["new"]["content"]) > 1000:
      data["tabs"]["new"]["content"] = data["tabs"]["new"]["content"][-1000:]
    get_account(author)["levels"].append(level_id)
  data["levels"][level_id].write()
  print("saved level")
  return "Yes"

client.start()
twclient.start()

while True:
  time.sleep(300)
  data.write()