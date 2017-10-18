import json
import logging
import re
import requests
import time

headers = {'X-Auth-Token': 'a076b21e36044e88830990b9ffe2bb04', 'X-Response-Control': 'minified'}
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_competitions():
    try:
        competitions = get_or_wait('http://api.football-data.org/v1/competitions')
        logging.debug(competitions)
    except:
        logger.error('get_competitions failed')
        raise

    return competitions


def get_competition_ids():
    return [competition['league'] for competition in get_competitions()]


def get_standing(competition_id):
    league_table = get_league_table(competition_id)

    standing = {item['teamId']: item['rank'] for item in
                league_table['standing']} if 'standing' in league_table else None

    logging.debug('standing: ' + json.dumps(standing))
    return standing


def get_league_table(competition_id):
    try:
        league_table = get_or_wait('http://api.football-data.org/v1/competitions/{}/leagueTable'.format(competition_id))
        logging.debug('league_table: ' + json.dumps(league_table))
    except:
        logger.error('get_league_table for competition {} failed'.format(competition_id))
        raise

    return league_table


def get_next_week_matches(competition_id):
    fixtures = get_competition_fixtures(competition_id)
    future_matches = [match for match in fixtures if match['status'] not in ['FINISHED', 'CANCELED']]

    current_week = future_matches[0]['matchday'] if future_matches else None

    next_week_matches = [match for match in future_matches if match['matchday'] == current_week]

    logging.debug('next_week_matches: ' + json.dumps(next_week_matches))
    return next_week_matches


def get_competition_fixtures(competition_id):
    try:
        fixtures = get_or_wait('http://api.football-data.org/v1/competitions/{}/fixtures'.format(competition_id))
        fixtures = fixtures['fixtures'] if 'fixtures' in fixtures else []
        logging.debug('fixtures: ' + json.dumps(fixtures))
    except:
        logger.error('get_competition_fixtures for competition {} failed'.format(competition_id))
        raise

    return fixtures


def get_team_fixtures(team_id):
    try:
        fixtures = get_or_wait('http://api.football-data.org/v1/teams/{}/fixtures'.format(team_id))
        fixtures = fixtures['fixtures'] if fixtures else []
        logging.debug('fixtures: ' + json.dumps(fixtures))
    except:
        logger.error('get_team_fixtures for team {} failed'.format(team_id))
        raise

    return fixtures


def get_or_wait(url):
    do_request = True
    while do_request:
        response = requests.get(url, headers=headers)
        json_response = json.loads(response.content.decode('utf-8'))

        do_request = False
        if 'error' in json_response:
            logger.debug(json_response)

            sleep_time_in_sec_group = re.search('You reached your request limit. Wait (.+)? seconds.',
                                                json_response['error'])
            if sleep_time_in_sec_group:
                sleep_time_in_sec = int(sleep_time_in_sec_group.group(1)) if sleep_time_in_sec_group else 0
                logger.debug('Reached request limit. Sleeping for {} seconds'.format(sleep_time_in_sec))
                time.sleep(sleep_time_in_sec)
                do_request = True

    return json_response
