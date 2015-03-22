import sys
sys.path.insert(0, 'libs')
import webapp2
import json
from google.appengine.api import users
from google.appengine.ext import ndb
import datetime
from time import *
import foursquare
import calendar
import random
DEFAULT_TR_NAME = 'def_trans'
formatString = "%d/%m/%Y %H:%M:%S:%f"
categories = ["Food","Health","Clothing","Bills","Other","Entertainment","Electronics"]
geoo = [(51.492,-0.148),(50.903,-1.407),(52.409,-1.512),(51.526,-0.139),(53.484,-2.242),(53.407,-2.988)]

def transaction_key(name=DEFAULT_TR_NAME):
    return ndb.Key('Trans', name)

class User(ndb.Model):
    """Sub model for representing an author."""
    identity = ndb.StringProperty(indexed=True)
    email = ndb.StringProperty(indexed=True)

class Item(ndb.Model):
    price = ndb.FloatProperty(indexed=False)
    storeName = ndb.StringProperty(indexed=False)
    storeCat = ndb.StringProperty(indexed=True)
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
        
        totalbudget = budget

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
        totaldays = calendar.monthrange(y,m)[1]
        days = (date-startD).days
        days = totaldays - days

        query = Trans.query(Trans.author == author, Trans.item.dateAdded >= startD)
        for i in query:
            budget = budget - i.item.price

        status = "You are on budget"
        
        if(budget*totaldays > totalbudget*days):
            status = "You are under budget"
        elif(budget*totaldays < totalbudget*days):
            status = "You are over budget"

        md = dict()
        md["budget"] = int(budget)
        md["status"] = status
        
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
        num = 50
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
        mh = dict()
        mh["key"] = tra.item.dateAdded.strftime(formatString)
        self.response.write(json.dumps(mh))

class getInsights(webapp2.RequestHandler):
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
        totaldays = calendar.monthrange(y,m)[1]
        days = (date-startD).days
        text = []

#pie stuff
        pichartM = {}
        totalM = 0
        pichartT = {}
        totalT = 0
        
        for c in categories:
            pichartM[c] = 0
            pichartT[c] = 0

        query1 = Trans.query(Trans.author == author, Trans.item.date >= startD)
        for t in query1:
            c = t.item.storeCat
            pichartM[c] = pichartM[c] + t.item.price 
            totalM = totalM + t.item.price
        
        query2 = Trans.query(Trans.author == author)
        for t in query2:
            c = t.item.storeCat
            pichartT[c] = pichartT[c] + t.item.price
            totalT = totalT + t.item.price



#burndown stuff
        burndown = {}
        for i in range(0,totaldays):
            burndown[i] = 0


#heatmap stuff
        heatmapM = {}
        heatmapT = {}
        maxM = 0
        maxT = 0
        heatM = (-1,-1)
        heatT = (-1,-1)

        for i in range(0,7):
            heatmapM[i] = {}
            heatmapT[i] = {}
            for j in range(0,12):
                heatmapM[i][j] = 0
                heatmapT[i][j] = 0
        
        query1 = Trans.query(Trans.author == author, Trans.item.date >= startD)
        for t in query1:
            x = t.item.date.weekday()
            y = t.item.date.hour / 2
            z = (t.item.date - startD).days
            burndown[z+1] = burndown[z+1] + t.item.price
            print z,burndown[z]
            heatmapM[x][y] = heatmapM[x][y] + t.item.price
            if(heatmapM[x][y] > maxM):
                maxM = heatmapM[x][y]
                heatM = (x,y)

        query2 = Trans.query(Trans.author == author)
        for t in query2:
            x = t.item.date.weekday()
            y = t.item.date.hour / 2
            heatmapT[x][y] = heatmapT[x][y] + t.item.price
            if(heatmapT[x][y] > maxT):
                maxT = heatmapT[x][y]
                heatT = (x,y)
 
 #normalize pie
        maxpM = 0
        maxpT = 0
        catM = ""
        catT = ""

        if totalM == 0:
            pichartM = "none"
        else:
            for c in categories:
                if pichartM[c] > maxpM:
                    maxpM = pichartM[c]
                    catM = c
                pichartM[c] = 1.0*pichartM[c]/totalM        
            text.append("You spent the greatest part of this month's budget in the category "+catM)

        if totalT == 0:
            pichartT = "none"
        else:
            for c in categories:
                if pichartT[c] > maxpT:
                    maxpT = pichartT[c]
                    catT = c
                pichartT[c] = 1.0*pichartT[c]/totalT
            text.append("You generally spend the greatest part of your budget in the category "+catT)

       
#normalize burndown
        summ = budget
        for i in range(0,days+1):
            burndown[i] = summ
            summ = summ - burndown[i+1]
         
#normalize heatmaps
        if maxM == 0:
            heatmapM = "none"
        else:

            for i in range(0,7):
                for j in range(0,12):
                    heatmapM[i][j] = 1.0*heatmapM[i][j]/maxM
            
        if maxT == 0:
            heatmapT = "none"
        else:
            for i in range(0,7):
                for j in range(0,12):
                    heatmapT[i][j] = 1.0*heatmapT[i][j]/maxT

#other text stuff

#return everything
        ret = {}
        ret['PieMonth'] = pichartM
        ret['PieTotal'] = pichartT
        ret['HeatMonth'] = heatmapM
        ret['HeatTotal'] = heatmapT
        ret['Burndown'] = burndown
        ret['Text'] = text
        self.response.headers['access-control-allow-origin'] = '*'
        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(json.dumps(ret))

class LoginC(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        self.response.headers['access-control-allow-origin'] = '*'
        if user:
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write('Hello, ' + user.nickname())
        else:
            self.redirect(users.create_login_url(self.request.uri))

itemList = ["item1", "item2", "item3", "item4"]

class generateData(webapp2.RequestHandler):
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
        self.response.headers['access-control-allow-origin'] = '*'
        dateStart = datetime.datetime.now() - datetime.timedelta(days=365)

        while(dateStart < datetime.datetime.now()):
            dateStart = dateStart + datetime.timedelta(minutes=random.randint(60,60*24))
            if dateStart > datetime.datetime.now():
                break
            if(dateStart.hour <= 8):
                dateStart = dateStart + datetime.timedelta(hours=12)
            tra = Trans(parent=transaction_key())
            location = random.choice(geoo)
            loc = ndb.GeoPt(location[0],location[1])
            ls = foursquare.getSuggestions(location[0],location[1])
            
            tra.author = author
            tra.item = Item(
                price = random.random()*25.0,
                storeName = random.choice(ls).getName(),
                storeCat = random.choice(categories),
                name = random.choice(itemList),
                loc = loc,
                date = dateStart
            )
            tra.put()
        self.response.write("Succes!!!")


application = webapp2.WSGIApplication([
    ('/addItem', AddItem), ('/', LoginC), ('/login', LoginC), ('/ql', LocQuerry), ('/setSettings', setSettings), ('/getSettings', getSettings)
    , ('/getInsights', getInsights), ('/getTrans', getTrans), ('/delTrans', delTrans), ("/getRemainingBudget",getRemainingBudget),
    ("/81411deff77867f34a45900c29d133378fa80c9d98acc56a063a1a65b8be5d2c", generateData)
], debug=True)
