import sys
sys.path.insert(0, 'libs')
import webapp2
import json
from google.appengine.api import users
from google.appengine.ext import ndb
import datetime
from time import *
import foursquare
DEFAULT_TR_NAME = 'def_trans'
formatString = "%d/%m/%Y %H:%M:%S:%f"

def transaction_key(name=DEFAULT_TR_NAME):
    return ndb.Key('Trans', name)

class User(ndb.Model):
    """Sub model for representing an author."""
    identity = ndb.StringProperty(indexed=True)
    email = ndb.StringProperty(indexed=True)

class Item(ndb.Model):
    price = ndb.FloatProperty(indexed=False)
    storeName = ndb.StringProperty(indexed=False)
    storeCat = ndb.StringProperty(indexed=False)
    name = ndb.StringProperty(indexed=False)
    loc = ndb.GeoPtProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=False)
    dateAdded = ndb.DateTimeProperty(auto_now_add=True)

class Trans(ndb.Model):
    author = ndb.StructuredProperty(User)
    item = ndb.StructuredProperty(Item)

class Settings(ndb.Model):
    author = ndb.StructuredProperty(User)
    budget = ndb.FloatProperty(indexed=False)
    foursquare = ndb.BooleanProperty(indexed=False)
    startDay = ndb.IntegerProperty(indexed=False)

def makeDicItem(trans):
    ret = dict()
    ret["price"]=trans.item.price
    ret["storename"]=trans.item.storeName
    ret["storecat"]=trans.item.storeCat
    ret["name"]=trans.item.name
    ret["date"]=trans.item.date.strftime(formatString)
    ret["key"]=trans.item.dateAdded.strftime(formatString)
    return ret

class getRemainingBudget(webapp2.RequestHandler):
    def get(self):
        author=""
        user = ""
        if users.get_current_user():
            user = users.get_current_user()
            author = User(
                    identity=user.user_id(),
                    email=user.email())
        elif( self.request.get('usrx') == '1'):
            author = User(
                    identity="1",
                    email="d@d.com")
        else:
            self.error(555)
            self.response.out.write('error in the request, no user')
            return
        
        startDay = 1
        queryx = Settings.query(Settings.author == author)
        budget = 0.0
        for i in queryx:
            budget = i.budget
            startDay = i.startDay
        
        date = datetime.datetime.now()
        y = date.year
        m = date.month
        d = date.day
        if d < startDay:
            m = m-1
        if m < 1:
            m = m+12
            y = y-1
        startD = datetime.datetime(y,m,startDay,0,0,0,0)
        query = Trans.query(Trans.author == author, Trans.item.dateAdded >= startD)
        for i in query:
            budget = budget - i.item.price

        md = dict()
        md["budget"] = budget
        self.response.headers['Content-Type'] = 'application/json'
        self.response.headers['access-control-allow-origin'] = '*'
        self.response.write(json.dumps(md))

class getTrans(webapp2.RequestHandler):
    def get(self):
        author=""
        user = ""
        if users.get_current_user():
            user = users.get_current_user()
            author = User(
                    identity=user.user_id(),
                    email=user.email())
        elif( self.request.get('usrx') == '1'):
            author = User(
                    identity="1",
                    email="d@d.com")
        else:
            self.error(555)
            self.response.out.write('error in the request, no user')
            return

        date = datetime.datetime.now()
        x = self.request.get('date')
        if(x):
            date = datetime.datetime.strptime(x, formatString)
        num = 10
        y = self.request.get('num')
        if(y):
            num = int(y)
        query = Trans.query(Trans.author == author, Trans.item.dateAdded < date).order(-Trans.item.dateAdded)
        retls = []

        for i in query:
            retls.append(makeDicItem(i))
            num = num - 1
            if(num <= 0):
                break
        self.response.headers['access-control-allow-origin'] = '*'
        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(json.dumps(retls))

class delTrans(webapp2.RequestHandler):
    def post(self):
        author=""
        user = ""
        if users.get_current_user():
            user = users.get_current_user()
            author = User(
                    identity=user.user_id(),
                    email=user.email())
        elif( self.request.get('usrx') == '1'):
            author = User(
                    identity="1",
                    email="d@d.com")
        else:
            self.error(555)
            self.response.out.write('error in the request, no user')
            return

        date = datetime.datetime.now()
        x = self.request.get('date')
        if(x):
            date = datetime.datetime.strptime(x, formatString)
        else:
            self.error(555)
            self.response.out.write('error in the request, no date')
            return
        query = Trans.query(Trans.author == author, Trans.item.dateAdded == date)
        for i in query:
            print "WE ARE DELETING!!!"
            i.key.delete()
        self.response.headers['access-control-allow-origin'] = '*'

class setSettings(webapp2.RequestHandler):
    def post(self):
        budget = float(self.request.get('budget'))
        foursquare = self.request.get('foursquare') in ["true", "True"]
        startDay = int(self.request.get('startDay'))
        
        author=""
        user = ""
        if users.get_current_user():
            user = users.get_current_user()
            author = User(
                    identity=user.user_id(),
                    email=user.email())
        elif( self.request.get('usrx') == '1'):
            author = User(
                    identity="1",
                    email="d@d.com")
        else:
            self.error(555)
            self.response.out.write('error in the request, no user')
            return

        print author.identity
        print author.email
        query = Settings.query(Settings.author == author)
        if(query):
            for i in query:
                i.key.delete()
        settings = Settings(
                author=author,
                budget=budget,
                foursquare=foursquare,
                startDay=startDay
            )
        settings.put()
        self.response.headers['access-control-allow-origin'] = '*'

class getSettings(webapp2.RequestHandler):
    def get(self):
        author=""
        user = ""
        if users.get_current_user():
            user = users.get_current_user()
            author = User(
                    identity=user.user_id(),
                    email=user.email())
        elif( self.request.get('usrx') == '1'):
            author = User(
                    identity="1",
                    email="d@d.com")
        else:
            self.error(555)
            self.response.out.write('error in the request, no user')
            return

        query = Settings.query(Settings.author == author)
        md = dict()
        for i in query:
            md["budget"] = i.budget
            md["foursquare"] = i.foursquare
            md["startDay"] = i.startDay
            md["email"] = author.email
        self.response.headers['access-control-allow-origin'] = '*'
        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(json.dumps(md))

class MainPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        self.response.headers['access-control-allow-origin'] = '*'
        if user:
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write('Hello, ' + user.nickname())
        else:
            self.redirect(users.create_login_url(self.request.uri))

class LocQuerry(webapp2.RequestHandler):
    def get(self):
        lat = float(self.request.get('lat'))
        lon = float(self.request.get('lon'))
        ls = foursquare.getSuggestions(lat,lon)
        retls = []
        for i in ls:
            md = dict()
            md["name"] = i.getName()
            md["category"] = i.getCategory()
            md["distance"] = i.getDistance()
            retls.append(md)
        self.response.headers['access-control-allow-origin'] = '*'
        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(json.dumps(retls))


class AddItem(webapp2.RequestHandler):
    def post(self):
        # Checks for active Google account session
        
        user = users.get_current_user()
        tra = Trans(parent=transaction_key())

        iPrice = float(self.request.get('price'))
        storeName = self.request.get('store')
        storeCat = self.request.get('storecat')
        name = self.request.get('name')
        lat = float(self.request.get('lat'))
        lon = float(self.request.get('lon'))
        loc = ndb.GeoPt(lat,lon)
        date = datetime.datetime.now()

        if users.get_current_user():
            tra.author = User(
                    identity=user.user_id(),
                    email=user.email())
        elif( self.request.get('usrx') == '1'):
            tra.author = User(
                    identity="1",
                    email="d@d.com")
        else:
            self.error(555)
            self.response.out.write('error in the request, no user')
            return

        tra.item = Item(
                price = iPrice,
                storeName = storeName,
                storeCat = storeCat,
                name = name,
                loc = loc,
                date = date
            )
        self.response.headers['access-control-allow-origin'] = '*'
        tra.put()

class LoginC(webapp2.RequestHandler):
    def get(self):

        user = users.get_current_user()
        self.response.headers['access-control-allow-origin'] = '*'
        if user:
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write('Hello, ' + user.nickname())
        else:
            self.redirect(users.create_login_url(self.request.uri))


application = webapp2.WSGIApplication([
    ('/addItem', AddItem), ('/', LoginC), ('/login', LoginC), ('/ql', LocQuerry), ('/setSettings', setSettings), ('/getSettings', getSettings)
    , ('/getTrans', getTrans), ('/delTrans', delTrans), ("/getRemainingBudget",getRemainingBudget)
], debug=True)
