#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin, urllib2, urllib, re, string, sys, os, traceback, xbmcaddon, unicodedata, cookielib
import xml.dom.minidom, base64
import time

__plugin__ = 'StreamOn'
__author__ = 'streamon@gmail.com'
__url__ = 'http://code.google.com/'
__date__ = '13-09-2012'
__version__ = '1.0.20'
__settings__ = xbmcaddon.Addon(id='plugin.video.StreamOn')
__profilepath__    = xbmc.translatePath( __settings__.getAddonInfo('profile') )
__rooturl__ = 'http://getmore.host22.com/redirect.php?id=1.2'
__language__ = __settings__.getLocalizedString



#plugin modes
PLUGIN_MODE_BUILD_DIR = 10
PLUGIN_MODE_PLAY_YT_VIDEO = 20
PLUGIN_MODE_QUERY_DB = 30
PLUGIN_MODE_QUERY_YT = 40
PLUGIN_MODE_BUILD_YT_USER = 50
PLUGIN_MODE_BUILD_YT_FAV = 60
PLUGIN_MODE_PLAY_PLAYLIST = 80
PLUGIN_MODE_PLAY_SLIDESHOW = 90
PLUGIN_MODE_OPEN_SETTINGS = 100
PLUGIN_MODE_PLAY_STREAM = 110
PLUGIN_MODE_PLAY_4SHARED = 120


#view modes
VIEW_THUMB = 500
VIEW_POSTER = 501
VIEW_LIST = 502
VIEW_MEDIAINFO2 = 503
VIEW_MEDIAINFO = 504
VIEW_FANART = 508

main_thumb = os.path.join( __settings__.getAddonInfo( 'path' ), 'resources', 'media', 'StreamOn.png' )
media_id = 0


def open_url( url ):
	req = urllib2.Request( url )
	content = urllib2.urlopen( req )
	data = content.read()
	content.close()
	return data

def clean( name ):
	list = [ ( '&amp;', '&' ), ( '&quot;', '"' ), ( '<em>', '' ), ( '</em>', '' ), ( '&#39;', '\'' ), ( '&#039;', '\'' ), ('&amp;#039;', '\'') ]
	for search, replace in list:
		name = name.replace( search, replace )	
	#return unicode(name.encode('utf-8','ignore'))
	#return unicode(name)
	return  name.encode('utf-8','ignore')

def open_settings():
	__settings__.openSettings()

#Play a single youtube video
def play_youtube_video(video_id):
	print ("Playing video id: " + video_id + " name: " + name)
	url = video_id
	listitem = xbmcgui.ListItem( label = str(name), iconImage = "DefaultVideo.png", thumbnailImage = xbmc.getInfoImage( "ListItem.Thumb" ), path=url )
	infolabels = { "title": name, "plot": name, "TVShowTitle": name}
	listitem.setInfo( type="Video", infoLabels=infolabels)
	xbmc.Player( xbmc.PLAYER_CORE_DVDPLAYER ).play( str(url), listitem)


		
#Play a single song	
def play_stream(url, name):

	listitem = xbmcgui.ListItem( label = str(name), iconImage = "DefaultVideo.png", thumbnailImage = xbmc.getInfoImage( "ListItem.Thumb" ), path=url )
	if isMusicFile(url):
		print "playing music file: " + str(name) + " url: " + str(url)
		listitem.setInfo( type="Music", infoLabels={ "Title": name } )
	else:
		print "playing stream name: " + str(name)
		listitem.setInfo( type="video", infoLabels={ "Title": name, "Plot" : name, "TVShowTitle": name } )
	xbmc.Player( xbmc.PLAYER_CORE_DVDPLAYER ).play( str(url), listitem)


#Start picture slideshow or display single picture depending on whether user selected single picture or <start slideshow>
def play_picture_slideshow(origurl, name):
	print "Starting play_picture_slideshow(): " + str(origurl)

	#user clicked on a picture
	if origurl[-4:].lower()=='.jpg' or origurl[-4:].lower()=='.gif' or origurl[-4:].lower()=='.png':
		print "Single picture mode"		
		origurl = origurl.replace( ' ', '%20' )
		xbmc.log("adding to picture slideshow: " + str(origurl))
		xbmc.executehttpapi("ClearSlideshow")
		xbmc.executehttpapi("AddToSlideshow(%s)" % origurl)
		xbmc.executebuiltin( "SlideShow(,,notrandom)" )
		return
		
	#user clicked on <start slideshow>
	items = getItemsFromUrl(origurl)

	xbmc.executehttpapi("ClearSlideshow")	

	itemCount=0
	for item in items:
		itemCount=itemCount+1
		label, url, description, pubDate, guid, thumb, duration, rating, viewcount = getItemFields(item)
		if url is not None and url != '':
			xbmc.executehttpapi("AddToSlideshow(%s)" % url)

	print "# of pictures added to sideshow " + str(itemCount)
	xbmc.executebuiltin( "SlideShow(,,notrandom)" )


#Create and play a playlist from the video/audio files contained in the passed in RSS url
def play_playlist(origurl, index):
	print "Starting play_playlist(): url: " + str(origurl + " index: " + str(index))
	xbmc.executebuiltin("XBMC.Notification("+ __plugin__ +",Starting playlist from selection,60)")

	items = getItemsFromUrl(origurl)
	if items is None:
		return

	player = xbmc.Player()
	if player.isPlaying():
		player.stop()
    
	playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
	playlist.clear()   
	

	itemCount=0
	for item in items:
		label, url, description, pubDate, guid, thumb, duration, rating, viewcount = getItemFields(item)

		playlisturl = None

		#youtube video
	#	if url.startswith('plugin://plugin.video.youtube') in url:	
			#print "Found item: " + label + " guid: " + guid 
	#		print 'here'
	#		playlisturl = 'plugin://plugin.video.youtube/?action=play_video&amp;videoid=%s' % (url)

		#jtv video
		if url.startswith('plugin://plugin.video.jtv.archives') and 'play=True' in url:	
			playlisturl = url.replace('play=True','play=False')

		#4shared link
		elif '.4shared.com' in url and 'preview' in url:
			playlisturl = 'plugin://plugin.video.StreamOn/?mode=%d&name=%s&url=%s' % (PLUGIN_MODE_PLAY_4SHARED, urllib.quote_plus(label), urllib.quote_plus(url))


		#for rtmp/rtmpe streams if no timeout is specified, add the timeout specifed by user
		elif 'timeout=' not in url and (url.startswith('rtmpe://') or url.startswith('rtmp://')):				
			setting_streamtimeout = (__settings__.getLocalizedString(30211), __settings__.getLocalizedString(30212), __settings__.getLocalizedString(30213))[int(__settings__.getSetting('streamtimeout')) ]
			playlisturl = url + ' timeout=%s' % setting_streamtimeout

		#for sawlive.tv streams
		elif url.startswith('http://sawlive.tv/embed') or url.startswith('http://www.sawlive.tv/embed'):
			xbmc.log('Found sawlive.tv url..needs resolving: ' + url)

			if len(url) > 100:
				playlisturl = find_stream(url,name)
			else:
				playlisturl = find_sawlive_url(url,name)


		#for dailymotion video
		elif url.startswith('http://www.dailymotion.com/embed/video/') and guid is not None and guid != '':
				xbmc.log('Found dailymotion url..needs resolving: ' + url)
				playlisturl = resolve_dailymotion(url,guid)

		#for nova video
		elif url.startswith('http://embed.novamov.com') and guid is not None and guid != '':
				xbmc.log('Found nova url..needs resolving: ' + url)
				playlisturl = resolve_novamov(url,guid)



		#anything else
		elif url is not None and url != '':
			#print "Found item: " + label + " url: " + url 
			playlisturl = url
		
		if playlisturl is not None and playlisturl !='' and itemCount >= index - 1:
			listitem = xbmcgui.ListItem( label = label,  thumbnailImage = thumb, path=playlisturl )
			#listitem.setInfo( type="Video", infoLabels={ "Title": label } )

			if isMusicFile(playlisturl):
				xbmc.log("adding audio file to playlist %s %s" % (label,playlisturl))
				listitem.setInfo( type="Music", infoLabels={ "Title": label } )
				listitem.setProperty('mimetype','audio/mpeg')
			else:
				listitem.setInfo( type="video", infoLabels={ "Title": label, "Plot" : description, "TVShowTitle": label } )
				xbmc.log("adding video file to playlist %s %s" % (label,playlisturl))
			playlist.add(url=playlisturl, listitem=listitem)

		itemCount=itemCount+1	


	setting_shuffle = __settings__.getSetting('shuffle')
	setting_repeat = __settings__.getSetting('repeat')
	xbmc.log("setting_shuffle is: " + str(setting_shuffle) + " setting_repeat is: " + str(setting_repeat))

	# shuffle playlist 
	if setting_shuffle == 'true':
		playlist.shuffle()

	# put playlist on repeat
	if setting_repeat == 'true':
		xbmc.executebuiltin("xbmc.playercontrol(RepeatAll)")


	xbmc.Player().play(playlist)
	#xbmc.executebuiltin('playlist.playoffset(video, index)')


def play_fourshared(url, name):
	global media_id
	xbmc.log("starting 4shared method with: %s and %s" % (name, url))
	username = 'pakeeapp'
	password = 'xbmctesting'
	cookie_file = os.path.join(__profilepath__, 'pktemp.cookies')
	media_file = os.path.join(__profilepath__, ("pktemp%d.mp3" % (media_id)))
	cj = cookielib.LWPCookieJar()
	media_id = media_id + 1

	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
	loginurl = 'https://www.4shared.com/login?login=%s&password=%s' % (username, password)
	xbmc.log("logging in to 4shared: " + loginurl)
	resp = opener.open(loginurl)

	cj.save(cookie_file, ignore_discard=True)
	cj.load(cookie_file, ignore_discard=True)

	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
	urllib2.install_opener(opener)

	usock = opener.open(url)
	data = usock.read()
	#media_file = usock.geturl()
	usock.close()

	fp = open(media_file, 'wb')
	fp.write(data)
	fp.close()

	#play_stream(media_file, name)
	print "playing stream name: " + str(name) + " url: " + str(media_file)
	listitem = xbmcgui.ListItem( label = str(name), iconImage = "DefaultVideo.png", thumbnailImage = xbmc.getInfoImage( "ListItem.Thumb" ), path=media_file )
	listitem.setInfo( type="Music", infoLabels={ "Title": name } )
	xbmc.Player( xbmc.PLAYER_CORE_DVDPLAYER ).play( str(media_file), listitem)

#saw embed (long url) received in form of http://xxxxxxxxx&streamer=xxxxx
def find_stream(url, name):
	xbmc.log("Starting find_stream with url: " + str(url))
	pageUrl = url.split("&streamer=")[0]
	streamer = url.split("&streamer=")[1]
	print ('Opening ' + pageUrl)
	res = open_url(pageUrl)
	#print (res)
	playpath = ''
	swfUrl = ''

	for line in res.split("\n"):
		#print ("line:" + line)
		matches = re.search(r'file.*\'(.+)\'', line)
		if matches:
			playpath = matches.group(1)
			print ("Found playpath:" + playpath)

		matches = re.search(r'(http.+\.swf)', line)
		if matches:
			swfUrl = matches.group(1)
			print ("Found swfUrl:" + swfUrl)

	streamurl = "%s playpath=%s swfUrl=%s pageurl=%s swfVfy=true live=true" % (streamer, playpath, swfUrl, pageUrl)
	xbmc.log ("streamurl: " + streamurl)
	return (streamurl)


#saw embed (short url) received in form of http://xxxxxxxxx&streamer=xxxxx
def find_sawlive_url(url, name):
	xbmc.log("Starting find_sawlive_url with url: " + str(url))
	pageUrl = url.split("&streamer=")[0]
	streamer = url.split("&streamer=")[1]

	res = open_url(pageUrl)
	#print (res)
	playpath = ''
	swfUrl = ''

	for line in res.split("\n"):
		#print ("line:" + line)
		matches = re.search(r'src=[\"\']([^\"\']+)/[\"\']', line)
		if matches:
			playpath = matches.group(1)
			playpath = playpath.replace( '/view/', '/watch/' )
			print ("Found sawurl:" + playpath)


	url = "%s&streamer=%s" % (playpath, streamer)
	xbmc.log ("url: " + url)
	return (find_stream(url, name))

#dailymotion url received in form of 'http://embed.novamov.com/embed.php?v=xxxxx'
def resolve_novamov(url, guid):
	xbmc.log("Starting resolve_novamov with url: " + str(url) + " and guid: " + str(guid))
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()

	match1=re.compile('flashvars.file="(.+?)"').findall(link)
	for file in match1:
		file = file

	match2=re.compile('flashvars.filekey="(.+?)"').findall(link)
	for filekey in match2:
		filekey = filekey

	if not match1 or not match2:
		return 'CONTENTREMOVED'

	novaurl = 'http://www.novamov.com/api/player.api.php?user=undefined&key=' + filekey + '&codes=undefined&pass=undefined&file=' + file 

	req = urllib2.Request(novaurl)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()

	match3=re.compile('url=(.+?\.flv)').findall(link)
	for link in match3:
		link = link


	print ('auth url is ' + str(link))
	return link


#dailymotion url received in form of 'http://www.dailymotion.com/embed/video/xxxxx'
def resolve_dailymotion(url, guid):
	xbmc.log("Starting resolve_dailymotion with url: " + str(url) + " and guid: " + str(guid))
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()

	#match=re.compile('auth=(.+?)","stream').findall(link); 
	match=re.compile('\/([a-zA-Z0-9-_]+?)\.mp4\?auth=(.+?)","stream').findall(link)
	for guid, url in match:
	    match = 'http://www.dailymotion.com/cdn/H264-512x384/video/'+guid+'.mp4?auth='+url 
	    #match = 'http://www.dailymotion.com/cdn/H264-512x384/video/'+guid+'.mp4?auth='+url+'&redirect=0' 

	if not match:
		match = 'CONTENTREMOVED'
	print ('auth url is ' + str(match))
	return match

	#try:
	#	req = urllib2.Request(match)
	#	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	#	response = urllib2.urlopen(req)
	#	link=response.read()
	#	response.close()
	#	print ('dailmotion link is ' + str(link))
	#	return link
	#except:
	#	return 'VIDEOREMOVED'

def build_show_directory(origurl):

	if origurl:
		xbmc.log('Starting build_show_directory() with url: ' + origurl)
	else:
		xbmc.log('Starting build_show_directory() with no url. Showing info')
		return

	setting_playmode = int(__settings__.getSetting('playmode')) 
	xbmc.log("playmode is: " + str(setting_playmode))


	if 'Facebook' in origurl:
		xbmc.executebuiltin("XBMC.Notification("+ __plugin__ +","+__settings__.getLocalizedString(30052)+",100)")
	elif 'queryyt' in origurl:
		xbmc.executebuiltin("XBMC.Notification("+ __plugin__ +","+__settings__.getLocalizedString(30053)+",100)")

	#Read RSS items from origurl and store in items
	items = getItemsFromUrl(origurl)

	if items is None:
		return

	itemCount=0


	for item in items:


		#extract fields from each RSS item
		label, url, description, pubDate, guid, thumb, duration, rating, viewcount = getItemFields(item)

		descprefix = ''
		#if duration != 0:
		#	descprefix = descprefix + 'Duration: ' + str(duration) + ' min' + '\n'
		if pubDate != '01.01.1960':
			descprefix = descprefix + 'Uploaded: ' + str(pubDate) + '\n'
		if viewcount != 0:
			descprefix = descprefix + 'Views: ' + str(viewcount) + '\n'
		if rating != 0.0:
			descprefix = descprefix + 'Rated: ' + str(rating) + '/10' + '\n'

		description = descprefix + description		

		mode = PLUGIN_MODE_BUILD_DIR
		isFolder = True


		#if weird characters found in label or description, instead of erroring out, empty their values (empty listitem will be shown)
		try:
			xbmc.log('found in show_dir(): ' + str(label).encode('utf-8','ignore') + ' ' + str(thumb) + ' ' + str(rating) + ' ' + str(pubDate) + ' ' + str(duration) + ' ' + str(viewcount)) 
		except:

			try:
				xbmc.log('found in show_dir(): ' + clean(str(label)) + ' ' + str(thumb) + ' ' + str(rating) + ' ' + str(pubDate) + ' ' + str(duration) + ' ' + str(viewcount)) 

			except:
				xbmc.log('bad label name for entry')	

		if (url is not None and url != ''):

			#For feeds with videos as their first item, show <play all> listitem as first listitem	
			#Video found, check whether in single or playlist mode and set the mode/url accordingly
			if 'plugin://plugin.video.youtube' in url:
				isFolder = False
				#play single video
				if setting_playmode == 0:
					mode = PLUGIN_MODE_PLAY_YT_VIDEO
					url = url
				#play video playlist
				else:
					mode = PLUGIN_MODE_PLAY_PLAYLIST
					url = origurl



			if 'plugin://plugin.video.jtv.archives' in url and 'play=True' in url:				
				url = url.replace('play=True','play=False')


			#For feeds with pictures as their first item, show <start slideshow> as first listitem
			if url[-4:].lower()=='.jpg' or url[-4:].lower()=='.gif' or url[-4:].lower()=='.png':
				#For folders with videos, show play all option 			
				if itemCount == 0:
					resolvedlabel = '<' + str(__settings__.getLocalizedString(30051)) + '>'
					playAll = xbmcgui.ListItem( label = resolvedlabel, iconImage = main_thumb, thumbnailImage = main_thumb )
					xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = sys.argv[0] + "?mode="+str(PLUGIN_MODE_PLAY_SLIDESHOW)+"&name=Playlist&url=" + urllib.quote_plus(origurl), listitem = playAll, isFolder = True )

				isFolder = False
				mode = PLUGIN_MODE_PLAY_SLIDESHOW


			#audio track found, check whether in single or playlist mode and set the mode/url accordingly	
			if isMusicFile(url):

				#For feeds with mp3s as their first item, show <play all> listitem as first listitem			
				if itemCount == 0:
					resolvedlabel = '<' + str(__settings__.getLocalizedString(30050)) + '>'
					playAll = xbmcgui.ListItem( label = resolvedlabel, iconImage = main_thumb, thumbnailImage = main_thumb )
					xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = sys.argv[0] + "?mode="+str(PLUGIN_MODE_PLAY_PLAYLIST)+"&index=0&name=Playlist&url=" + urllib.quote_plus(origurl), listitem = playAll, isFolder = True )


				isFolder = False

				#play single video
				if setting_playmode == 0:
					mode = PLUGIN_MODE_PLAY_STREAM

				#play video playlist
				else:
					mode = PLUGIN_MODE_PLAY_PLAYLIST
					url = origurl

				if '.4shared.com' in url and 'preview' in url:
					mode = PLUGIN_MODE_PLAY_4SHARED

			if url.startswith('http://www.dailymotion.com/embed/video/'):
				xbmc.log('Found dailymotion url..needs resolving: ' + url)
				if itemCount == 0:
					resolvedlabel = '<' + str(__settings__.getLocalizedString(30050)) + '>'
					playAll = xbmcgui.ListItem( label = resolvedlabel, iconImage = main_thumb, thumbnailImage = main_thumb )
					xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = sys.argv[0] + "?mode="+str(PLUGIN_MODE_PLAY_PLAYLIST)+"&index=0&name=Playlist&url=" + urllib.quote_plus(origurl), listitem = playAll, isFolder = True )


				#play single video
				if setting_playmode == 0:
					mode = PLUGIN_MODE_PLAY_STREAM
					url = resolve_dailymotion(url,guid)
					if url == 'CONTENTREMOVED':
						label = 'Content Removed'


				#play video playlist
				else:
					mode = PLUGIN_MODE_PLAY_PLAYLIST
					url = origurl

			if url.startswith('http://embed.novamov.com'):
				xbmc.log('Found novamov url..needs resolving: ' + url)
				if itemCount == 0:
					resolvedlabel = '<' + str(__settings__.getLocalizedString(30050)) + '>'
					playAll = xbmcgui.ListItem( label = resolvedlabel, iconImage = main_thumb, thumbnailImage = main_thumb )
					xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = sys.argv[0] + "?mode="+str(PLUGIN_MODE_PLAY_PLAYLIST)+"&index=0&name=Playlist&url=" + urllib.quote_plus(origurl), listitem = playAll, isFolder = True )


				#play single video
				if setting_playmode == 0:
					mode = PLUGIN_MODE_PLAY_STREAM
					url = resolve_novamov(url,guid)
					if url == 'CONTENTREMOVED':
						label = 'Content Removed'


				#play video playlist
				else:
					mode = PLUGIN_MODE_PLAY_PLAYLIST
					url = origurl



			#video stream found
			if 'getmore' not in url and (url.startswith('rtmpe://') or url.startswith('rtmp://') or url.startswith('mms://') or url.startswith('rtsp://') or '.avi' in url or '.wmv' in url or '.m3u8' in url or '.flv' in url or '.wsx' in url or '.wmv' in origurl or '.avi' in origurl):
				isFolder = False

				#for rtmp/rtmpe streams if no timeout is specified, pick the timeout specifed by user
				if 'timeout=' not in url and (url.startswith('rtmpe://') or url.startswith('rtmp://')):				
					setting_streamtimeout = (__settings__.getLocalizedString(30211), __settings__.getLocalizedString(30212), __settings__.getLocalizedString(30213))[int(__settings__.getSetting('streamtimeout')) ]
					url = url + ' timeout=%s' % setting_streamtimeout

				#play single video
				if setting_playmode == 0:
					mode = PLUGIN_MODE_PLAY_STREAM

				#play video playlist
				else:
					mode = PLUGIN_MODE_PLAY_PLAYLIST
					url = origurl




			#sawlive.tv embed url found from which we need to extract stream
			if url.startswith('http://sawlive.tv/embed') or url.startswith('http://www.sawlive.tv/embed'):
				xbmc.log('Found sawlive.tv url..needs resolving: ' + url)

				#play single video
				if setting_playmode == 0:
					mode = PLUGIN_MODE_PLAY_STREAM
					if len(url) > 100:
						url = find_stream(url,name)
					else:
						url = find_sawlive_url(url,name)

				#play video playlist
				else:
					mode = PLUGIN_MODE_PLAY_PLAYLIST
					url = origurl



		itemCount=itemCount+1		
		xbmcplugin.setContent( handle=int( sys.argv[ 1 ] ), content='movies' )
		listitem = xbmcgui.ListItem( label = label, iconImage = thumb, thumbnailImage = thumb, path = url)
		infolabels = { "title": label, "plot": description, "plotoutline": description, "date": pubDate, "duration": duration, "rating": rating, "votes": viewcount, "tvshowtitle": label, "originaltitle": label, "count": viewcount, "TVShowTitle": label}
		listitem.setInfo( type="video", infoLabels=infolabels )


		if url:
			u = sys.argv[0] + "?mode=" + str(mode) + "&name=" + urllib.quote_plus( str(label) ) + "&url=" + urllib.quote_plus( url ) + "&index=" + str(itemCount)
		else:
			u = sys.argv[0] + "?mode=" + str(mode) + "&name=" + urllib.quote_plus( label ) + "&index=" + str(itemCount)
	
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = isFolder )


	#if only one audio/video file found, play it (rather than showing a new page with one item)
	#if itemCount == 1 and (mode == PLUGIN_MODE_PLAY_YT_VIDEO or mode == PLUGIN_MODE_PLAY_STREAM):
	if itemCount == 1:
		if mode == PLUGIN_MODE_PLAY_STREAM:
			xbmc.Player( xbmc.PLAYER_CORE_DVDPLAYER ).play( str(url), listitem)
			return
		elif mode == PLUGIN_MODE_PLAY_YT_VIDEO:
			play_youtube_video(guid, label)



	#show search options on only the main page
	if origurl == __rooturl__:

		searchYT = xbmcgui.ListItem( label = 'Search YouTube', iconImage = thumb, thumbnailImage = thumb )
		xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = sys.argv[0] + "?mode="+str(PLUGIN_MODE_QUERY_YT)+"&name=Search YouTube...", listitem = searchYT, isFolder = True )

		searchYT = xbmcgui.ListItem( label = 'YouTube user uploads/playlists', iconImage = thumb, thumbnailImage = thumb )
		xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = sys.argv[0] + "?mode="+str(PLUGIN_MODE_BUILD_YT_USER)+"&name=YouTube user uploads and playlists", listitem = searchYT, isFolder = True )

		#searchYT = xbmcgui.ListItem( label = 'YouTube user favorites...', iconImage = thumb, thumbnailImage = thumb )
		#xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = sys.argv[0] + "?mode="+str(PLUGIN_MODE_BUILD_YT_FAV)+"&name=YouTube user favorites", listitem = searchYT, isFolder = True )


		settings = xbmcgui.ListItem( label = 'Settings', iconImage = thumb, thumbnailImage = thumb )
		xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = sys.argv[0] + "?mode="+str(PLUGIN_MODE_OPEN_SETTINGS)+"&name=Settings", listitem = settings, isFolder = True )



	#get the view sort order specified by user in settings
	setting_sort_order = (__settings__.getLocalizedString(30101), __settings__.getLocalizedString(30102))[int(__settings__.getSetting('viewsortorder')) ]

	xbmc.log("setting_sort_order is " + str(setting_sort_order))
	
	#set requested sort order
	if setting_sort_order == 'Title':
		xbmc.log("Setting view sort order to 'Title'")
		sortmethods = ( xbmcplugin.SORT_METHOD_LABEL, xbmcplugin.SORT_METHOD_VIDEO_RUNTIME, xbmcplugin.SORT_METHOD_DATE, xbmcplugin.SORT_METHOD_PROGRAM_COUNT, xbmcplugin.SORT_METHOD_UNSORTED )
	else:
		sortmethods = ( xbmcplugin.SORT_METHOD_UNSORTED, xbmcplugin.SORT_METHOD_LABEL, xbmcplugin.SORT_METHOD_VIDEO_RUNTIME, xbmcplugin.SORT_METHOD_DATE, xbmcplugin.SORT_METHOD_PROGRAM_COUNT  )

	for sortmethod in sortmethods:	
		xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=sortmethod )	

	#display the view based on selection from settings
	setting_viewname = (VIEW_THUMB, VIEW_POSTER, VIEW_LIST, VIEW_MEDIAINFO, VIEW_MEDIAINFO2, VIEW_FANART)[ int(__settings__.getSetting('viewname')) ] 
	xbmc.executebuiltin("Container.SetViewMode("+str(setting_viewname)+")")

	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )



def isMusicFile(url):

	if 'dailymotion.com' in url:
		return False
	if '.mp3' in url or '.wma' in url or '.m4a' in url or 'http://bit.ly' in url or '/getSharedFile/' in url or '.mp4' in url or 'kiwi6.com' in url:
		return True
	else:
		return False

#open url and parse XML using dom
def getItemsFromUrl(url):

	username = __settings__.getSetting('username')
	password = __settings__.getSetting('password')

	#if no credentials entered
#	if username == '' or password == '':
#		print __settings__.getLocalizedString(30501).replace('\\n','\n')
#		xbmcgui.Dialog().ok(__settings__.getLocalizedString(30500),__settings__.getLocalizedString(30501).replace('\\n','\n'))
#		open_settings()
#		return

	try:
#		passman = urllib2.HTTPPasswordMgrWithDefaultRealm()

		# this creates a password manager
#		passman.add_password(None, url, username, password)

#		authhandler = urllib2.HTTPBasicAuthHandler(passman)

#		opener = urllib2.build_opener(authhandler)
#		urllib2.install_opener(opener)

		file = urllib2.urlopen(url, timeout=140)
		data = file.read()
		file.close()
		comment = '<!-- Hosting24 Analytics Code -->'
		comment2 = '<script type="text/javascript" src="http://stats.hosting24.com/count.php"></script>'
		comment3 = '<!-- End Of Analytics Code -->'
		pos = data.find( comment )
		if comment in data:
			data = data.replace( comment, ' ' )
			data = data.replace( comment2, ' ' )
			data = data.replace( comment3, ' ' )

	except urllib2.HTTPError, e:
		errorMsg = str(e)

		#invalid credentials passed
		if 'HTTP Error 401' in errorMsg:
			print __settings__.getLocalizedString(30502)
			print errorMsg
			xbmcgui.Dialog().ok(__settings__.getLocalizedString(30500),__settings__.getLocalizedString(30502).replace('\\n','\n'))
			open_settings()

		#url not found at start (root url not found). server down ask user to check later
		elif url == __rooturl__:
			print __settings__.getLocalizedString(30504)
			print errorMsg
			xbmcgui.Dialog().ok(__settings__.getLocalizedString(30500),__settings__.getLocalizedString(30504).replace('\\n','\n'))

		#url not found during navigation within addon, ask user to try another link
		else:
			print __settings__.getLocalizedString(30503)
			print errorMsg
			xbmcgui.Dialog().ok(__settings__.getLocalizedString(30500),__settings__.getLocalizedString(30503).replace('\\n','\n'))
		return

	dom =  xml.dom.minidom.parseString(data)
	items = dom.getElementsByTagName('item')
	return items


#extract fields from each RSS item parsed via dom
def getItemFields(item):

	label=''
	url = ''
	thumb = ''
	guid = ''
	description = ''
	pubDate = '01.01.1960'
	rating = 0.0
	duration = 0
	viewcount = '0'

	if item.getElementsByTagName("title"):
		label = clean(getText(item.getElementsByTagName("title")[0].childNodes))
	else:
		label = 'No title'
	if item.getElementsByTagName("enclosure"):
		url = item.getElementsByTagName("enclosure")[0].getAttribute('url')
		print ('Found enclosure link: ' + url)
	elif item.getElementsByTagName("link"):
		url = getText(item.getElementsByTagName("link")[0].childNodes)

	else:
		url = ''

	if item.getElementsByTagNameNS("http://www.itunes.com/dtds/podcast-1.0.dtd","summary"):
		description = clean(getText(item.getElementsByTagNameNS("http://www.itunes.com/dtds/podcast-1.0.dtd","summary")[0].childNodes))
	elif item.getElementsByTagName("description"):
		description = clean(getText(item.getElementsByTagName("description")[0].childNodes))
	else:
		description = ''

	if item.getElementsByTagNameNS("http://search.yahoo.com/mrss/","thumbnail"):
		thumb = item.getElementsByTagNameNS("http://search.yahoo.com/mrss/","thumbnail")[0].getAttribute('url')
	elif item.getElementsByTagName("thumbnail"):
		thumb = clean(getText(item.getElementsByTagName("thumbnail")[0].childNodes))
	else:
		thumb = main_thumb

	if item.getElementsByTagNameNS("http://search.yahoo.com/mrss/","content"):
		duration = item.getElementsByTagNameNS("http://search.yahoo.com/mrss/","content")[0].getAttribute('duration')
	else:
		duration = ''
	if duration == '':
		duration = 0
	else:
		duration = string.atoi(duration)
	duration = time.strftime('%H:%M:%S', time.gmtime(duration))

	
	if item.getElementsByTagNameNS("http://search.yahoo.com/mrss/","starRating"):
		rating = item.getElementsByTagNameNS("http://search.yahoo.com/mrss/","starRating")[0].getAttribute('average')
	else:
		rating = ''
	if rating == '':
		rating = 0.0
	else:
		rating = string.atof(rating)

	if item.getElementsByTagNameNS("http://search.yahoo.com/mrss/","starRating"):
		viewcount = item.getElementsByTagNameNS("http://search.yahoo.com/mrss/","starRating")[0].getAttribute('viewcount')
		if viewcount == '':
			viewcount = '0'
	else:
		viewcount = '0'
	viewcount = string.atoi(viewcount)


	if item.getElementsByTagName("pubDate"):
		pubDate = getText(item.getElementsByTagName("pubDate")[0].childNodes)
		if pubDate == '':
			pubDate = '01.01.1960'
		elif '+' in pubDate:
			tpubDate = time.strptime(pubDate, '%a, %d %b %Y %H:%M:%S +0000')
			pubDate = time.strftime("%d.%m.%Y", tpubDate)
		else:
			try:
				tpubDate = time.strptime(pubDate, '%Y-%m-%d')
			except:
				tpubDate = time.strptime(pubDate, '%a, %d %b %Y %H:%M:%S GMT')


			pubDate = time.strftime("%d.%m.%Y", tpubDate)
	else:
		pubDate = '01.01.2012'

	if item.getElementsByTagName("guid"):
		guid = getText(item.getElementsByTagName("guid")[0].childNodes)

	return label, url, description, pubDate, guid, thumb, duration, rating, viewcount



def getText(nodelist):
	rc = []
	for node in nodelist:
		if node.nodeType == node.TEXT_NODE:
			rc.append(node.data)
	return ''.join(rc)


	
def build_search_directory(paramName):
	if paramName == 'querydb':
		title = 'Search DB'
	else:
		title = 'Search YouTube'

	keyboard = xbmc.Keyboard( '', title )
	keyboard.doModal()
	if ( keyboard.isConfirmed() == False ):
		return
	search_string = keyboard.getText().replace( ' ', '_' )
	if len( search_string ) == 0:
		return

	build_show_directory('http://getmore.host22.com/youtube.php?search=' + search_string)


def build_ytuser_directory():
	keyboard = xbmc.Keyboard( '', 'Enter YouTube userid' )
	keyboard.doModal()
	if ( keyboard.isConfirmed() == False ):
		return
	search_string = keyboard.getText().replace( ' ', '_' )
	if len( search_string ) == 0:
		return

	build_show_directory('http://getmore.host22.com/youtube.php?user=' + search_string)



	

def get_params():
	param = []
	paramstring = sys.argv[2]
	if len( paramstring ) >= 2:
		params = sys.argv[2]
		cleanedparams = params.replace( '?', '' )
		if ( params[len( params ) - 1] == '/' ):
			params = params[0:len( params ) - 2]
		pairsofparams = cleanedparams.split( '&' )
		param = {}
		for i in range( len( pairsofparams ) ):
			splitparams = {}
			splitparams = pairsofparams[i].split( '=' )
			if ( len( splitparams ) ) == 2:
				param[splitparams[0]] = splitparams[1]					
	return param


params = get_params()
url = None
name = None
mode = None
description = None
page = 0


try:
	url = urllib.unquote_plus( params['url'] )
except:
	pass
try:
	name = urllib.unquote_plus( params['name'] )
except:
	pass
try:
	mode = int( params['mode'] )
except:
	pass
try:
        page = int( params['page'] )
except:
        pass

try:
        index = int( params['index'] )
except:
        pass

print ("addon started with mode: " + str(mode))


if mode == None:
	build_show_directory(__rooturl__)

elif mode == PLUGIN_MODE_BUILD_DIR:
	build_show_directory(url)
elif mode == PLUGIN_MODE_PLAY_YT_VIDEO:
	#play_playlist(url, index)
	play_youtube_video(url)
elif mode == PLUGIN_MODE_QUERY_DB:
	build_search_directory('querydb')
elif mode == PLUGIN_MODE_QUERY_YT:
	build_search_directory('queryyt')
elif mode == PLUGIN_MODE_BUILD_YT_USER:
	build_ytuser_directory()
elif mode == PLUGIN_MODE_BUILD_YT_FAV:
	build_ytuser_favs_directory()
elif mode == PLUGIN_MODE_PLAY_PLAYLIST:
	play_playlist(url, index)
elif mode == PLUGIN_MODE_PLAY_SLIDESHOW:
	play_picture_slideshow(url, name)
elif mode == PLUGIN_MODE_PLAY_STREAM:
	play_stream(url, name)
elif mode == PLUGIN_MODE_OPEN_SETTINGS:
	open_settings()
elif mode == PLUGIN_MODE_PLAY_4SHARED:
	play_fourshared(url,name)


