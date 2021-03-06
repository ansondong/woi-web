from app.helpers import get_rdata

import datetime

CORE_DATA = "http://data.war-on-ice.net/nhlscrapr-core.RData"


def get_r_seasons():
    """Gets the season data from CORE_DATA"""
    rdata = get_rdata(CORE_DATA)
    teamgames = {}
    for game in rdata["games"]:
        # Split data up by season
        if game["season"] not in teamgames:
            teamgames[game["season"]] = []
        teamgames[game["season"]].append(game)
    return teamgames


def compiled_teams(season, years):
    """Compile data about teams over the games in the season(s)"""
    teams = {}
    for game in season:
        hometeam = game["hometeam"]
        awayteam = game["awayteam"]
        # If valid game
        if hometeam != "" and awayteam != "":
            # Check to see if these teams exist yet
            if hometeam not in teams:
                teams[hometeam] = {}
            if awayteam not in teams:
                teams[awayteam] = {}
            # Don't count games that haven't happened yet
            if game["status"] != 1 and game["status"] != 4:
                if "Gm" not in teams[hometeam]:
                    teams[hometeam] = prepare_team_comparisons()
                    teams[hometeam]["Team"] = hometeam
                    teams[hometeam]["Season"] = years
                if "Gm" not in teams[awayteam]:
                    teams[awayteam] = prepare_team_comparisons()
                    teams[awayteam]["Team"] = awayteam
                    teams[awayteam]["Season"] = years
                # Collect data
                teams[hometeam]["Gm"] += 1
                teams[awayteam]["Gm"] += 1
                if game["homeafteraway"] == True or game["homeafterhome"] == True:
                    teams[hometeam]["b2b"] += 1
                if game["awayafteraway"] == True or game["awayafterhome"] == True:
                    teams[awayteam]["b2b"] += 1
                teams[hometeam]["GF"] += game["homescore"]
                teams[awayteam]["GF"] += game["awayscore"]
                teams[hometeam]["GA"] += game["awayscore"]
                teams[awayteam]["GA"] += game["homescore"]
    return teams


def get_r_games():
    # Get today's date
    now = datetime.datetime.now()
    now = now.isoformat()
    # Grab the CORE_DATA RData file
    alldata = get_rdata(CORE_DATA)
    # Grab game history
    games = alldata["games"]
    fgames = []
    season = None
    # Grab games from the current season
    for game in multikeysort(games, ["-date", "-gcode"]):
        if len(game["date"]) == 10 and game["date"] <= now:
            if season == None:
                season = game["season"]
            else:
                if season != game["season"]:
                    break
            fgames.append(game)

    return fgames


def multikeysort(items, columns):
    from operator import itemgetter
    comparers = [((itemgetter(col[1:].strip()), -1) if col.startswith('-') else
                  (itemgetter(col.strip()), 1)) for col in columns]
    def comparer(left, right):
        for fn, mult in comparers:
            result = cmp(fn(left), fn(right))
            if result:
                return mult * result
        else:
            return 0
    return sorted(items, cmp=comparer)


def get_r_standings(teamgames, seasons=None):
    # Get overall standings for the season(s) found in seasons
    seasongames = {}
    for season in seasons:
        for team in teamgames[season]:
            hometeam = team["hometeam"]
            awayteam = team["awayteam"]
            if hometeam != "" and awayteam != "":
                if hometeam not in seasongames:
                    seasongames[hometeam] = {}
                if awayteam not in seasongames:
                    seasongames[awayteam] = {}
                if team["status"] != 1 and team["status"] != 4:
                    if "Gm" not in seasongames[hometeam]:
                        seasongames[hometeam] = prepare_team()
                    if "Gm" not in seasongames[awayteam]:
                        seasongames[awayteam] = prepare_team()
                    seasongames[hometeam]["Gm"] += 1
                    seasongames[awayteam]["Gm"] += 1
                    seasongames[hometeam]["GF"] += team["homescore"]
                    seasongames[hometeam]["GA"] += team["awayscore"]
                    seasongames[awayteam]["GF"] += team["awayscore"]
                    seasongames[awayteam]["GA"] += team["homescore"]
                    seasongames[hometeam]["CF"] += team["homecorsi"]
                    seasongames[hometeam]["CA"] += team["awaycorsi"]
                    seasongames[awayteam]["CF"] += team["awaycorsi"]
                    seasongames[hometeam]["CA"] += team["homecorsi"]
                    # Determine winner, if game is still not going on
                    if team["status"] != 2:
                        if team["homescore"] > team["awayscore"]:
                            winner = hometeam
                            loser = awayteam
                        elif team["awayscore"] > team["homescore"]:
                            winner = awayteam
                            loser = hometeam
                        if team["periods"] == 3:
                            seasongames[winner]["RW"] += 1
                            seasongames[loser]["RL"] += 1
                            seasongames[winner]["PNow"] += 2
                            seasongames[winner]["P3"] += 3
                            seasongames[winner]["PTie"] += 2
                            seasongames[winner]["PNL"] += 2
                        elif team["periods"] == 4:
                            seasongames[winner]["OW"] += 1
                            seasongames[loser]["OL"] += 1
                            seasongames[winner]["PNow"] += 2
                            seasongames[loser]["PNow"] += 1
                            seasongames[winner]["P3"] += 2
                            seasongames[loser]["P3"] += 1
                            seasongames[winner]["PTie"] += 2
                            seasongames[loser]["PTie"] += 1
                            seasongames[winner]["PNL"] += 2
                        elif team["periods"] == 5:
                            seasongames[winner]["SW"] += 1
                            seasongames[loser]["SL"] += 1
                            seasongames[winner]["PNow"] += 2
                            seasongames[loser]["PNow"] += 1
                            seasongames[winner]["P3"] += 2
                            seasongames[loser]["P3"] += 1
                            seasongames[winner]["PTie"] += 1
                            seasongames[loser]["PTie"] += 1
                            seasongames[winner]["PNL"] += 2
    return seasongames


def prepare_team_comparisons():
    keys = ["Gm", "b2b", "corsi", "seconds", "GF", "GA"]
    dic = {}
    for key in keys:
        dic[key] = 0
    return dic


def prepare_team():
    keys = ["Gm", "RW", "OW", "SW", "RL", "OL", "SL", "GF", "GA", "CF", "CA", "PNow", "P3", "PTie", "PNL"]
    dic = {}
    for key in keys:
        dic[key] = 0
    return dic
