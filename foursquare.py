import urlparse
import requests
import json
import datetime

cID = "05RTOMSTFEIT315XDJAB4P4AM1ECE5301CWSEHHQDZAIC20K"
secret = "H3J20JIH0CHLRZ045XLDFOA0HFOLVIPDC3SWDW2GJ5TDJSA4"
categories = ['Store', 'Supermarket', 'Restaurant', 'Bar', 'Shop']

class Venue:
    def __init__(self, name, category, distance):
        self.name = name
        self.category = category
        self.distance = distance
    def __lt__(self, other):
        return self.distance < other.distance
    def getName(self):
        return self.name
    def getCategory(self):
        return self.category
    def getDistance(self):
        return self.distance

def getSuggestions(lat, lon):
    venueList = []
    date = datetime.date.today().strftime("%Y%m%d")
    url = "https://api.foursquare.com/v2/venues/search?ll="+str(lat)+","+str(lon)+"&client_id="+cID+"&client_secret="+secret+"&v="+date    
    content = requests.get(url).content 

    if content[1]=='<':
        return []
    
    venues = json.loads(content)['response']['venues']
    
    for v in venues:
        relevant = False
        for c in v['categories']:
            for x in categories:
                if x in c['name']:
                    relevant = True
        if relevant == True:
            venueList.append(Venue(v['name'],c['name'],v['location']['distance']))

    venueList.sort()
    nr = min(len(venueList),5)
    return venueList[:nr]
