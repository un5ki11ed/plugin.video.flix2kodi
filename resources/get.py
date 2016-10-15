from __future__ import unicode_literals

import json
import time
import requests
import collections

from resources.path_evaluator import path, from_to, req_path, filter_empty, deref

test = False
try:
    import xbmc
    import xbmcvfs
    import xbmcgui
except Exception:
    test = True

from resources import connect, video_parser
from resources.utility import generic_utility
if generic_utility.android():
    from resources.android import ordered_dict_backport

video_infos1 = '["availability","bookmarkPosition","details","episodeCount","maturity",' \
               '"queue","releaseYear","requestId","runtime","seasonCount","summary","title","userRating","watched","hd"]'
video_infos2 = '"current",["summary","runtime","bookmarkPosition","creditsOffset","title"]'
video_infos3 = '"seasonList","current",["showMemberType","summary"]'
video_infos4 = '"boxarts",["_665x375","_342x192"],"jpg"'


def viewing_activity_matches(video_type):
    content = viewing_activity_info()
    matches = json.loads(content)['viewedItems']
    
    if generic_utility.android():
        metadatas = ordered_dict_backport.OrderedDict()
    else:
        metadatas = collections.OrderedDict()
    
    videos_str = ''
    for match in matches:
        if 'seriesTitle' in match:
            metadata_type = 'show'
            seriesTitle = match['seriesTitle']
        else:
            metadata_type = 'movie'
            seriesTitle = ""

        video_id = unicode(match['movieID'])
        if video_type == metadata_type:
            metadatas[video_id] = {'topNodeId': match['topNodeId'], 'seriesTitle': seriesTitle, 'dateStr': match['dateStr']}
            videos_str += video_id + ','

    videos_str = videos_str[:-1]
    path1 = path('"videos"', '[' + videos_str + ']', video_infos1)
    path2 = path('"videos"', '[' + videos_str + ']', video_infos2)
    path3 = path('"videos"', '[' + videos_str + ']', video_infos3)
    path4 = path('"videos"', '[' + videos_str + ']', video_infos4)
    ret = req_path(path1, path2, path3, path4)
    filter_empty(ret)
    videos = ret.get('videos')
    rets = []

    for video_id in metadatas:
        vjsn = videos[video_id]
        vjsn["topNodeId"] = metadatas[video_id]["topNodeId"]
        vjsn["seriesTitle"] = metadatas[video_id]["seriesTitle"]
        vjsn["dateStr"] = metadatas[video_id]["dateStr"]
        parsed = video_parser.parse_video(vjsn, video_id)
        if is_age_appropriate(parsed):
            rets.append(parsed)

    return rets

def videos_in_list(list_to_browse, page):
    items_per_page = int(generic_utility.get_setting('items_per_page'))
    off_from = page * items_per_page
    off_to = off_from + items_per_page - 2

    path1 = path('"lists"', '"' + list_to_browse + '"', from_to(off_from, off_to), video_infos1)
    path2 = path('"lists"', '"' + list_to_browse + '"', from_to(off_from, off_to), video_infos2)
    path3 = path('"lists"', '"' + list_to_browse + '"', from_to(off_from, off_to), video_infos3)
    path4 = path('"lists"', '"' + list_to_browse + '"', from_to(off_from, off_to), video_infos4)
    ret = req_path(path1, path2, path3, path4)
    filter_empty(ret)
    lists = ret.get('lists')
    list = lists.get(list_to_browse)
    rets = []
    for ref in list:
        video_id, vjsn = deref(list[ref], ret)
        parsed = video_parser.parse_video(vjsn, video_id)
        if is_age_appropriate(parsed):
            rets.append(parsed)
    return rets

def similars(video_id, page):
	items_per_page = int(generic_utility.get_setting('items_per_page'))
	off_from = page * items_per_page
	off_to = off_from + items_per_page - 2
	s1 = '["availability","bookmarkPosition","creditsOffset","current","details","episodeCount","hd","maturity","queue","releaseYear","requestId","runtime",'\
		'"seasonCount","seasonList","showMemberType","summary","title","userRating","watched"]'
	s2 = '"boxarts",["_665x375","_342x192"],"jpg"'
	p1 = path('"videos"', '"' + video_id + '"', '"similars"', from_to(off_from, off_to), s1)
	p2 = path('"videos"', '"' + video_id + '"', '"similars"', from_to(off_from, off_to), s2)
	ret = req_path(p1, p2)
	filter_empty(ret)
	vids = ret.get('videos')
	rets = []
	for vid in vids:
		parsed = video_parser.parse_video(vids[vid], vid)
		if is_age_appropriate(parsed):
			rets.append(parsed)
	return rets
	

def videos_in_genre(genre_to_browse, page):
    items_per_page = int(generic_utility.get_setting('items_per_page'))
    off_from = page * items_per_page
    off_to = off_from + items_per_page - 2
    path1 = path('"genres"', '"' + genre_to_browse + '"', '"su"', from_to(off_from, off_to), video_infos1)
    path2 = path('"genres"', '"' + genre_to_browse + '"', '"su"', from_to(off_from, off_to), video_infos2)
    path3 = path('"genres"', '"' + genre_to_browse + '"', '"su"', from_to(off_from, off_to), video_infos3)
    path4 = path('"genres"', '"' + genre_to_browse + '"', '"su"', from_to(off_from, off_to), video_infos4)
    ret = req_path(path1, path2, path3, path4)
    filter_empty(ret)
    gnrs = ret.get('genres')
    gnre = gnrs.get(genre_to_browse)
    sus = gnre.get('su')
    rets = []
    for ref in sus:
        video_id, vjsn = deref(sus[ref], ret)
        parsed = video_parser.parse_video(vjsn, video_id)
        if is_age_appropriate(parsed):
            rets.append(parsed)
    return rets

def videos_in_search(search_str):
    path1 = path('"search"', '"' + search_str + '"', from_to(0,99), video_infos1)
    path2 = path('"search"', '"' + search_str + '"', from_to(0,99), video_infos2)
    path3 = path('"search"', '"' + search_str + '"', from_to(0,99), video_infos3)
    path4 = path('"search"', '"' + search_str + '"', from_to(0,99), video_infos4)
    ret = req_path(path1, path2, path3, path4)
    filter_empty(ret)
    search = ret.get('search')
    search_node = search.get(search_str)

    rets = []
    for video_ref in search_node:
        video_id, vjsn = deref(search_node[video_ref], ret)
        parsed = video_parser.parse_video(vjsn, video_id)
        if is_age_appropriate(parsed):
            rets.append(parsed)
    return rets

def get_viewing_activity_title(item):
    date = item['dateStr']
    try:
        series_id = item['series']
        series_title = item['seriesTitle']
        title = item['title']
        if series_title:
            title = series_title + ' ' + title
    except Exception:
        title = item['title']
    title = date + ' - ' + title
    return title

def seasons_data(series_id):
    seasons = []
    content = series_info(series_id)
    tvshow = json.loads(content)['video']
    tvshowyear = None
    if tvshow.get("boxart"):
        seriesthumb = tvshow.get("boxart")[0].get("url")
    else: seriesthumb = ""
    
    for item in tvshow.get('seasons'):
        #get playcount from episodes
        watched_episodes = 0
        for eps in item['episodes']:
            duration = eps['runtime']
            offset = eps['bookmark']['offset']
            if (duration > 0 and float(offset) / float(duration)) >= 0.9:
                watched_episodes += 1
        total_episodes = len(item['episodes'])
        unwatched_episodes = total_episodes - watched_episodes
        if watched_episodes == total_episodes: playcount = 1
        else: playcount = 0
        season = {
            "series_id": series_id, 
            "total_episodes":total_episodes,
            "unwatched_episodes":unwatched_episodes,
            "watched_episodes":watched_episodes,
            "season":item['seq'], 
            "seriesthumb":seriesthumb, 
            "playcount":playcount, 
            "year":item['year'], 
            "tvshowtitle":tvshow.get('title'),
            "description":tvshow.get('synopsis'),
            "tvshowyear": tvshowyear,
            "tvshowgenre": "Series",
            "name": xbmc.getLocalizedString(20358) %item['seq']
        }
        seasons.append(season)
        
    return seasons

def season_title(series_id, seq):
    title = None
    datas = seasons_data(series_id)
    for data in datas:
        if data[1] == seq:
            title = data[0]
            break;
    return title

def series_playcounts(series_id):
    watched_episodes = 0
    total_episodes = 0
    content = series_info(series_id)
    content = json.loads(content)['video']
    for season in content["seasons"]:
        for eps in season['episodes']:
            total_episodes += 1
            duration = eps['runtime']
            offset = eps['bookmark']['offset']
            if (duration > 0 and float(offset) / float(duration)) >= 0.9:
                watched_episodes += 1
    unwatched_episodes = total_episodes - watched_episodes
    if watched_episodes == total_episodes: playcount = 1
    else: playcount = 0
    return playcount, total_episodes, watched_episodes, unwatched_episodes
        
def episodes_data(season, series_id):
    episodes = []
    content = series_info(series_id)
    tvshow = json.loads(content)['video']
    seasons = tvshow.get('seasons')
    tvshowyear = None
    if tvshow.get("boxart"):
        seriesthumb = tvshow.get("boxart")[0].get("url")
    else: seriesthumb = ""
    
    for item in seasons:
        episode_season = unicode(item['seq'])
        if not tvshowyear: tvshowyear = item.get("year")
        if episode_season == season:
            for item in item['episodes']:
                playcount = 0
                episode_id = item['episodeId']
                episode_nr = item['seq']
                episode_title = item['title']
                duration = item['runtime']
                offset = item['bookmark']['offset']
                if (duration > 0 and float(offset) / float(duration)) >= 0.9:
                    playcount = 1
                description = item['synopsis']
                try:
                    thumb = item['stills'][0]['url']
                except:
                    thumb = generic_utility.addon_fanart()
                episode = {
                    "series_id": series_id, 
                    "episode_id":episode_id, 
                    "episode_title":episode_title, 
                    "description":description, 
                    "episode_nr":int(episode_nr), 
                    "season":int(season), 
                    "duration":duration, 
                    "thumb":thumb,
                    "seriesthumb":seriesthumb,
                    "hd":item.get("hd",False), 
                    "playcount":playcount, 
                    "tvshowtitle":tvshow.get('title'),
                    "tvshowyear": tvshowyear,
                    "tvshowgenre": "Series"
                }
                episodes.append(episode)
    return episodes

def extended_artwork(title,year,type,id):
    result = {}
    if not type in ["movie","show"]:
        return {}
    
    #gets extended metadata and artwork from the skinhelper service json interface
    if xbmc.getCondVisibility("System.HasAddon(script.skin.helper.service)"):
        #use win properties as cache
        try:
            win = xbmcgui.Window(10000)
            cache = win.getProperty(id)
            if cache: 
                result = eval(cache)
            else:
                url = 'http://localhost:52307/getartwork&year=%s&title=%s&type=%s' %(year,title,type)
                res = requests.get(url)
                result = json.loads(res.content.decode('utf-8','replace'))
                win.setProperty(id,repr(result))
        except: generic_utility.log('Error while requesting extended artwork !')
            
    return result

def genre_data(video_type):
    match = []

    content = genre_info(video_type)

    matches = json.loads(content)['value']['genres']
    for item in matches:
        try:
            match.append((unicode(matches[item]['id']), matches[item]['menuName']))
        except Exception:
            try:
                match.append((unicode(matches[item]['summary']['id']), matches[item]['summary']['menuName']))
            except Exception:
                pass
    return match


def series_info(series_id):
    content = ''
    cache_file = xbmc.translatePath(generic_utility.cache_dir() + series_id + '_episodes.cache')
    if xbmcvfs.exists(cache_file) and (time.time() - xbmcvfs.Stat(cache_file).st_mtime() < 60 * 5):
        file_handler = xbmcvfs.File(cache_file, 'rb')
        content = generic_utility.decode(file_handler.read())
        file_handler.close()
    if not content:
        url = generic_utility.series_url % (generic_utility.api_url, generic_utility.endpoints()['/metadata'], series_id)
        content = connect.load_netflix_site(url)
        file_handler = xbmcvfs.File(cache_file, 'wb')
        file_handler.write(generic_utility.encode(content))
        file_handler.close()
    return content

def genre_info(video_type):
    post_data = ''
    if video_type == 'show':
        post_data = generic_utility.series_genre % generic_utility.get_setting('authorization_url')
    elif video_type == 'movie':
        post_data = generic_utility.movie_genre % generic_utility.get_setting('authorization_url')
    else:
        pass
    content = connect.load_netflix_site(generic_utility.evaluator(), post=post_data)
    return content


def viewing_activity_info():
    content = connect.load_netflix_site(generic_utility.activity_url % (generic_utility.api_url, generic_utility.endpoints()['/viewingactivity'],
                                                                        generic_utility.get_setting(
                                                                                'authorization_url')))
    return content


def video_playback_info(video_datas):
    ids_str = ''
    for video_data in video_datas:
        ids_str += '"'+video_data+'",'
    ids_str = ids_str[:-1]
    post_data = generic_utility.video_playback_info % (ids_str, generic_utility.get_setting('authorization_url'))
    content = connect.load_netflix_site(generic_utility.evaluator(), post=post_data)
    return content


def track_id_list(list):
    jsn = req_path(path('"lists"', '"%s"' % list, '"trackIds"'))
    lsts = jsn.get('lists')
    lst = lsts.get(list)
    track_ids = lst.get('trackIds')
    track_id = track_ids.get('trackId')
    return track_id

def is_age_appropriate(item):
    if generic_utility.get_boolean('filter_age'):
        age = eval(generic_utility.get_setting('age'))
        rating = eval(item.get('mpaa'))
        if rating > age:
            return False
        else:
            return True
    else:
        return True
