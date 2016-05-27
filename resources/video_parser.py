from __future__ import unicode_literals

import json

from resources.utility import generic_utility
    
def parse_list_to_string(dict, key):
    list = parse_list(dict, key)
    string = " / ".join(list)
    return string
    
def parse_rating(jsn):
    userRating = jsn.get('userRating', {})
    average = userRating.get('average', 0)
    return average * 2

def get_mpaa(jsn):
    maturity = jsn.get('maturity', {})
    rating = maturity.get('rating', {})
    value = rating.get('value')
    if(generic_utility.get_boolean('filter_age')):
        if not value or value not in ('0', '6', '12', '16', '18'):
            value=generic_utility.get_setting('fsk_default')
    return value

def extract_thumb_url(jsn):
    boxarts = jsn.get('boxarts', {})
    res = boxarts.get('_665x375', boxarts.get('_342x192', {}))
    jpg = res.get('jpg',{})
    url = jpg.get('url', generic_utility.addon_fanart())
    return url
    
def parse_video(jsn, video_id):
    details = jsn.get('details', {})
    summary = jsn.get('summary', {})
    type = summary.get('type')
    
    movie_metadata = {
        'title': jsn.get('title', ''),
        'video_id': video_id,
        'thumb_url': extract_thumb_url(jsn),
        'type': type,
        'description': details.get('synopsis', ''),
        'duration': jsn.get('runtime', 0),
        'year': jsn.get('releaseYear', 1900),
        'mpaa': get_mpaa(jsn),
        'director': parse_list_to_string(details, 'director'),
        'genre': parse_list_to_string(details, 'genre'),
        'rating': parse_rating(jsn),
        'playcount': jsn.get('watched', False),
        'actors': parse_list(details, 'actors'),
        'date_watched': jsn.get('dateStr'),
        'hd': jsn.get('hd', False)
        }
    if type == "episode":
        movie_metadata['episode'] = summary.get('episode')
        movie_metadata['season'] = summary.get('season')
        movie_metadata["series_title"] = jsn.get('seriesTitle')
        movie_metadata["series_id"] = jsn.get('topNodeId')
    
    return movie_metadata
    
    
def parse_list(dict, key):
    list = dict.get(key, [])
    names = []
    for item in list:
        name = item.get('name')
        if key == 'genres' and name != 'Series':
            names.append(name)
    return names
