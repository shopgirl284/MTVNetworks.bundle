TITLE = 'MTV Networks'
PREFIX = '/video/mtvnetworks'

ART = 'art-default.jpg'
ICON = 'icon-default.png'

RE_MANIFEST_URL = Regex('var triforceManifestURL = "(.+?)";', Regex.DOTALL)
RE_MANIFEST_FEED = Regex('var triforceManifestFeed = (.+?);\n', Regex.DOTALL)

ENT_LIST = ['ent_m100', 'ent_m150', 'ent_m151', 'ent_m112', 'ent_m116', 'ent_l001']
SEARCH_TYPE = ['Video', 'Specials', 'Episode', 'Series']

SHOWS_LIST = [
    {'title': 'MTV', 'base_url' : 'http://www.mtv.com', 'search_url' : 'http://relaunch-search.mtv.com/solr/mtv/select?q=%s&wt=json&defType=edismax&start=', 'site_code' : '_mtv', 'icon' : 'mtv-icon.png'}, 
    {'title': 'VH1', 'base_url' : 'http://www.vh1.com', 'search_url' : 'http://search.vh1.com/solr/vh1/select?q=%s&wt=json&defType=edismax&start=', 'site_code' : '_vh1', 'icon' : 'vh1-icon.png'}, 
    {'title': 'CMT', 'base_url' : 'http://www.cmt.com', 'search_url' : 'http://search.cmt.com/solr/cmt/select?q=%s&wt=json&defType=edismax&start=', 'site_code' : '_cmt', 'icon' : 'cmt-icon.png'}, 
    {'title': 'LogoTV', 'base_url' : 'http://www.logotv.com', 'search_url' : 'http://search.logotv.com/solr/logo/select?q=%s&wt=json&defType=edismax&start=', 'site_code' : '_logo', 'icon' : 'logo-icon.png'}, 
]

###################################################################################################
# Set up containers for all possible objects
def Start():

    ObjectContainer.title1 = TITLE

    DirectoryObject.thumb = R(ICON)
    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36'
 
#####################################################################################
@handler(PREFIX, TITLE, art=ART, thumb=ICON)
def MainMenu():
    oc = ObjectContainer()
  
    for item in SHOWS_LIST:
        oc.add(DirectoryObject(
            key = Callback(
                WebsiteMenu,
                title=item['title'],
                url=item['base_url'],
                search_url=item['search_url'],
                site_code=item['site_code'],
                thumb=R(item['icon'])
            ),
            title=item['title'],
            thumb = R(item['icon'])
        ))

    return oc

####################################################################################################
@route(PREFIX + '/websitemenu')
def WebsiteMenu(title, url, site_code, search_url='', thumb=''):
    
    oc = ObjectContainer(title2=title)
    oc.add(DirectoryObject(key=Callback(FeedMenu, title='Shows', url=url+'/shows', thumb=thumb, site_code=site_code), title='Shows', thumb=thumb))
    oc.add(DirectoryObject(key=Callback(FeedMenu, title='Full Episodes', url=url+'/full-episodes', thumb=thumb, site_code=site_code), title='Full Episodes', thumb=thumb))
    if 'MTV' in title:
        oc.add(DirectoryObject(key=Callback(FeedMenu, title='MTV2 Shows', url=url+'/mtv2', thumb=thumb, site_code=site_code), title='MTV2 Shows', thumb=thumb))
    oc.add(InputDirectoryObject(key = Callback(SearchSections, title="Search", search_url=search_url, thumb=thumb), title = "Search", thumb=thumb))
    feed_list = GetFeedList(url)
    for feed in feed_list:
        if '/feeds/ent_m177' in feed:
            oc.add(DirectoryObject(key=Callback(OtherVideos, title='Most Viewed Videos', url=feed, base_url=url), title='Most Viewed Videos', thumb=thumb))
    return oc
####################################################################################################
# This function pulls the json feeds in the ENT_LIST for the Shows and Full Episode main pages and Specials video page
# A separate function (ShowSections) is used to pull the individual show full episode and video clips
@route(PREFIX + '/feedmenu')
def FeedMenu(title, url, thumb='', site_code=' '):
    
    oc = ObjectContainer(title2=title)
    feed_list = GetFeedList(url)
    if feed_list<1:
        return ObjectContainer(header="Incompatible", message="Unable to find video feeds for %s." %url)
    
    for json_feed in feed_list:
        # Split feed to get ent code
        try: ent_code = json_feed.split('/feeds/')[1].split('/')[0]
        except: ent_code = ''
        ent_code = ent_code.split(site_code)[0]
        if ent_code not in ENT_LIST:
            continue

        json = JSON.ObjectFromURL(json_feed, cacheTime = CACHE_1DAY)
        
        # Create menu for the ent_l001 - Specials video page
        if ent_code=='ent_l001':
            try: title = json['result']['data']['header']['title'].title()
            except: title = 'Videos'
            base_url = url.split('.com')[0] + '.com'
            oc.add(DirectoryObject(key=Callback(OtherVideos, title=title, url=json_feed, base_url=base_url),
                title=title,
                thumb=thumb
            ))
        # Create menu items for those that need to go to Produce Sections
        # ent_m100-featured show and ent_m150-all shows
        elif ent_code in ['ent_m100', 'ent_m150']:
            try: title = json['result']['data']['headerText'].title()
            except: title = ''
            oc.add(DirectoryObject(key=Callback(ProduceSection, title=title, url=json_feed),
                title=title,
                thumb=thumb
            ))
        # Create menu for the ent_m151 - full episodes to produce videos and menu items for full episode feeds by show
        else:
            # Titles for video clips and full episodes for individual shows are under promo/headline
            try: title = json['result']['promo']['headline'].title()
            except: 
                # Full episode feed titles are under data/headerText
                try: title = json['result']['data']['headerText'].title()
                except: title = ''
            oc.add(DirectoryObject(key=Callback(ShowVideos, title=title, url=json_feed),
                title=title,
                thumb=thumb
            ))
        # Also create additional menu items for full episode feeds for each show
        if ent_code == 'ent_m151':
            for item in json['result']['data']['shows']:
                oc.add(DirectoryObject(key=Callback(ShowVideos, title=item['title'], url=item['url']),
                    title=item['title'],
                    thumb=thumb
                ))

            
    if len(oc) < 1:
        return ObjectContainer(header="Empty", message="There are no results to list.")
    else:
        return oc
#######################################################################################
# This function pulls the video links from the navigation bar and produces the video feeds for those sections
# Cannot use the FeedMenu function because the show main pages do not give a full json feed for full episodes and video clips
@route(PREFIX + '/showsections')
def ShowSections(title, url, thumb=''):
    
    oc = ObjectContainer(title2=title)
    base = url.split('.com')[0] + '.com'
    content = HTTP.Request(url, cacheTime=CACHE_1DAY).content
    page = HTML.ElementFromString(content)
        
    if not thumb:
        try: thumb = page.xpath('//meta[@property="og:image"]/@content')[0].strip()
        except: thumb = ''

    # Get the full episode and video clip feeds 
    for section in page.xpath('//ul[@class="show_menu"]/li/a'):
        section_title = section.xpath('./text()')[0].strip().title()
        section_url = section.xpath('./@href')[0]
        if not section_url.startswith('http://'):
            section_url = base + section_url
        if 'Episode' in section_title or 'Video' in section_title or 'Film' in section_title:
            feed_list = GetFeedList(section_url)
            # There should only be one feed listed for show video pages
            if 'ent_m112' in feed_list[0] or 'ent_m116' in feed_list[0]:
                oc.add(DirectoryObject(
                    key=Callback(ProduceSection, title=section_title, url=feed_list[0], result_type='filters', thumb=thumb),
                    title=section_title,
                    thumb = Resource.ContentsOfURLWithFallback(url=thumb)
                ))
        # Create video object for listed special full shows
        elif 'Full Special' in section_title:
            oc.add(VideoClipObject(
                url = section_url, 
                title = section_title, 
                thumb = Resource.ContentsOfURLWithFallback(url=thumb)
            ))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no video sections for this show." )
    else:
        return oc
#####################################################################################
# This function produces the sections in a json feeds
# Used for show lists, AtoZ show lists, and individuals shows full episodes and video clips filters
@route(PREFIX + '/producesections', alpha=int)
def ProduceSection(title, url, result_type='items', thumb='', alpha=None):
    
    oc = ObjectContainer(title2=title)
    (section_title, feed_url) = (title, url)
    counter=0
    json = JSON.ObjectFromURL(url)

    # To create show (data items) lists
    try: 
        item_list = json['result']['data'][result_type]
    except: 
        # To create filter lists
        try: item_list = json['result'][result_type]
        except: item_list = []
    # To create list for alphabet sections for the AtoZ listings
    if '/ent_m150/' in feed_url and alpha:
        item_list = json['result']['data']['items'][alpha]['sortedItems']
    for item in item_list:
        # For show lists
        if '/ent_m150/' in feed_url or '/ent_m100/' in feed_url:
            # Produce alpha items for AtoZ
            if '/ent_m150/' in feed_url and not alpha:
                oc.add(DirectoryObject(
                    key=Callback(ProduceSection, title=item['letter'], url=feed_url, result_type=result_type, alpha=counter),
                    title=item['letter']
                ))
                counter=counter+1
            # Produce shows under Featured, a letter or other show section
            else:
                try: url = item['canonicalURL']
                except:
                    try: url = item['url']
                    except: continue
                # Skip bad show urls that do not include '/shows/' or events. If '/events/' there is no manifest.
                if '/shows/' not in url:
                    continue
                try: thumb = item['image']['url']
                except: thumb = thumb
                if thumb.startswith('//'):
                    thumb = 'https:' + thumb
                oc.add(DirectoryObject(
                    key=Callback(ShowSections, title=item['title'], url=url, thumb=thumb),
                    title=item['title'],
                    thumb = Resource.ContentsOfURLWithFallback(url=thumb)
                ))
        # For filters in full episodes and video links of shows
        else:
            try: title=item['name']
            except: continue
            if title.isdigit():
                title = 'Season %s' %title
            oc.add(DirectoryObject(
                key=Callback(ShowVideos, title=title, url=item['url']),
                title=title,
                thumb=Resource.ContentsOfURLWithFallback(url=thumb)
            ))
    
    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no results to list right now.")
    else:
        return oc
#######################################################################################
# This function produces the videos listed in json feed
# Produces main full episodes feeds as well as the full episode and video-clip feeds for individual shows
@route(PREFIX + '/showvideos')
def ShowVideos(title, url):

    oc = ObjectContainer(title2=title)
    json = JSON.ObjectFromURL(url)
    # Feeds for video clips (ent_m116) and latest videos (ent_m067, ent_m101) for individual shows list videos under result/items
    try: videos = json['result']['items']
    except: 
        # Feeds for full episode (ent_m151) and full episode for individual shows (ent_m112) list videos under result/data/items
        try: videos = json['result']['data']['items']
        except: return ObjectContainer(header="Empty", message="There are no videos to list right now.")
    
    for video in videos:

        # some items are just ads so skip any without a URL
        if 'isAd' in video:
            continue
        # Indivudual show video urls are under canonicalURL and full episode feeds are under itemURL
        try: vid_url = video['canonicalURL']
        except:
            try: vid_url = video['itemURL']
            except: continue

        # catch any bad links that get sent here
        if not ('/video-clips/') in vid_url and not ('/full-episodes/') in vid_url and not ('/episodes/') in vid_url:
            continue

        # Individual show images are under images and full episode feeds are under image
        try: thumb = video['images'][0]['url']
        except:
            try: thumb = video['image'][0]['url']
            except:  thumb = None
        if thumb.startswith('//'):
            thumb = 'http:' + thumb

        # Show names for Individual shows are under show/title and full episode feeds are under showTitle
        try: show = video['show']['title']
        except: show = video['showTitle']
        # Seasons and episodes for Individual shows are under season and full episode feeds are not
        try: episode = int(video['season']['episodeAiringOrder'])
        except: 
            try: episode = int(video['episodeAiringOrder'])
            except: episode = 0
        try: season = int(video['season']['seasonNumber'])
        except: 
            try: season = int(video['seasonNumber'])
            except: season = 0
        
        # Dates for Individual shows are unix and full episode feeds are strings
        raw_date = video['airDate']
        Log('the value of raw_date is %s' %raw_date)
        if raw_date and raw_date.isdigit(): 
            raw_date = Datetime.FromTimestamp(float(raw_date)).strftime('%m/%d/%Y')
        date = Datetime.ParseDate(raw_date)

        # Duration for Individual shows are integers/floats and full episode feeds are strings
        duration = video['duration']
        try: duration = Datetime.MillisecondsFromString(duration)
        except:
            # Durations for clips have decimal points
            if not isinstance(duration, int):
                duration = int(duration.split('.')[0])
            duration = duration * 1000

        # Everything else has episode and show info now
        oc.add(EpisodeObject(
            url = vid_url, 
            show = show,
            season = season,
            index = episode,
            title = video['title'], 
            thumb = Resource.ContentsOfURLWithFallback(url=thumb ),
            originally_available_at = date,
            duration = duration,
            summary = video['description']
        ))

    # Individual show next pages are under results/nextPageURL and full episode feeds are under results/data
    try: next_page = json['result']['data']['nextPageURL']
    except: 
        try: next_page = json['result']['nextPageURL']
        except: next_page = None

    if next_page and len(oc) > 0:
        # Check for query string for full episodes by show (?filterShowId=)
        try: next_query = json['result']['data']['nextPageURLqueryString']
        except: next_query = None
        if next_query: 
            next_page = '%s?%s' %(next_page, next_query)

        oc.add(NextPageObject(
            key = Callback(ShowVideos, title=title, url=next_page),
            title = 'Next Page ...'
        ))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no unlocked videos available to watch.")
    else:
        return oc
#######################################################################################
# This function produces video results for the shorter special json feeds
@route(PREFIX + '/othervideos')
def OtherVideos(title, url, base_url):

    oc = ObjectContainer(title2=title)
    try: 
        json = JSON.ObjectFromURL(url)
        videos = json['result']['data']['items']
    except: return ObjectContainer(header="Empty", message="There are no videos to list right now.")
    
    for video in videos:

        try: vid_url = video['url']
        except: continue
        if not vid_url.startswith('http://'):
            vid_url = base_url + vid_url
        try: thumb=video['image']['url']
        except: thumb=video['image'][0]['url']
        try: date = Datetime.ParseDate(video['airDate'])
        except: date = None
        try: duration = Datetime.MillisecondsFromString(video['duration'])
        except: 
            try: duration = Datetime.MillisecondsFromString(video['flags']['display'])
            except: duration = None
        try: show = video['header']
        except: 
            try: show = video['label']
        oc.add(EpisodeObject(
            url = vid_url, 
            title = video['title'], 
            show = show, 
            thumb = Resource.ContentsOfURLWithFallback(url=thumb),
            originally_available_at = date,
            duration = duration
        ))

    try: next_page = json['result']['data']['nextPage']['url']
    except: next_page = None

    if next_page and len(oc) > 0:

        oc.add(NextPageObject(
            key = Callback(OtherVideos, title=title, url=next_page, base_url=base_url),
            title = 'Next Page ...'
        ))

    if len(oc) < 1:
        return ObjectContainer(header="Empty", message="There are no videos available.")
    else:
        return oc
####################################################################################################
@route(PREFIX + '/searchsections')
def SearchSections(title, search_url, query, thumb):
    
    oc = ObjectContainer(title2=title)
    json_url = search_url %String.Quote(query, usePlus = False)
    local_url = json_url + '0&facet=on&facet.field=bucketName_s'
    json = JSON.ObjectFromURL(local_url)
    i = 0
    search_list = json['facet_counts']['facet_fields']['bucketName_s']
    for item in search_list:
        if item in SEARCH_TYPE and search_list[i+1]!=0:
            oc.add(DirectoryObject(key = Callback(Search, title=item, url=json_url, search_type=item), title = item, thumb=thumb))
        i=i+1

    return oc
####################################################################################################
@route(PREFIX + '/search', start=int)
def Search(title, url, start=0, search_type=''):

    oc = ObjectContainer(title2=title)
    local_url = '%s%s&fq=bucketName_s:%s' %(url, start, search_type)
    json = JSON.ObjectFromURL(local_url)

    for item in json['response']['docs']:
        title = item['title_t']
        try: item_url=item['url_s']
        except: continue
        try: thumb = item['imageUrl_s']
        except: thumb = ''
        # For Specials
        if search_type=='Specials':
            vid_url = item_url + '/videos'
            oc.add(DirectoryObject(key=Callback(FeedMenu, title=title, url=vid_url, thumb=thumb),
                title = title, thumb = Resource.ContentsOfURLWithFallback(url=thumb)
            ))
        # For Shows
        elif search_type=='Series':
            oc.add(DirectoryObject(key=Callback(ShowSections, title=title, url=item_url, thumb=thumb),
                title = title, thumb = Resource.ContentsOfURLWithFallback(url=thumb)
            ))
        # For Episodes and Videos
        else:
            try: season = int(item['seasonNumber_s'].split(':')[0])
            except: season = 0
            try: episode = int(item['episodeNumber_s'])
            except: episode = 0
            try: show = item['parentTitle_t']
            except: show = ''
            try: summary = item['description_t']
            except: summary = ''
            try: duration = Datetime.MillisecondsFromString(item['duration_s'])
            except: duration = 0
            try: date = Datetime.ParseDate(item['contentDate_dt'])
            except: date = Datetime.Now()
            oc.add(EpisodeObject(
                url = item_url, 
                show = show, 
                title = title, 
                thumb = Resource.ContentsOfURLWithFallback(url=thumb),
                summary = summary, 
                season = season, 
                index = episode, 
                duration = duration, 
                originally_available_at = date
            ))

    if json['response']['start']+10<json['response']['numFound']:
        oc.add(NextPageObject(key=Callback(Search, title='Search', url=url, search_type=search_type, start=start+10),
            title =  L("Next Page ...")
        ))
    
    if len(oc) < 1:
        return ObjectContainer(header="Empty", message="There are no results to list.")
    else:
        return oc
####################################################################################################
# This function pulls the list of json feeds from a manifest
@route(PREFIX + '/getfeedlist')
def GetFeedList(url):
    
    feed_list = []
    # In case there is an issue with the manifest URL, we then try just pulling the manifest data
    try: content = HTTP.Request(url, cacheTime=CACHE_1DAY).content
    except: content = ''
    if content:
        try: zone_list = JSON.ObjectFromURL(RE_MANIFEST_URL.search(content).group(1))['manifest']['zones']
        except:
            try:
                zone_data = RE_MANIFEST_FEED.search(content).group(1)
                zone_list = JSON.ObjectFromString(zone_data)['manifest']['zones']
            except: zone_list = []
    
        for zone in zone_list:
            if zone in ('header', 'footer', 'ads-reporting', 'ENT_M171'):
                continue
            json_feed = zone_list[zone]['feed']
            feed_list.append(json_feed)
            #Log('the value of feed_list is %s' %feed_list)

    return feed_list
