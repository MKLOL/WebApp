import foursquare

ls = foursquare.getSuggestions(51.526231, -0.139436)

for x in ls:
    print x.getName()
