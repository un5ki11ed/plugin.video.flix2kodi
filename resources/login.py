from __future__ import unicode_literals

import json
import re

test = False
try:
    import xbmc
    import xbmcgui
except Exception:
    test = True

import connect
import profiles
from resources.utility import generic_utility

def login():
    if not test:
        login_progress = xbmcgui.DialogProgress()
        login_progress.create('Netflix', generic_utility.get_string(30200) + '...')
        generic_utility.progress_window(login_progress, 25, generic_utility.get_string(30201))
    content = connect.load_netflix_site(generic_utility.main_url + 'Login', new_session=True, login_process=True)
    if 'Sorry, Netflix ' not in content:

        match = re.compile('locale: "(.+?)"', re.DOTALL|re.UNICODE).findall(content)
        locale = None
        if(len(match)) == 0:
            match = re.compile('"pageName":"login","locale":"(.+?)"', re.DOTALL|re.UNICODE).findall(content)
            if(len(match)) == 0:
                generic_utility.error('Cannot find locale on page. content: '+content)
                login_url = 'Login'
            else:
                locale = match[0]
                login_url = 'Login?locale=' + locale
        else:
            locale = match[0]
            login_url = 'Login?locale=' + locale
        generic_utility.set_setting('language', locale)

        post_data = {
                     'authURL': generic_utility.get_setting('authorization_url'),
                     'email': generic_utility.get_setting('username'),
                     'password':  generic_utility.get_setting('password'), 
                     'rememberMe': 'true',
                     'flow': 'websiteSignUp',
                     'mode': 'loginPassword',
                     'action': 'loginAction',
                     'withFields': 'email,password,rememberMe,nextPage',
                     'nextPage': ''}

        if not test:
            generic_utility.progress_window(login_progress, 50, generic_utility.get_string(30202))

        content = connect.load_netflix_site(
            generic_utility.main_url + login_url,
            post=post_data, login_process=True)

        if 'id="page-LOGIN"' in content:
            if not test:
                generic_utility.notification(generic_utility.get_string(30303))
            return False

        parse_data_set_cookies(content)

        if not test:
            generic_utility.progress_window(login_progress, 75, generic_utility.get_string(30203))

        profile_selection()

        if login_progress:
            if not test:
                if not generic_utility.progress_window(login_progress, 100, generic_utility.get_string(30204)):
                    return False
                xbmc.sleep(500)
                login_progress.close()
        return True
    else:
        if not test:
            generic_utility.notification(generic_utility.get_string(30300))
            if login_progress:
                login_progress.close()
        return False


def parse_data_set_cookies(content):
    parse_endpoints(content)
    connect.set_chrome_netflix_cookies()




def parse_endpoints(content):
    match = re.compile('"endpointIdentifiers":({.+?}),', re.UNICODE).findall(content)
    if len(match) > 0:
        epstr = match[0]
        if epstr.endswith('}}'):
            epstr = epstr[:-1]

        epstr = generic_utility.replace_netfix_secret_code(epstr)

        generic_utility.set_setting('endpoints', epstr)
    else:
        generic_utility.error('Cannot find api endpoints! Source: ' + content)


def choose_profile():
    profiles.choose()
    profiles.update_displayed()


def profile_selection():

    if generic_utility.get_setting('single_profile') == 'false':
        if not generic_utility.get_setting('selected_profile') or generic_utility.get_setting('show_profiles') == 'true':
            profiles.choose()
        else:
            profiles.load()

    profiles.update_displayed()


class CannotRefreshDataException(Exception):
    pass


def refresh_data():
    content = connect.load_netflix_site('https://www.netflix.com/browse')
    parse_endpoints(content)

    profl = generic_utility.get_setting('selected_profile')
    if not profl:
        if login():
            profl = generic_utility.get_setting('selected_profile')
    if not profl:
        raise CannotRefreshDataException

    try:
        profiles.switch_profile(profl)
    except ValueError as vex:
        raise CannotRefreshDataException(vex)

    content = connect.load_netflix_site(generic_utility.main_url)

    parse_data_set_cookies(content)
