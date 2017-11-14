import logging
from math import ceil

from matchfinder.filter.domain.competition import Competition
from matchfinder.footballapi import footballapi

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def before_or_equal(team, standing, position):
    return standing[team] <= position


def after_or_equal(team, standing, position):
    return standing[team] >= position


def get_matches(competition, filter):
    selected_matches = []
    standing = footballapi.get_standing(competition['id'])

    if standing:
        number_of_teams = len(standing)
        group_size = ceil(number_of_teams * (filter['percent'] / 100))

        matches = footballapi.get_next_week_matches(competition['id'])

        selected_matches = [match for match in matches
                            if (
                                before_or_equal(match['homeTeamId'], standing, group_size)
                                and after_or_equal(match['awayTeamId'], standing,
                                                   number_of_teams - group_size + 1))
                            or (
                                before_or_equal(match['awayTeamId'], standing, group_size)
                                and after_or_equal(match['homeTeamId'], standing,
                                                   number_of_teams - group_size + 1))]

    return Competition(competition['caption'],
                       [Match(match['date'], 
				Team(match['homeTeamName'], standing[match['homeTeamId']], get_team_crest_url(match['homeTeamId'])),
				Team(match['awayTeamName'], standing[match['awayTeamId']], get_team_crest_url(match['awayTeamId'])))
                        for match in selected_matches])

def get_team_crest_url(teamId):
    team = footballapi.get_team(teamId)
    return team['crestUrl'] if 'crestUrl' in team else None

class Match:
    def __init__(self, datetime, homeTeam, awayTeam):
        self.datetime = datetime
        self.homeTeam = homeTeam
        self.awayTeam = awayTeam

    def __str__(self):
        return '{} {} - {}'.format(self.datetime, self.homeTeam, self.awayTeam)

class Team:
    def __init__(self, name, standing, crestUrl):
        self.name = name
        self.standing = standing
        self.crestUrl = crestUrl

    def __str__(self):
        return '{}({})'.format(self.name, self.standing)

