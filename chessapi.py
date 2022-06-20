# chess.com API -> https://www.chess.com/news/view/published-data-api
# The API has been used to download monthly archives for a user using a Python3 program.
# This program works as of 24/09/2018

# import urllib
import urllib.request
import json
# username = "SirNytram" #change 
# baseUrl = "https://api.chess.com/pub/player/" + username + "/games/"
# archivesUrl = baseUrl + "archives"

#read the archives url and store in a list

def get_game_byindex(user, month_index, game_index):
    game = ''
    archives_url = f'https://api.chess.com/pub/player/{user}/games/archives'
    archives_json =  json.loads(urllib.request.urlopen(archives_url).read())
    month_url = archives_json['archives'][month_index]
    month_json = json.loads(urllib.request.urlopen(month_url).read())
    game = month_json['games'][game_index]
    return game

# print(get_game('SirNytram', 0, 0))

def get_game_bydate(user, year, month, game_index):
    game = ''
    month_url = f'https://api.chess.com/pub/player/{user}/games/{year}/{month}'
    month_json = json.loads(urllib.request.urlopen(month_url).read())
    game = month_json['games'][game_index]
    return game


# games_archives = json.loads(urllib.request.urlopen(archivesUrl).read())
# for month_archive in games_archives['archives']:
#     games_cur_month = json.loads(urllib.request.urlopen(month_archive).read())
#     pass


# archives = f'{f.read()}' #.decode("utf-8")
# archives = archives.replace("{\"archives\":[\"", "\",\"")
# archivesList = archives.split("\",\"" + baseUrl)
# archivesList[len(archivesList)-1] = archivesList[len(archivesList)-1].rstrip("\"]}")

# #download all the archives
# for i in range(len(archivesList)-1):
#     url = baseUrl + archivesList[i+1] + "/pgn"
#     filename = archivesList[i+1].replace("/", "-")
#     urllib.request.urlretrieve(url, "/Users/Magnus/Desktop/My Chess Games/" + filename + ".pgn") #change
#     print(filename + ".pgn has been downloaded.")
# print ("All files have been downloaded.")



# from chessdotcom import get_player_profile

# response = get_player_profile("SirNytram")

# player_name = response.json['player']['name']
# #or
# player_name = response.player.name


# https://api.chess.com/pub/player/sirnytram/games/2022/06
pass