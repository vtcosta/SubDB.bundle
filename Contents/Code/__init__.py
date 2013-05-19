# http://thesubdb.com/api/

import os, glob, inspect, urllib, urllib2
from subprocess import Popen, PIPE
from urllib2 import URLError, HTTPError

SUBDB_URL = 'http://api.thesubdb.com/'
USERAGENT = 'SubDB/1.0 (SubDB.bundle/1.0; https://github.com/fvitorc/SubDB.bundle)'

class SubInfo():
  def __init__(self, lang, url, sub):
    self.lang = lang
    self.url = url
    self.sub = sub
    self.ext = 'srt'

def Start():
  HTTP.CacheTime = 0
  HTTP.Headers['User-agent'] = 'plexapp.com v9.0'

def ValidatePrefs():
  return

def downloadSubtitle(filename, lang):
  hash = computeHash(filename)
  Log('Searching subtitle for %s (hash: %s; lang: %s)' % (os.path.basename(filename), hash, lang))
  
  try:
    data = urllib.urlencode({'action': 'download', 'hash': hash, 'language': lang})
    url = SUBDB_URL + '?' + data
    req = urllib2.Request(url, None, { 'User-Agent' : USERAGENT })
    sub = urllib2.urlopen(req).read()
    
    Log('Hooray, subtitle found!')
    return SubInfo(lang, url, sub)
  except HTTPError as e:
    if e.code == 404:
      Log('No subtitles available for language ' + lang)
    elif e.code == 400:
      Log('Malformed request. Contact the developer.')
    else:
      Log.Error('Unknown response: ' + e.code)
  except URLError as e:
    Log.Error('We failed to reach the server: ' + e.reason)

def computeHash(filename):
  directory = os.path.dirname(inspect.getsourcefile( lambda:None ))
  script = os.path.join(directory, 'subdb_hash.py')
  proc = Popen(['python', script, filename], stdout=PIPE, stderr=PIPE, shell=False)
  (out, err) = proc.communicate()
  for line in err.splitlines():
    Log.Error(line)
  for line in out.splitlines():
    return line

def shouldDownloadSubtitle(MediaPath, Language):
  filename = '%s.%s.*' % (os.path.splitext(MediaPath)[0], Language)
  return not Prefs["saveNextToMedia"] or Prefs["overwriteNextToMedia"] or not glob.glob(filename)

def getLangList():
  langList = []
  if Prefs["langPref1"] != 'None':
    langList.append(Prefs["langPref1"])
  if Prefs["langPref2"] != 'None':
    langList.append(Prefs["langPref2"])
  return langList

def processItems(mediaItems):
  for item in mediaItems:
    for part in item.parts:
      for lang in getLangList():
        if not shouldDownloadSubtitle(part.file, lang):
          Log('Skipping, subtitle already exists')
          continue
        
        subInfo = downloadSubtitle(part.file, lang)
        if subInfo:
          if Prefs["saveNextToMedia"]:
            Log('Saving subtitle next to media')
            filename = '%s.%s.%s' % (os.path.splitext(part.file)[0], subInfo.lang, subInfo.ext)
            Core.storage.save(filename, subInfo.sub, binary=False)
          else:
            Log('Saving subtitle to PMS library')
            p.subtitles[subInfo.lang][subInfo.url] = Proxy.Media(subInfo.sub, ext=subInfo.ext)


class SubDBAgentMovies(Agent.Movies):
  name = 'SubDB'
  languages = [Locale.Language.English]
  primary_provider = False
  contributes_to = ['com.plexapp.agents.imdb', 'com.plexapp.agents.themoviedb']
  
  def search(self, results, media, lang):
    results.Append(MetadataSearchResult(
      id    = 'null',
      score = 100  ))
    
  def update(self, metadata, media, lang):
    processItems(media.items)


class SubDBAgentTV(Agent.TV_Shows):
  name = 'SubDB'
  languages = [Locale.Language.English]
  primary_provider = False
  contributes_to = ['com.plexapp.agents.thetvdb']

  def search(self, results, media, lang):
    results.Append(MetadataSearchResult(
      id    = 'null',
      score = 100  ))

  def update(self, metadata, media, lang):
    for season in media.seasons:
      for episode in media.seasons[season].episodes:
        processItems(media.seasons[season].episodes[episode].items)
