from matchfinder.filter.strategy import topbottom
from matchfinder.filter.strategy import underover

filter_types = {
    'topbottom': topbottom,
    'underover': underover
}


def get_matches(competition, filter):
    return filter_types[filter['type']].get_matches(competition, filter)
