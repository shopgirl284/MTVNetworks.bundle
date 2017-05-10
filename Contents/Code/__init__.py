TITLE = 'MTV Networks'
PREFIX = '/video/mtvnetworks'

ART = 'art-default.jpg'
ICON = 'icon-default.png'

RE_MANIFEST_URL = Regex('var triforceManifestURL = "(.+?)";', Regex.DOTALL)
RE_MANIFEST_FEED = Regex('var triforceManifestFeed = (.+?);\n', Regex.DOTALL)

ENT_LIST = ['ent_m100', 'ent_m150', 'ent_m151', 'ent_m112', 'ent_m116']

SHOWS_LIST = [
    {'title': 'MTV', 'base_url' : 'http://www.mtv.com', 'search_url' : 'http://relaunch-search.mtv.com/solr/mtv/select?q=%s&wt=json&start=', 'site_code' : '_mtv', 'icon' : 'mtv-icon.png'}, 
    {'title': 'VH1', 'base_url' : 'http://www.vh1.com', 'search_url' : 'http://search.vh1.com/solr/vh1/select?q=%s&wt=json&start=', 'site_code' : '_vh1', 'icon' : 'vh1-icon.png'}, 
    {'title': 'CMT', 'base_url' : 'http://www.cmt.com', 'search_url' : 'http://search.cmt.com/solr/cmt/select?q=%s&wt=json&start=', 'site_code' : '_cmt', 'icon' : 'cmt-icon.png'}, 
    {'title': 'LogoTV', 'base_url' : 'http://www.logotv.com', 'search_url' : 'http://search.logotv.com/solr/logo/select?q=%s&wt=json&start=', 'site_code' : '_logo', 'icon' : 'logo-icon.png'}, 
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
            oc.add(DirectoryObject(key=Callback(OtherVideos, title='Most Viewed Videos', url=feed), title='Most Viewed Videos', thumb=thumb))
    return oc
####################################################################################################
# This function pulls the various json feeds for video sections of a page 
# Used for Shows and Full Episode main pages since this channel requires a separate function for individual shows
@route(PREFIX + '/feedmenu')
def FeedMenu(title, url, thumb='', site_code=''):
    
    oc = ObjectContainer(title2=title)
    feed_list = GetFeedList(url)
    if feed_list<1:
        return ObjectContainer(header="Incompatible", message="Unable to find video feeds for %s." %url)
    
    for json_feed in feed_list:
        # Split feed to get ent code
        try: ent_code = json_feed.split('/feeds/')[1].split('/')[0]
        except: ent_code = ''
        ent_code = ent_code.split(site_code)[0]
        #Log('the value of final ent_code is %s' %ent_code)
        if ent_code not in ENT_LIST:
            continue
        json = JSON.ObjectFromURL(json_feed, cacheTime = CACHE_1DAY)
        try: title = json['result']['promo']['headline'].title()
        except: title = ''
        # Create menu for the ent_m151 - full episodes to produce videos and menu items for full episode feeds by show
        if ent_code=='ent_m151':
            oc.add(DirectoryObject(key=Callback(ShowVideos, title=title, url=json_feed),
                title=title,
                thumb=thumb
            ))
            for item in json['result']['shows']:
                oc.add(DirectoryObject(key=Callback(ShowVideos, title=item['title'], url=item['url']),
                    title=item['title'],
                    thumb=thumb
                ))
        # Create menu items for those that need to go to Produce Sections
        # ent_m100-featured show and ent_m150-all shows
        else:
            oc.add(DirectoryObject(key=Callback(ProduceSection, title=title, url=json_feed, result_type='shows'),
                title=title,
                thumb=thumb
            ))
            
    if len(oc) < 1:
        return ObjectContainer(header="Empty", message="There are no results to list.")
    else:
        return oc
#######################################################################################
# This function produces a list of feeds for the video sections for an individual shows
# Since the show main pages for these sites do not include json feeds that list all the full episodes or video clips,  
# we have to pull the show navigation feed, to get the video section URLs and then get the json feeds for those URLs
@route(PREFIX + '/showsections')
def ShowSections(title, url, thumb=''):
    
    oc = ObjectContainer(title2=title)
    base = url.split('.com')[0] + '.com'
    # In case there is an issue with the manifest URL, we then try just pulling the data
    try: content = HTTP.Request(url, cacheTime=CACHE_1DAY).content
    except: return ObjectContainer(header="Incompatible", message="This is an invalid %s." %url)
    try: pagenav_feed = JSON.ObjectFromURL(RE_MANIFEST_URL.search(content).group(1))['manifest']['zones']['header']['feed']
    except: 
        try: pagenav_feed = JSON.ObjectFromString(RE_MANIFEST_FEED.search(content).group(1)+'}}')['manifest']['zones']['header']['feed']
        except: return ObjectContainer(header="Incompatible", message="Unable to find video feeds for %s." %url)
        
    if not thumb:
        try: thumb = HTML.ElementFromString(content).xpath('//meta[@property="og:image"]/@content')[0].strip()
        except: thumb = ''

    json = JSON.ObjectFromURL(pagenav_feed, cacheTime = CACHE_1DAY)
    nav_list = json['result']['showNavigation']
    
    # Get the full episode and video clip feeds 
    for section in nav_list:
        if 'episode' in section or 'video' in section or 'film' in section:
            section_title = nav_list[section]['title'].title()
            section_url = nav_list[section]['url']
            if not section_url.startswith('http://'):
                section_url = base + section_url
            feed_list = GetFeedList(section_url)
            # There should only be one feed listed for these pages
            if 'ent_m112' in feed_list[0] or 'ent_m116' in feed_list[0]:
                oc.add(DirectoryObject(
                    key=Callback(ProduceSection, title=section_title, url=feed_list[0], result_type='filters', thumb=thumb),
                    title=section_title,
                    thumb = Resource.ContentsOfURLWithFallback(url=thumb)
                ))
        # Create video object for listed special full shows
        elif 'full special' in section:
            oc.add(VideoClipObject(
                url = nav_list[section]['url'], 
                title = nav_list[section]['title'], 
                thumb = Resource.ContentsOfURLWithFallback(url=thumb)
            ))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no video sections for this show." )
    else:
        return oc
#####################################################################################
# For Producing the sections from various json feeds
# This function can produce show lists, AtoZ show lists, and video filter lists
@route(PREFIX + '/producesections')
def ProduceSection(title, url, result_type, thumb='', alpha=''):
    
    oc = ObjectContainer(title2=title)
    (section_title, feed_url) = (title, url)
    json = JSON.ObjectFromURL(url)

    try: item_list = json['result'][result_type]
    except: 
        try: item_list = json['result']['data'][result_type]
        except: item_list = []
    # Create item list for individual sections of alphabet for the All listings
    if '/feeds/ent_m150' in feed_url and alpha:
        item_list = json['result'][result_type][alpha]
    for item in item_list:
        # Create a list of show sections
        if result_type=='shows':
            if '/feeds/ent_m150' in feed_url and not alpha:
                oc.add(DirectoryObject(
                    key=Callback(ProduceSection, title=item, url=feed_url, result_type=result_type, alpha=item),
                    title=item.replace('hash', '#').title()
                ))
            else:
                try: url = item['url']
                except: url = item['canonicalURL']
                # Skip bad show urls that do not include '/shows/' or events. If '/events/' there is no manifest.
                if '/shows/' not in url:
                    continue
                try: thumb = item['images'][0]['url']
                except: thumb = thumb
                if thumb.startswith('//'):
                    thumb = 'http:' + thumb
                oc.add(DirectoryObject(
                    key=Callback(ShowSections, title=item['title'], url=url, thumb=thumb),
                    title=item['title'],
                    thumb = Resource.ContentsOfURLWithFallback(url=thumb)
                ))
        # Create season sections for filters
        else:
            # Skip any empty sections
            try: count=item['subFilters'][1]['count']
            except: count=item['count']
            if  count==0:
                continue
            title=item['name']
            # Add All to Full Episodes section
            if 'Episode' in title:
                title='All ' +   title
            try: url=item['subFilters'][1]['url'] 
            except: url=item['url']
            oc.add(DirectoryObject(
                key=Callback(ShowVideos, title=title, url=url),
                title=title,
                thumb=Resource.ContentsOfURLWithFallback(url=thumb)
            ))
    
    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no results to list right now.")
    else:
        return oc
#######################################################################################
# This function produces the videos listed in json feed under items
@route(PREFIX + '/showvideos')
def ShowVideos(title, url):

    oc = ObjectContainer(title2=title)
    json = JSON.ObjectFromURL(url)
    try: videos = json['result']['items']
    except: 
        # Some full episode feeds now put media items in a data group
        try: videos = json['result']['data']['items']
        except: return ObjectContainer(header="Empty", message="There are no videos to list right now.")
    
    for video in videos:

        # some items are just ads so skip any without a URL
        try: vid_url = video['canonicalURL']
        except: continue

        # catch any bad links that get sent here
        if not ('/video-clips/') in vid_url and not ('/full-episodes/') in vid_url and not ('/episodes/') in vid_url:
            continue

        thumb = video['images'][0]['url']

        show = video['show']['title']
        try: episode = int(video['season']['episodeNumber'])
        except: episode = 0
        try: season = int(video['season']['seasonNumber'])
        except: season = 0
        
        try: unix_date = video['airDate']
        except:
            try: unix_date = video['publishDate']
            except: unix_date = unix_date = video['date']['originalPublishDate']['timestamp']
        if unix_date and unix_date.isdigit():
            date = Datetime.FromTimestamp(float(unix_date)).strftime('%m/%d/%Y')
            date = Datetime.ParseDate(date)
        else: date = None

        # Durations for clips have decimal points
        duration = video['duration']
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

    try: next_page = json['result']['nextPageURL']
    except: next_page = None

    if next_page and len(oc) > 0:

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
def OtherVideos(title, url, result_type='data'):

    oc = ObjectContainer(title2=title)
    try: videos = JSON.ObjectFromURL(url)['result'][result_type]['items']
    except: return ObjectContainer(header="Empty", message="There are no videos to list right now.")
    
    for video in videos:

        oc.add(EpisodeObject(
            url = video['url'], 
            show = video['header'],
            title = video['title'], 
            thumb = Resource.ContentsOfURLWithFallback(url=video['image']['url']),
            originally_available_at = Datetime.ParseDate(video['airDate']),
            duration = Datetime.MillisecondsFromString(video['duration'])
        ))

    if len(oc) < 1:
        return ObjectContainer(header="Empty", message="There are no videos available.")
    else:
        return oc
####################################################################################################
@route(PREFIX + '/searchsections')
def SearchSections(title, search_url, query, thumb):
    
    oc = ObjectContainer(title2=title)
    json_url = search_url %(String.Quote(query, usePlus = False))
    local_url = json_url + '0&defType=edismax'
    json = JSON.ObjectFromURL(local_url)
    search_list = []
    for item in json['response']['docs']:
        if item['bucketName_s'] not in search_list and item['bucketName_s'] not in ['Articles']:
            search_list.append(item['bucketName_s'])
    for item in search_list:
        oc.add(DirectoryObject(key = Callback(Search, title=item, url=json_url, search_type=item), title = item, thumb=thumb))

    return oc
####################################################################################################
@route(PREFIX + '/search', start=int)
def Search(title, url, start=0, search_type=''):

    oc = ObjectContainer(title2=title)
    local_url = '%s%s&fq=bucketName_s:%s&defType=edismax' %(url, start, search_type)
    json = JSON.ObjectFromURL(local_url)

    for item in json['response']['docs']:
        result_type = item['bucketName_s']
        title = item['title_t']
        full_title = '%s: %s' %(result_type, title)
        try: item_url=item['url_s']
        except: continue
        # For Shows
        if result_type=='Series':
            oc.add(DirectoryObject(key=Callback(ShowSections, title=item['title_t'], url=item_url, thumb=item['imageUrl_s']),
                title = full_title, thumb = Resource.ContentsOfURLWithFallback(url=item['imageUrl_s'])
            ))
        # For Episodes and Videos
        else:
            try: season = int(item['seasonNumber_s'].split(':')[0])
            except: season = 0
            try: episode = int(item['episodeNumber_s'])
            except: episode = 0
            try: show = item['seriesTitle_t']
            except: show = ''
            try: summary = item['description_t']
            except: summary = ''
            try: thumb = item['imageUrl_s']
            except: thumb = ''
            try: duration = Datetime.MillisecondsFromString(item['duration_s'])
            except: duration = 0
            try: date = Datetime.ParseDate(item['contentDate_dt'])
            except: date = Datetime.Now()
            oc.add(EpisodeObject(
                url = item_url, 
                show = show, 
                title = full_title, 
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
        try: zone_list = JSON.ObjectFromURL(RE_MANIFEST_URL.search(content).group(1))['manifest']['zoness']
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
