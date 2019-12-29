import requests
import html.parser
from bs4 import BeautifulSoup
import re
from collections import defaultdict


def extract_match_details(href):
    req = requests.get('https://www.fussballdaten.de' + href + 'vergleich/')
    if (req.status_code is not 200):
        raise ConnectionError
    soup = BeautifulSoup(req.text, "lxml")
    stats = soup.select('html body div.wrap div.container div#page-content div#myPjax div.row.padding-cols.row-flex '
                        'div.col-md-8.col-sm-12.col-xs-12 div.box.bs.green-top div.p10.mb0.mt10.pb0 '
                        'div.vergleich-stats div.row.padding-cols div.col-md-4.col-sm-4.col-xs-4.padding-0.fw600')
    goals_home = str.strip(stats[0].contents[2])
    goals_away = str.strip(stats[1].contents[0])
    ylw_cards_home = str.strip(stats[2].contents[2])
    ylw_cards_away = str.strip(stats[3].contents[0])
    rd_cards_home = str(int(stats[4].contents[2]) + int(stats[6].contents[2]))
    rd_cards_away = str(int(stats[5].contents[0]) + int(stats[7].contents[0]))
    # TODO add stats of previous matches
    # Concatenate results and return (grouped by home and away)
    return goals_home + '\t' + ylw_cards_home + '\t' + rd_cards_home, \
           goals_away + '\t' + ylw_cards_away + '\t' + rd_cards_away

def extract_matchday(season,matchday,ranking):
    req = requests.get('https://www.fussballdaten.de/2liga/{}/{}/'.format(str(season),str(matchday)))

    if (req.status_code is not 200):
        raise ConnectionError
    # Xpath for ranking: /html/body/div[1]/div/div[4]/div[3]/div[2]/div/div[1]/div[2]/div[2]/a[1]/span[1]
    # How to find via CSS?
    soup = BeautifulSoup(req.text, "lxml")
    # Select relevant elements: home team, away team, match result
    entries = soup.select(
        'html body div.wrap div.container div#page-content div#spiele.box.bs.green-top div.kategorie-content '
        'div.row div.col-md-8.content-spiele.content-divider div.content-spiele div.spiele-row.detils a')
    # Select ranking statistics of the end of the matchday
    teams_ranked = soup.select('html body div.wrap div.container div#page-content div#spiele.box.bs.green-top '
                               'div.kategorie-content div.row div.col-md-4.content-md-4.hidden-xs div.content-tabelle '
                               'div#w2.grid-view table.table.lh2 tbody tr td.text-left a.ellipsis')
    points_ranked = soup.select('html body div.wrap div.container div#page-content div#spiele.box.bs.green-top '
                                'div.kategorie-content div.row div.col-md-4.content-md-4.hidden-xs div.content-tabelle '
                                'div#w2.grid-view table.table.lh2 tbody tr td.text-right.fw600.green')
    goals_ranked = soup.select('html body div.wrap div.container div#page-content div#spiele.box.bs.green-top '
                               'div.kategorie-content div.row div.col-md-4.content-md-4.hidden-xs div.content-tabelle '
                               'div#w2.grid-view table.table.lh2 tbody tr td.text-center')


    # Iterate through sections which contain information about teams and match results
    # The pattern for each match is 1. home team 2. result 3. guest team
    winner = ''
    for i in range(0,len(entries)):
        heim_name = entries[i].contents[1]
        i += 1
        # Visit match details page with more statistics
        home_comp, away_comp = extract_match_details(entries[i].attrs['href'])
        ergebnis = entries[i].contents[0].contents[0]
        tore_heim = int(ergebnis.split(':')[0])
        tore_gast = int(ergebnis.split(':')[1])
        if tore_heim > tore_gast:
            winner = 'home'
        elif tore_gast > tore_heim:
            winner = 'away'
        else:
            winner = 'draw'
        i += 1
        gast_name = entries[i].contents[1]

        if len(ranking) is 0:
            return '{}\t0\t{}\t0\t{}\t{}\n'.format(heim_name,gast_name,winner,match_comp)

    # Collecting ranked teams at the end of the matchday with points and scored and received goals in a dictionary
    # with team names as keys and points, scored and received as value (list of ints)
    for rank in range(0,17):
        points = int(points_ranked[rank].contents[0])
        scored = int(goals_ranked[rank].contents[0].split(':')[0])
        received = int(goals_ranked[rank].contents[0].split(':')[1])
        team = teams_ranked[rank].contents[1]
        ranking[team] = [points, scored, received]


# Initializing CSV file
# home name | home rank | home points | home scored total | home received total| home comp goals | home yw cards | home rd cards
# away name | away rank ... | home goals | aways goals | result
csv_header = 'h_team\th_rank_prior\ta_team\twinner\t'


ranking = {}
for n_day in range(1,34):
    extract_matchday(2018,n_day,ranking)

