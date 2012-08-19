# -*- coding: utf-8 -*-

# imports
import sys
import urllib
import time
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import theguild

# Debug
DEBUG = False

__addon__ = xbmcaddon.Addon(id='plugin.video.theguild')
__info__ = __addon__.getAddonInfo
__plugin__ = __info__('name')
__version__ = __info__('version')
__icon__ = __info__('icon')
__fanart__ = __info__('fanart')

# Fanart
xbmcplugin.setPluginFanart(int(sys.argv[1]), __fanart__)

shows = theguild.get_theguild()


class Main:
  def __init__(self):
    if ('action=list' in sys.argv[2]):
      self.list_contents(self.arguments('name'))
    else:
      self.main_menu()

  def main_menu(self):
    if DEBUG:
      self.log('List available directories.')
    for season in sorted(shows.keys()):
      name = str(season)
      self.add_dir(name)
    xbmcplugin.endOfDirectory(int(sys.argv[1]), True)

  def list_contents(self, name):
    if DEBUG:
      self.log('List available episodes.')
    for video in shows[name]:
      _label = str(video.title)
      _title = str(video.title)
      _description = str(video.description.encode('utf-8'))
      _thumbnail = str(video.thumb_path)
      _url = str(video.video_path)
      _duration = str(time.strftime('%M:%S', time.gmtime(video.duration)))
      self.add_link(_title, _url, _thumbnail, _description, _duration, _label)
    xbmcplugin.endOfDirectory(int(sys.argv[1]), True)

  def add_link(self, name, url, iconimage, desc, duration, label):
    listitem = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    listitem.setProperty('fanart_image', __fanart__)
    listitem.setInfo(type="Video",
                     infoLabels={"Title": name,
                                 "Duration": duration,
                                 "Plot": desc,
                                 "Label": label,
                                 'tvshowtitle': __plugin__})
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, False)
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')

  def add_dir(self, name):
    listitem = xbmcgui.ListItem(name)
    listitem.setProperty('fanart_image', __fanart__)
    parameters = '%s?action=list&name=%s' % (sys.argv[0], name)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), parameters, listitem, True)

  def arguments(self, arg):
    _arguments = dict(part.split('=') for part in sys.argv[2][1:].split('&'))
    return urllib.unquote_plus(_arguments[arg])

  def log(self, description):
    xbmc.log("[ADD-ON] '%s v%s': %s" % (__plugin__, __version__, description), xbmc.LOGNOTICE)

if (__name__ == '__main__'):
  Main()