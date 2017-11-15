import logging
from functools import reduce

from matchfinder.filter.domain.competition import Competition
from matchfinder.footballapi import footballapi

logger = logging.getLogger()
logger.setLevel(logging.INFO)

filter = {}


def combine_stats(home_team_stats, away_team_stats):
    return {
        'under_or_equal_chance':
            (home_team_stats['under_or_equal_chance'] * away_team_stats['under_or_equal_chance']) / 100,
        'over_or_equal_chance':
            (home_team_stats['over_or_equal_chance'] * away_team_stats['over_or_equal_chance']) / 100
    }


def has_probability(team_stats, expected_chance):
    return team_stats['under_or_equal_chance'] >= expected_chance \
           or team_stats['over_or_equal_chance'] >= expected_chance


def get_matches(competition, search_filter):
    matches = footballapi.get_next_week_matches(competition['id'])
    filter['halftime'] = search_filter['halffulltime'] == 'halftime'
    filter['homeaway'] = search_filter['homeaway'] == 'on'
    filter['numberofgoals'] = search_filter['numberofgoals']
    filter['chance'] = search_filter['percent']
    filter['competitionId'] = competition['id']

    selected_match_and_stats = [
        {
            'match': match,
            'stats': combine_stats(
                get_over_under_stats(match['homeTeamId'], filter['numberofgoals'],
                                     {'home': True, 'away': not filter['homeaway']}),
                get_over_under_stats(match['awayTeamId'], filter['numberofgoals'],
                                     {'home': not filter['homeaway'], 'away': True}))
        } for match in matches]

    return Competition(competition['caption'],
                       [Match(match_and_stats['match']['date'],
                              Team(match_and_stats['match']['homeTeamName'],
                                   get_team_crest_url(match_and_stats['match']['homeTeamId'])),
                              Team(match_and_stats['match']['awayTeamName'],
                                   get_team_crest_url(match_and_stats['match']['awayTeamId'])),
                              match_and_stats['stats'])
                        for match_and_stats in selected_match_and_stats
                        if has_probability(match_and_stats['stats'], filter['chance'])])


def get_team_crest_url(team_id):
    team = footballapi.get_team(team_id)
    return team['crestUrl'] if 'crestUrl' in team else None


def get_goal_count(match):
    result = match['result']['halfTime'] if filter['halftime'] and 'halfTime' in match['result'] else match['result']
    return result['goalsHomeTeam'] + result['goalsAwayTeam']


def get_over_under_stats(team_id, number_of_goals, games_filter):
    fixtures = footballapi.get_team_fixtures(team_id)

    finished_games = [match for match in fixtures
                      if match['competitionId'] == filter['competitionId']
                      and match['status'] == 'FINISHED'
                      and ((games_filter['home'] and match['homeTeamId'] == team_id)
                           or (games_filter['away'] and match['awayTeamId'] == team_id))]
    finished_game_count = len(finished_games)

    results = reduce(lambda r1, r2:
                     Results(r1.under_or_equal_count + r2.under_or_equal_count,
                             r1.over_or_equal_count + r2.over_or_equal_count)
                     , [Results(
            1 if get_goal_count(match) <= number_of_goals else 0,
            1 if get_goal_count(match) >= number_of_goals else 0) for match in finished_games])

    return {
        'under_or_equal_chance':
            (results.under_or_equal_count / finished_game_count) * 100 if finished_game_count > 0 else 0,
        'over_or_equal_chance':
            (results.over_or_equal_count / finished_game_count) * 100 if finished_game_count > 0 else 0
    }


class Match:
    def __init__(self, datetime, home_team, away_team, stats):
        self.datetime = datetime
        self.homeTeam = home_team
        self.awayTeam = away_team
        self.stats = stats

    def __str__(self):
        return '{} {} - {} (under_or_equal_chance:{}%, over_or_equal_chance: {}%)' \
            .format(self.datetime, str(self.homeTeam), str(self.awayTeam), self.stats['under_or_equal_chance'],
                    self.stats['over_or_equal_chance'])

    def __iter__(self):
        return iter([('datetime', self.datetime),
                     ('homeTeam', dict(self.homeTeam)),
                     ('awayTeam', dict(self.awayTeam)),
                     ('stats', self.stats)])


class Team:
    def __init__(self, name, crest_url):
        self.name = name
        self.crestUrl = crest_url

    def __str__(self):
        return '{}(crestUrl: {})'.format(self.name, self.crestUrl)

    def __iter__(self):
        return iter([('name', self.name),
                     ('crestUrl', self.crestUrl)])


class Results:
    def __init__(self, under_or_equal_count, over_or_equal_count):
        self.under_or_equal_count = under_or_equal_count
        self.over_or_equal_count = over_or_equal_count
