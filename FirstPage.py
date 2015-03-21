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

def transaction_key(guestbook_name=DEFAULT_TR_NAME):
    """Constructs a Datastore key for a Guestbook entity.

    We use guestbook_name as the key.
    """
    return ndb.Key('Trans', guestbook_name)

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
        if users.get_current_user():
            author = User(
                    identity=user.user_id(),
                    email=user.email())
        elif( self.request.get('usrx') == '1'):
            author = User(
                    identity="1",
                    email="d@d.com")
        else:
            self.error(404)
            self.response.out.write('error in the request, no user')
            return

        date = datetime.datetime.now()
        startD = datetime.datetime(date.year,date.month,1,0,0,0,0)
        query = Trans.query(Trans.author == author, Trans.item.dateAdded >= startD)
        queryx = Settings.query(Settings.author == author)
        budget = 0.0
        for i in queryx:
            budget = i.budget
        for i in query:
            budget = budget - i.item.price

        md = dict()
        md["budget"] = budget
        self.response.write(json.dumps(md))

class getTrans(webapp2.RequestHandler):
    def get(self):
        author=""
        if users.get_current_user():
            author = User(
                    identity=user.user_id(),
                    email=user.email())
        elif( self.request.get('usrx') == '1'):
            author = User(
                    identity="1",
                    email="d@d.com")
        else:
            self.error(404)
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
            print "\n\n!!!\n\n"
            retls.append(makeDicItem(i))
            num = num - 1
            if(num <= 0):
                break
        self.response.write(json.dumps(retls))

class delTrans(webapp2.RequestHandler):
    def post(self):
        author=""
        if users.get_current_user():
            author = User(
                    identity=user.user_id(),
                    email=user.email())
        elif( self.request.get('usrx') == '1'):
            author = User(
                    identity="1",
                    email="d@d.com")
        else:
            self.error(500)
            self.response.out.write('error in the request, no user')
            return
        date = datetime.datetime.now()
        x = self.request.get('date')
        if(x):
            date = datetime.datetime.strptime(x, formatString)
        else:
            self.error(500)
            self.response.out.write('error in the request, no date')
            return
        query = Trans.query(Trans.author == author, Trans.item.dateAdded == date)
        for i in query:
            print "WE ARE DELETING!!!"
            i.key.delete()

        

class setSettings(webapp2.RequestHandler):
    def post(self):
        budget = float(self.request.get('budget'))
        foursquare = self.request.get('foursquare') in ["true", "True"]
        author=""
        if users.get_current_user():
            author = User(
                    identity=user.user_id(),
                    email=user.email())
        elif( self.request.get('usrx') == '1'):
            author = User(
                    identity="1",
                    email="d@d.com")
        else:
            self.error(404)
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
                foursquare=foursquare
            )
        print foursquare
        settings.put()
        self.response.write("Succes")

class getSettings(webapp2.RequestHandler):
    def get(self):
        author=""
        if users.get_current_user():
            author = User(
                    identity=user.user_id(),
                    email=user.email())
        elif( self.request.get('usrx') == '1'):
            author = User(
                    identity="1",
                    email="d@d.com")
        else:
            self.error(404)
            self.response.out.write('error in the request, no user')
            return
        query = Settings.query(Settings.author == author)
        md = dict()
        for i in query:
            md["budget"] = i.budget
            md["foursquare"] = i.foursquare

        self.response.write(json.dumps(md))

class MainPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()

        if user:
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write('Hello, ' + user.nickname())
        else:
            self.redirect(users.create_login_url(self.request.uri))

class LocQuerry(webapp2.RequestHandler):
    def get(self):
        pass
        lat = float(self.request.get('lat'))
        lon = float(self.request.get('lon'))
        ls = foursquare.getSuggestions(lat,lon)
        self.response.headers['Content-Type'] = 'json/application'
        retls = []
        for i in ls:
            md = dict()
            md["name"] = i.getName()
            md["category"] = i.getCategory()
            md["distance"] = i.getDistance()
            retls.append(md)
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
            self.error(404)
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

        tra.put()

        self.response.write("success")

class MainS(webapp2.RequestHandler):
    def get(self):
        # Checks for active Google account session
        userId=0
        uEmail="d@d.com"
        if users.get_current_user():
            userId=user.user_id()
            uEmail=user.email()
        elif( self.request.get('usrx') == '1'):
            userId='1'
        else:
            self.error(404)
            self.response.out.write('error in the request, no user')
            return
        q = Trans.query()
        for i in q:
            self.response.write(i.item.price)

class LoginC(webapp2.RequestHandler):
    def get(self):
        # Checks for active Google account session

        user = users.get_current_user()

        if users.get_current_user():
            greeting.author = User(
                    identity=user.user_id(),
                    email=user.email())



        if user:
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write('Hello, ' + user.nickname())
        else:
            self.redirect(users.create_login_url(self.request.uri))


application = webapp2.WSGIApplication([
    ('/addItem', AddItem), ('/', MainS), ('/login', LoginC), ('/ql', LocQuerry), ('/setSettings', setSettings), ('/getSettings', getSettings)
    , ('/getTrans', getTrans), ('/delTrans', delTrans), ("/getRemainingBudget",getRemainingBudget)
], debug=True)