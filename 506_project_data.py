import requests_oauthlib
import webbrowser
import json
import dota2api
import requests
import os
import collections
import pickle
import datetime
from datetime import timedelta
import time
import unittest

# Create instances for each individual match
class matchdetail():
    def __init__(self, match):
        self.match_id = match[u'result'][u'match_id']
        self.radiant_win = match[u'result'][u'radiant_win']
        self.radiant_score = match[u'result'][u'radiant_score']
        self.dire_score = match[u'result'][u'dire_score']
        self.players = match[u'result'][u'players']

    def match_heroes(self):
        heroes_list = []
        for i in self.players:
            heroes_list.append(i[u'hero_id'])
        return heroes_list

    def radiant_items(self):
        it_list =[]
        count = 0
        for i in self.players:
            if count < 5:
                for j in range(6):
                    it_list.append(i[u'item_'+str(j)])
            count +=1
        return it_list

    def dire_items(self):
        it_list =[]
        count = 0
        for i in self.players:
            if count > 5:
                for j in range(6):
                    it_list.append(i[u'item_'+str(j)])
            count +=1
        return it_list

    def match_itemes(self):
        itemes_list = self.dire_items()+self.radiant_items()
        return itemes_list

    def dominant2win(self):
        if self.radiant_win:
            if self.radiant_score>self.dire_score:
                return True
            else:
                return False
        else:
            if self.radiant_score>self.dire_score:
                return False
            else:
                return True

# One instance
class tweetinfo():
    def __init__(self,tweets):
        self.heroname = tweets["hero_name"]
        self.content = tweets["tweets"]["statuses"]
        self.count = len(tweets["tweets"]["statuses"])

    def tweets_fav_count(self):
        count = 0
        for i in self.content:
            count += i["favorite_count"]
        return count

    def tweets_retw_count(self):
        retw = 0
        for i in self.content:
            retw += i["retweet_count"]
        return retw

def pretty(obj):
    return json.dumps(obj, sort_keys=True, indent=2)




# Dota2 data collection


# Build a dictionary for all dota2 heroes. We are going to use this dictionary in tweets search later.
def get_hero():
    try:
        hero_file = open("dota_hero.txt",'r')
        dic  = json.loads(hero_file.read())
        hero_file.close()
    except:
        dic = {}
        heroes = game.get_heroes()
        for hero in heroes[u'heroes']:
            if hero[u'id'] not in dic:
                dic[hero[u'id']] = hero[u'localized_name']
        dic["0"] = "NoHero"
        hero_file = open("dota_hero.txt",'w')
        hero_file.write(json.dumps(dic))
        hero_file.close()
    return dic

# Also Build a dictionary for dota2 itemes whose value is more than 2000.
# We define such itemes as core itemes that could have significant influence on one match.
# We can easily do the same thing with itemes_dic in tweets searching. But itemes are not very popular topic for players.
def get_items():
    try:
        item_file = open("dota_item.txt",'r')
        dic  = json.loads(item_file.read())
        item_file.close()
    except:
        dic = {}
        items = game.get_game_items()
        core_list = filter(lambda item: item[u'cost']>2000 , items[u'items'])
        for item in core_list:
            dic[item[u'id']]=item[u'localized_name']
        item_file = open("dota_item.txt",'w')
        item_file.write(json.dumps(dic))
        item_file.close()
    return dic

def get_match():
    #try to load match_cache:
    try:
        dotafile = open("dota.txt", 'r')
        match_cache = pickle.load(dotafile)
        dotafile.close()
    except:
        match_cache = {}
    dota2_url = "https://api.steampowered.com/IDOTA2Match_570/GetMatchDetails/V001/"
    # Be careful when you set this number larger than 1000. The caching file could be big.
    match_number = 500
    change_made = False
    match_id = last_match_id
    for i in range(match_number):
        if match_id in match_cache:
            match_dic[match_id] = match_cache[match_id]
            # print "match retrived"
        else:
            try:
                h = requests.get(dota2_url,params={"key":dota_api,"match_id":match_id})
                match_his = json.loads(h.text)
                if "error" not in  match_his[u'result'].keys():
                    if "radiant_win" in match_his[u'result'].keys():
                        match_cache[match_id] = match_his
                        match_dic[match_id] = match_his
                        change_made=True
                        # print "New match found"
            except:
                # print "gg"
                pass
        match_id +=1
    # if new match record comes in, cache it into the file
    if change_made==True:
        d = open('dota.txt', 'w')
        pickle.dump(match_cache, d)
        d.close()


def get_game_dics():
    for m_id in match_dic:
        # get a dictionary of using frequency of each hero
        for i in matchdetail(match_dic[m_id]).match_heroes():
            if heroes_dic[str(i)] not in heroes_count:
                heroes_count[heroes_dic[str(i)]] = 1
            else:
                heroes_count[heroes_dic[str(i)]] +=1
        for m in heroes_dic:
            if heroes_dic[m] not in heroes_count:
                heroes_count[heroes_dic[m]] = 0

        # get a dictionary of using frequency of each item
        for j in matchdetail(match_dic[m_id]).match_itemes():
            if str(j) in itemes_dic:
                if itemes_dic[str(j)] not in itemes_count:
                    itemes_count[itemes_dic[str(j)]]=1
                else:
                    itemes_count[itemes_dic[str(j)]]+=1

def sort_item(it_dic):
    sort_it = sorted(it_dic, key = lambda i:it_dic[i], reverse=True)
    return sort_it[:10]

def best_itemes():
    item = {}
    for m_id in match_dic:
        if matchdetail(match_dic[m_id]).radiant_win:
            for it in matchdetail(match_dic[m_id]).radiant_items():
                if str(it) in itemes_dic:
                    if itemes_dic[str(it)] not in item:
                        item[itemes_dic[str(it)]] = 1
                    else:
                        item[itemes_dic[str(it)]] += 1
        else:
            for it in matchdetail(match_dic[m_id]).dire_items():
                if str(it) in itemes_dic:
                    if itemes_dic[str(it)] not in item:
                        item[itemes_dic[str(it)]] = 1
                    else:
                        item[itemes_dic[str(it)]] += 1
    bestit = sorted(item, key = lambda x:item[x], reverse=True)
    return bestit[:10]

def worst_itemes():
    item = {}
    for m_id in match_dic:
        if matchdetail(match_dic[m_id]).radiant_win:
            for it in matchdetail(match_dic[m_id]).dire_items():
                if str(it) in itemes_dic:
                    if itemes_dic[str(it)] not in item:
                        item[itemes_dic[str(it)]] = 1
                    else:
                        item[itemes_dic[str(it)]] += 1
        else:
            for it in matchdetail(match_dic[m_id]).radiant_items():
                if str(it) in itemes_dic:
                    if itemes_dic[str(it)] not in item:
                        item[itemes_dic[str(it)]] = 1
                    else:
                        item[itemes_dic[str(it)]] += 1

    worstit = sorted(item, key = lambda x:item[x], reverse=True)
    return worstit[:10]

def dominantwin():
    count = 0
    wins = 0
    for m_id in match_dic:
        count +=1
        if matchdetail(match_dic[m_id]).dominant2win():
            wins +=1
    return float(wins)/float(count)


itemes_dic = {}
match_dic = {}
fail_count = {}
heroes_count = {}
itemes_count = {}
heroes_dic = {}
twitter_heroes_count = {}
twitter_heroes_dic = {}

dota_api = "5893D96762028E80A2BA393B7671E06C"
if not dota_api:
    dota_api = raw_input("Please input a valid dota_api")

# There could be thousands of matches at the same time, but please don't worry to much about the timeliness.
# The preference of players is not changing very much
# This is a game on 2016-12-10
last_match_id = 2834644254
if not last_match_id:
    last_match_id=raw_input("Please input the id of a recent match")

# Initialise the dota2api
game=dota2api.Initialise(api_key=dota_api)

heroes_dic = get_hero()
# print pretty(heroes_dic)
itemes_dic = get_items()
get_match()
get_game_dics()
# print pretty(heroes_count)
# print pretty(itemes_count)

sorted_itemes = sort_item(itemes_count)
# print sorted_itemes
best_10_itemes = best_itemes()
# print best_10_itemes
worst_10_itemes = worst_itemes()
# print worst_10_itemes

item_f = open('item_top10.csv','w')
item_f.write("All_top10_items,Winner_top10_items,Loser_top10_items\n")
for c in range(10):
    temp = sorted_itemes[c]+ "," +best_10_itemes[c] + "," + worst_10_itemes[c]+"\n"
    item_f.write(temp)
item_f.close()

print "The possiblity for the leading side to win the game is " + str(dominantwin())


#Twitter Data Collection

# This function is from sample_twitter.py in the textbook
def get_tokens():
    oauth = requests_oauthlib.OAuth1Session(client_key, client_secret=client_secret)
    request_token_url = 'https://api.twitter.com/oauth/request_token'
    fetch_response = oauth.fetch_request_token(request_token_url)
    resource_owner_key = fetch_response.get('oauth_token')
    resource_owner_secret = fetch_response.get('oauth_token_secret')
    base_authorization_url = 'https://api.twitter.com/oauth/authorize'
    authorization_url = oauth.authorization_url(base_authorization_url)

    webbrowser.open(authorization_url)
    verifier = raw_input('Please input the verifier>>> ')
    oauth = requests_oauthlib.OAuth1Session(client_key,
                              client_secret=client_secret,
                              resource_owner_key=resource_owner_key,
                              resource_owner_secret=resource_owner_secret,
                              verifier=verifier)

    access_token_url = 'https://api.twitter.com/oauth/access_token'
    oauth_tokens = oauth.fetch_access_token(access_token_url)

    resource_owner_key = oauth_tokens.get('oauth_token')
    resource_owner_secret = oauth_tokens.get('oauth_token_secret')

    return (client_key, client_secret, resource_owner_key, resource_owner_secret, verifier)

# Make sure the user choose between using the cached data or not.
# If using cached data, it won't make any new request.
def get_tweets():
    temp_dic = {}
    input_flag = True # True
    while (input_flag):
        use_caching = raw_input("Would you like to use twitter caching files? Yes:'y' No:'n'")
        if use_caching == "n":
            try:
                f = open("creds.txt", 'r')
                (client_key, client_secret, resource_owner_key, resource_owner_secret, verifier) = json.loads(f.read())
                f.close()
            except:
                tokens = get_tokens()
                f = open("creds.txt", 'w')
                f.write(json.dumps(tokens))
                f.close()
                (client_key, client_secret, resource_owner_key, resource_owner_secret, verifier) = tokens
            oauth = requests_oauthlib.OAuth1Session(client_key,
                                    client_secret=client_secret,
                                    resource_owner_key=resource_owner_key,
                                    resource_owner_secret=resource_owner_secret)
            for hero in heroes_dic:
                temp_dic[heroes_dic[hero]] = {}
                flag = True
                while (flag):
                    if temp_dic[heroes_dic[hero]] =={}:
                        r = oauth.get("https://api.twitter.com/1.1/search/tweets.json", params = {'q': 'dota 2 '+str(heroes_dic[hero]), 'count' : 100})
                        res=r.json()
                        temp_dic[heroes_dic[hero]]["hero_name"] = heroes_dic[hero]
                        temp_dic[heroes_dic[hero]]["tweets"] = res
                    else:
                        max_id = int(min_id)-1
                        r = oauth.get("https://api.twitter.com/1.1/search/tweets.json", params = {'q': 'dota 2 '+str(heroes_dic[hero]), 'count' : 100,'max_id':max_id})
                        res = r.json()
                        temp_dic[heroes_dic[hero]]["tweets"]["statuses"] += res["statuses"]

                    for i in res["statuses"]:
                        min_id = i["id_str"]
                    if len(res["statuses"])<100:
                        flag = False
            t = open('twitter.txt', 'w')
            t.write(json.dumps(temp_dic))
            t.close()
            input_flag = False
            return temp_dic

        elif use_caching=="y":
            twitterref = open('twitter.txt','r')
            twitterstr = twitterref.read()
            temp_dic = json.loads(twitterstr)
            input_flag = False
            return temp_dic
        else:
            pass

def get_tweet_count():
    for hero in twitter_heroes_dic:
        twitter_heroes_count[hero] = tweetinfo(twitter_heroes_dic[hero]).count


def get_tweet_fav():
    fav ={}
    for hero in twitter_heroes_dic:
        fav[hero] = tweetinfo(twitter_heroes_dic[hero]).tweets_fav_count()
    return fav

def get_tweet_retw():
    retweet ={}
    for hero in twitter_heroes_dic:
        retweet[hero] = tweetinfo(twitter_heroes_dic[hero]).tweets_retw_count()
    return retweet

client_key = "BNcXVYHOEFrDLdStiAi3PAqrg"
client_secret = "VcSbTIeaxRJkJ4B26lElJkI5jPyKXnfYe7ivItUT1otAUzE3nN"


if not client_secret or not client_key:
    client_secret = raw_input("Please input your client secret")
    client_key = raw_input("Please input your client key")

twitter_heroes_dic=get_tweets()
# print len(twitter_heroes_dic)
get_tweet_count()
# print pretty(twitter_heroes_count)
twitter_heroes_fav = get_tweet_fav()
# print pretty(twitter_heroes_fav)
twitter_heroes_retweet = get_tweet_retw()
# print pretty(twitter_heroes_retweet)

# print pretty(heroes_dic)
# print pretty(heroes_count)
# print pretty(twitter_heroes_count)
# print pretty(twitter_heroes_fav)
# print pretty(twitter_heroes_retweet)
pop = open("pop.csv","w")
pop.write("Hero Name, Appearances, Tweets, Favorited, Retweet\n")
for h in heroes_dic:
    if h == "0":
        continue
    temp = heroes_dic[h] + "," + str(heroes_count[heroes_dic[h]])+ "," + str(twitter_heroes_count[heroes_dic[h]])+ "," + str(twitter_heroes_fav[heroes_dic[h]]) + "," + str(twitter_heroes_retweet[heroes_dic[h]]) + "\n"
    pop.write(temp)
pop.close()

##### TESTS BELOW, DO NOT CHANGE #########
class Hero(unittest.TestCase):
    def test_1(self):
        self.assertEqual(len(heroes_dic),113,"There is not 112 heroes and one for empty.")
    def test_2(self):
        self.assertEqual(heroes_dic["1"],"Anti-Mage","Heroes are not correctly indexed.")

class Item(unittest.TestCase):
    def test_1(self):
        self.assertEqual(type(itemes_dic),type({}),"testing the type of itemes_dic.")
    def test_2(self):
        self.assertEqual(itemes_dic["1"],"Blink Dagger","Items are not correctly indexed.")

class Match(unittest.TestCase):
    def test_1(self):
        self.assertEqual(type(match_dic),type({}),"testing the type of match_dic.")
    def test_2(self):
        self.assertEqual(type(match_dic.keys()[0]),type(1),"Items are not correctly indexed.")

class Herocount(unittest.TestCase):
    def test_1(self):
        self.assertEqual(type(heroes_count),type({}),"testing the type of heroes_count.")

class Itemcount(unittest.TestCase):
    def test_1(self):
        self.assertEqual(type(itemes_count),type({}),"testing the type of itemes_count.")

class Twitter(unittest.TestCase):
    def test_1(self):
        self.assertEqual(type(twitter_heroes_dic),type({}),"testing the type of twitter_heroes_dic.")
    def test_2(self):
        self.assertEqual(type(twitter_heroes_dic[u"Razor"]),type({}),"The next layer of the dictionary is not correctly indexed.")

class Retweet(unittest.TestCase):
    def test_1(self):
        self.assertEqual(len(twitter_heroes_retweet),112,"Not all heroes tweets are collected")

class Fav(unittest.TestCase):
    def test_1(self):
        self.assertEqual(len(twitter_heroes_fav),112,"Not all heroes tweets are collected")

unittest.main(verbosity=2)
