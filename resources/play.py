from __future__ import unicode_literals

import json
import os
import subprocess
import sys
import time
import traceback

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
from thread import start_new_thread

import get
from resources.utility import generic_utility
from resources import library

plugin_handle = int(sys.argv[1])

BROWSER_CHROME='1'
BROWSER_CHROME_LAUNCHER = '2'
BROWSER_INTERNET_EXPLORER = '3'
BROWSER_EDGE = '4'
BROWSER_SAFARI = '5'
BROWSER_CHROMIUM = '6'
BROWSER_ANDROID = '7'

MAX_LANG = 5
MAX_SUB = 5

def video(video_id, series_id):
    xbmc.Player().stop()
    player = LogiPlayer()
    if player.has_valid_browser():
        player.play(video_id, series_id)
    listitem = xbmcgui.ListItem(path=generic_utility.addon_dir() + '/resources/fakeVid.mp4')
    xbmcplugin.setResolvedUrl(plugin_handle, True, listitem)
    xbmc.PlayList(xbmc.PLAYLIST_VIDEO).clear()
    if player.has_valid_browser():
        player.doModal()
    return None


class LogiPlayer(xbmcgui.Window):
    valid_browser = False
    browser = None
    screensaver = None
    display_off = None
    shutdown_time = None
    screensaver_mode = None
    addon_path = None
    lang_count = 0
    subtitle_count = 0

    def has_valid_browser(self):
        return self.valid_browser

    def play (self, video_id, series_id):
        start_new_thread(self.playInternal, (video_id, series_id,))
        start_new_thread(self.after_chrome_launched, ())

    def playInternal (self, video_id, series_id):
        xbmc.audioSuspend()
        self.disable_screensaver()

        if generic_utility.get_setting('disable_lirc') == 'true':
            xbmc.executebuiltin('LIRC.Stop')

        try:
            self.launch_browser('http://netflix.com/watch/%s' % video_id)
        except:
            generic_utility.log(traceback.format_exc(), xbmc.LOGERROR)
            generic_utility.notification('Error launching browser. See logfile')

        self.enable_screensaver()
        xbmc.audioResume()
        if generic_utility.get_setting('disable_lirc') == 'true':
            xbmc.executebuiltin('LIRC.Start')

        if generic_utility.get_setting('sync_viewstate') == 'true':
            try:
                self.update_playcount(video_id)
            except:
                generic_utility.log(traceback.format_exc(), xbmc.LOGERROR)
                generic_utility.notification('Cannot update playcount. See logfile')
        self.close()


    def update_playcount(self, video_id):
        library.update_playcounts()

    def disable_screensaver(self):
        ret = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Settings.getSettingValue", "params": {"setting":"screensaver.mode" } }')
        jsn = json.loads(ret)
        self.screensaver_mode = jsn['result']['value']

        ret = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Settings.getSettingValue", "params": {"setting":"powermanagement.displaysoff" } }')
        jsn = json.loads(ret)
        self.display_off = jsn['result']['value']

        ret = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Settings.getSettingValue", "params": {"setting":"powermanagement.shutdowntime" } }')
        jsn = json.loads(ret)
        self.shutdown_time = jsn['result']['value']


        xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Settings.SetSettingValue", "params": {"setting": "screensaver.mode", "value": "" } }')
        xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Settings.SetSettingValue", "params": {"setting": "powermanagement.displaysoff", "value": 0 } }')
        xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Settings.SetSettingValue", "params": {"setting": "powermanagement.shutdowntime", "value": 0 } }')


    def enable_screensaver(self):
        xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Settings.SetSettingValue", "params": {"setting":"screensaver.mode", "value": "'+self.screensaver_mode+'" } }')
        xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Settings.SetSettingValue", "params": {"setting":"powermanagement.displaysoff", "value": '+str(self.display_off)+' } }')
        xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Settings.SetSettingValue", "params": {"setting": "powermanagement.shutdowntime", "value": %s } }' % str(self.shutdown_time))


    def after_chrome_launched(self):
        pass


    def onAction(self, action):
        if generic_utility.get_setting('alternate_remote') == 'true':
            #from plugin.video.netflixbmc
            ACTION_SELECT_ITEM = 7
            ACTION_PARENT_DIR = 9
            ACTION_PREVIOUS_MENU = 10
            ACTION_PAUSE = 12
            ACTION_STOP = 13
            ACTION_SHOW_INFO = 11
            ACTION_SHOW_GUI = 18
            ACTION_MOVE_LEFT = 1
            ACTION_MOVE_RIGHT = 2
            ACTION_MOVE_UP = 3
            ACTION_MOVE_DOWN = 4
            ACTION_PLAYER_PLAY = 79
            ACTION_VOLUME_UP = 88
            ACTION_VOLUME_DOWN = 89
            ACTION_MUTE = 91
            ACTION_CONTEXT_MENU = 117
            ACTION_BUILT_IN_FUNCTION = 122
            KEY_BUTTON_BACK = 275

            if generic_utility.windows():
                proc = subprocess.Popen('WMIC PROCESS get Caption', shell=True, stdout=subprocess.PIPE)
                procAll = ""
                for line in proc.stdout:
                    procAll+=line
                if "chrome.exe" in procAll:
                    if action in [ACTION_SHOW_INFO, ACTION_SHOW_GUI, ACTION_STOP, ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, KEY_BUTTON_BACK]:
                        subprocess.Popen('"'+sendKeysPath+'"'+' sendKey=Close', shell=False)
                        self.close()
                    elif action==ACTION_SELECT_ITEM:
                        subprocess.Popen('"'+sendKeysPath+'"'+' sendKey=PlayPause', shell=False)
                    elif action==ACTION_MOVE_LEFT:
                        subprocess.Popen('"'+sendKeysPath+'"'+' sendKey=SeekLeft', shell=False)
                    elif action==ACTION_MOVE_RIGHT:
                        subprocess.Popen('"'+sendKeysPath+'"'+' sendKey=SeekRight', shell=False)
                    elif action==ACTION_MOVE_UP:
                        subprocess.Popen('"'+sendKeysPath+'"'+' sendKey=VolumeUp', shell=False)
                    elif action==ACTION_MOVE_DOWN:
                        subprocess.Popen('"'+sendKeysPath+'"'+' sendKey=VolumeDown', shell=False)
                else:
                    self.close()                
            elif generic_utility.darwin():
                proc = subprocess.Popen('/bin/ps ax', shell=True, stdout=subprocess.PIPE)
                procAll = ""
                for line in proc.stdout:
                    procAll+=line
                if "chrome" in procAll:
                    if action in [ACTION_SHOW_INFO, ACTION_SHOW_GUI, ACTION_STOP, ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, KEY_BUTTON_BACK]:
                        subprocess.Popen('cliclick kd:cmd t:q ku:cmd', shell=True)
                        self.close()
                    elif action==ACTION_SELECT_ITEM:
                        subprocess.Popen('cliclick t:p', shell=True)
                    elif action==ACTION_MOVE_LEFT:
                        subprocess.Popen('cliclick kp:arrow-left', shell=True)
                    elif action==ACTION_MOVE_RIGHT:
                        subprocess.Popen('cliclick kp:arrow-right', shell=True)
                    elif action==ACTION_MOVE_UP:
                        subprocess.Popen('cliclick kp:arrow-up', shell=True)
                    elif action==ACTION_MOVE_DOWN:
                        subprocess.Popen('cliclick kp:arrow-down', shell=True)
                else:
                    self.close()
            else: #linux
                doClose = False
                key=None
                if action in [ACTION_SHOW_GUI, ACTION_STOP, ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, KEY_BUTTON_BACK]:
                    key="control+shift+q"
                    doClose=True
                elif action in [ ACTION_SELECT_ITEM, ACTION_PLAYER_PLAY, ACTION_PAUSE ]:
                    key="space"
                elif action==ACTION_MOVE_LEFT:
                    key="Left"
                elif action==ACTION_MOVE_RIGHT:
                    key="Right"
                elif action==ACTION_SHOW_INFO:
                    key="question"
                elif action==ACTION_VOLUME_UP:
                    key="Up"
                elif action==ACTION_VOLUME_DOWN:
                    key="Down"
                elif action==ACTION_MUTE:
                    key="M"
                elif action==ACTION_CONTEXT_MENU:
                    key="ctrl+alt+shift+d"
                if key is not None:
                    p = subprocess.Popen('xdotool search --onlyvisible --class "google-chrome|Chromium" key %s' % key, shell=True)
                    p.wait()
                    # 0 for success, 127 if xdotool not found in PATH. Return code is 1 if window not found (indicating should close).
                    if not p.returncode in [0,127] or doClose:
                        self.close()

        else:
            generic_utility.debug('caught action: '+str(action.getId()))
            ACTION_NAV_BACK = 92
            ACTION_PREVIOUS_MENU = 10
            ACTION_STOP = 13

            ACTION_SELECT_ITEM = 7
            ACTION_PLAYER_PLAY = 79
            ACTION_PLAYER_PLAYPAUSE = 229
            ACTION_PAUSE = 12

            ACTION_PLAYER_REWIND = 78
            ACTION_MOVE_LEFT = 1
            ACTION_REWIND = 17

            ACTION_PLAYER_FORWARD = 77
            ACTION_MOVE_RIGHT = 2
            ACTION_FORWARD = 16

            ACTION_MOVE_UP = 3
            ACTION_MOVE_DOWN = 4

            ACTION_KEY_1 = 59
            ACTION_KEY_2 = 142
            ACTION_CONTEXT_MENU = 117
            ACTION_SHOW_INFO = 11

            if action.getId() in(ACTION_NAV_BACK, ACTION_PREVIOUS_MENU, ACTION_STOP):
                self.control('close')
            elif action.getId() in(ACTION_SELECT_ITEM, ACTION_PLAYER_PLAY, ACTION_PLAYER_PLAYPAUSE, ACTION_PAUSE):
                self.control('pause')
            elif action.getId() in(ACTION_PLAYER_REWIND, ACTION_MOVE_LEFT, ACTION_REWIND):
                self.control('backward')
            elif action.getId() in(ACTION_PLAYER_FORWARD, ACTION_MOVE_RIGHT, ACTION_FORWARD):
                self.control('forward')
            elif action.getId() == ACTION_MOVE_UP:
                self.control('up')
            elif action.getId() == ACTION_MOVE_DOWN:
                self.control('down')
            elif action.getId() in (ACTION_KEY_1, ACTION_CONTEXT_MENU):
                self.control('toggle_lang'+str(self.lang_count))
                if self.lang_count == MAX_LANG:
                    self.lang_count = 0
                else:
                    self.lang_count += 1

            elif action.getId() in(ACTION_KEY_2, ACTION_SHOW_INFO):
                self.control('toggle_sub'+str(self.subtitle_count))
                if self.subtitle_count == MAX_SUB:
                    self.subtitle_count = 0
                else:
                    self.subtitle_count += 1

            else:
                generic_utility.error('unknown action: ' + str(action.getId()))

    def control(self, key):
        script = self.get_launch_script('keysender')
        if script:
            callcmd = script + ' ' + key
            self.call_script(callcmd)

    def launch_browser_android(self, url):
        xbmc.executebuiltin("StartAndroidActivity(com.android.chrome,android.intent.action.VIEW,,"+url+")")


    def launch_browser(self, url):

        if self.browser == BROWSER_ANDROID:
            self.launch_browser_android(url)
        else:
            self.before_launch()

            if not self.call_custom_script('playback', url):
                script = self.get_launch_script('launcher')

                if script:
                    callstr = script + ' ' + url
                    self.call_script(callstr)
                    generic_utility.debug('browser terminated')
            self.after_launch()

    def before_launch(self):
#        if self.browser == BROWSER_CHROME:
#            connect.refresh_data()

        self.call_custom_script('before_playback')

    def after_launch(self):
        self.call_custom_script('after_playback')
        #refresh listing to update any watched indicators
        xbmc.executebuiltin("Container.Refresh")

    def call_custom_script(self, name, params = ''):
        data_dir = generic_utility.data_dir()
        if not generic_utility.windows():
            bash = 'sh '
            ending = '.sh'
            double_quotes = ''
        else:
            bash = ''
            ending = '.cmd'
            double_quotes = '"'
        custom_script = data_dir + 'custom' + os.sep + name + ending

        if generic_utility.windows():
            custom_script = custom_script.replace('/','\\')

#        generic_utility.log('custom: '+custom_script)
        if os.path.isfile(custom_script):
            generic_utility.debug('calling: '+custom_script)
            if params != '':
                params = ' '+params
            if generic_utility.darwin():
                custom_script = generic_utility.sh_escape(custom_script)
            else:
                custom_script = double_quotes+custom_script+double_quotes

            self.call_script(bash+custom_script+params)
            return True

        return False

    def call_script(self, callstr):
        generic_utility.debug('launching: ' + callstr)
        info = None
        if generic_utility.windows():
            info = subprocess.STARTUPINFO()
            info.dwFlags = subprocess.STARTF_USESHOWWINDOW
            info.wShowWindow = subprocess.SW_HIDE
        process = subprocess.Popen(callstr, startupinfo=info, shell=True)
        process.wait()

    def get_launch_script(self, type):
        path = addon_path + '/resources/scripts/'+type+'/'
        browser_name = None
        double_quotes=''
        bash = ''
        if generic_utility.windows():
            path += 'windows/'
            ending = '.cmd'
            double_quotes = '"'
        elif generic_utility.darwin():
            path += 'darwin/'
            ending = '.sh'
            bash = 'sh '
        else:
            path += 'linux/'
            ending = '.sh'
            bash = 'sh '
        browser_name = self.get_browser_scriptname(browser_name)

        script = path+browser_name+ending

        if generic_utility.windows():
            script = script.replace('/','\\')

        if not os.path.isfile(script):
            generic_utility.error('Script: '+script+' not found!')
            script = ''

        if generic_utility.darwin():
            script = bash + generic_utility.sh_escape(script)
        else:
            script = bash + double_quotes+script+double_quotes

        return script

    def get_browser_scriptname(self, browser_name):
        if self.browser == BROWSER_CHROME:
            browser_name = 'chrome'
        elif self.browser == BROWSER_CHROME_LAUNCHER:
            browser_name = 'chromelauncher'
        elif self.browser == BROWSER_INTERNET_EXPLORER:
            browser_name = 'iexplore'
        elif self.browser == BROWSER_EDGE:
            browser_name = 'edge'
        elif self.browser == BROWSER_SAFARI:
            browser_name = 'safari'
        elif self.browser == BROWSER_CHROMIUM:
            browser_name = 'chromium'
        elif self.browser == BROWSER_ANDROID:
            browser_name = 'android'
        return browser_name

    def read_browser(self):
        self.browser = generic_utility.get_setting('browser')
        if self.browser not in(BROWSER_CHROME, BROWSER_CHROME_LAUNCHER, BROWSER_EDGE, BROWSER_INTERNET_EXPLORER, BROWSER_SAFARI, BROWSER_CHROMIUM, BROWSER_ANDROID):
            generic_utility.notification(generic_utility.get_string(50001))
            xbmc.sleep(2000)
            self.valid_browser = False
            generic_utility.open_setting()
        self.valid_browser = True

    def __init__(self):
        global addon_path
        self.read_browser()

        self.strActionInfo = xbmcgui.ControlLabel(180, 60, 1200, 400, '', 'font14', '0xFFBBBBFF')
        self.addControl(self.strActionInfo)
        self.strActionInfo.setLabel(generic_utility.get_string(50005))

        addon_path = xbmcaddon.Addon().getAddonInfo("path")
