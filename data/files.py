import os, json, shutil

class Collection:
  def __init__(self, path, *, loadcontents=False, load=False, write=False, delete=False, data=None, mkdir=True, collections=None):
    if os.path.exists(path) and os.path.isfile(path):
      raise Exception
    if loadcontents and delete:
      raise ValueError
    if mkdir and not os.path.exists(path):
      os.mkdir(path)
    collections = {} if collections is None else collections
    self.path = path
    self.data = {} if data is None else data
    self.data = {key: Content(f"{self.path}/{key}", data=item, write=write, load=load) for key, item in self.data.items()}
    for i in collections:
      self.data[i] = collections[i]
    if loadcontents:
      for i in os.listdir(self.path):
        if i in self.data:
          continue
        if os.path.isfile(f := f"{self.path}/{i}"):
          self.data[i] = Content(f, load=True)
          continue
        self.data[i] = Collection(f, loadcontents=True, load=True)
    if delete:
      for i in os.listdir(self.path):
        if i in self.data:
          continue
        shutil.rmtree(f'{self.path}/{i}')
    self.path = path
    self._data = 0
  def __contains__(self, item):
    return item in self.data
  def __getitem__(self, item):
    return self.data[item]
  def __setitem__(self, item, value):
    if isinstance(value, (Collection, Content)):
      self.data[item] = value
      return
    self.data[item] = Content(f"{self.path}/{item}", data=value, write=True)
  def write(self):
    if self._data == hash(self):
      return
    self._data = hash(self)
    for _, i in self.data.items():
      i.write()
  def __hash__(self):
    return hash(tuple(self.data.items()))

class Content:
  def __init__(self, path, *, load=False, write=False, data=None):
    if write and data is None:
      raise ValueError
    self.autowrite = False
    self.path = path
    self.data = {}
    self._data = 0
    try:
     if load:
      with open(self.path) as f:
        for i in (c := json.load(f)):
          self.data[i] = c[i]
    except:
      print(self.path)
    if data:
      for key, item in data.items():
        self.data[key] = item
    if write:
      self.write()
  def __contains__(self, item):
    return item in self.data
  def __getitem__(self, item):
    return self.data[item]
  def __setitem__(self, item, value):
    self.data[item] = value
    if self.autowrite:
      self.write()
  def write(self, data=None):
    data = self.data if data is None else data
    if hash(self) == self._data:
      return
    with open(self.path, "w") as f:
      self._write(f, data)
  def _write(self, file, data):
    if self.data != data:
      self.data = data
    if self._data != hash(self):
      self._data = hash(self)
    json.dump(data, file)
  def __hash__(self):
    return hash(json.dumps(self.data))