import json
from collections import OrderedDict
from datetime import datetime
from typing import List

import numpy as np

class SimpleRepr(object):
    """A mixin implementing a simple __repr__."""
    def __repr__(self):
        return "<{klass} @{id:x} {attrs}>".format(
            klass=self.__class__.__name__,
            id=id(self) & 0xFFFFFF,
            attrs=" ".join("{}={!r}".format(k, v) for k, v in self.__dict__.items()),
            )

class Point(SimpleRepr) :
   def __init__(self, x, y, score=None):
      self.x = x
      self.y = y

      # For maximas only
      self.score = score

class Action(SimpleRepr) :
   def __init__(self, country, region, date, actorId):
      self.country = country
      self.region = region
      self.date = date
      self.actorId = actorId

class Click(Point) :
   def __init__(self, x, y, action=None, score=None):
      super().__init__(x, y)
      self.action = action
      if score is not None :
        self.score=score

class Polygon(SimpleRepr) :
    def __init__(self, action=None, score=None, area=None):
        self.points = []
        if action is not None :
            self.action = action
        if score is not None:
            self.score = score
        if area is not None:
            self.area = area

class Image(SimpleRepr) :
   def __init__(self, id, city, department, region, install_id):
      self.clicks=[]
      self.notPvActions = []
      self.polygons = []
      self.id = id
      self.city = city
      self.department = department
      self.region = region
      self.install_id = install_id

class ClickResult(SimpleRepr) :
    def __init__(self, id):
        self.id = id
        self.clicks = []

class SurfaceResult(SimpleRepr):
    def __init__(self, id):
        self.id = id
        self.polygons : List[Polygon] = []

# Register classes by names
CLASSES = dict()
for clazz in Point, Action, Click, Polygon, Image, ClickResult, SurfaceResult:
    CLASSES[clazz.__name__] = clazz

def np_encoder(object):
    if isinstance(object, np.generic):
        return object.item()

def to_dict(data) :
   """Recursively transform any object to dict"""
   if data is None :
      return None
   if type(data) in (int, str, float, bool) or isinstance(data, np.generic):
      return data
   elif isinstance(data, list) :
      return list(to_dict(item) for item in data)
   elif isinstance(data, dict) :
      return {key: to_dict(val) for key, val in data.items() if val is not None}
   elif isinstance(data, datetime) :
      return data.isoformat()
   elif hasattr(data, '__dict__') :
      dic = OrderedDict()
      dic["@type"] = type(data).__name__
      dic.update(data.__dict__)
      return to_dict(dic)
   else :
      raise Exception("Not supported type ", type(data))

def to_json(data, outfile) :
    out = open(outfile, "w") if isinstance(outfile, str) else outfile
    json.dump(to_dict(data), out, indent=2, default=np_encoder)

def parse_dict(data) :
    """ Load a nested structure of dict into python objects """
    if data is None:
        return None
    if type(data) in (int, str, float, bool):
        return data
    elif isinstance(data, list):
        return list(parse_dict(item) for item in data)

    elif isinstance(data, dict):
        if "@type" in data :
            # Instanciate the class
            typeName = data.pop("@type")
            clazz = CLASSES[typeName]
            inst = clazz.__new__(clazz)
            for key, val in data.items() :
                setattr(inst, key, parse_dict(val))
            return inst
        else :
            # Raw dict
            return {key: parse_dict(val) for key, val in data.items()}
    else :
        raise Exception("Unsupported type", type(data))