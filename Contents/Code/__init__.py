Login = SharedCodeService.roosterteeth.Login

TITLE = 'Rooster Teeth'
ART   = 'art-default.jpg'
ICON  = 'icon-default.png'
BASE_URL = 'http://roosterteeth.com'
HTTP_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/536.30.1 (KHTML, like Gecko) Version/6.0.5 Safari/536.30.1'

CHANNELS = [
    {
        'title': 'Rooster Teeth',
        'url': 'http://roosterteeth.com/show',
        'image': 'https://pbs.twimg.com/profile_images/699276126644936704/rCkvY0SS_400x400.jpg'
    },
    {
        'title': 'Achievement Hunter',
        'url': 'http://achievementhunter.roosterteeth.com/show',
        'image': 'https://pbs.twimg.com/profile_images/1834741417/283025_10150250994985698_268895495697_7664630_357027_n_400x400.jpg'
    },
    {
        'title': 'Funhaus',
        'url': 'http://funhaus.roosterteeth.com/show',
        'image': 'https://pbs.twimg.com/profile_images/563456577076596737/kTHggklU_400x400.png'
    },
    {
        'title': 'ScrewAttack',
        'url': 'http://screwattack.roosterteeth.com/show',
        'image': 'https://pbs.twimg.com/profile_images/735516290773704704/gJZmqxDZ_400x400.jpg'
    },
    {
        'title': 'The Know',
        'url': 'http://theknow.roosterteeth.com/show',
        'image': 'https://pbs.twimg.com/profile_images/639837776934891520/WA-rAvdP_400x400.png'
    },
    {
        'title': 'CowChop',
        'url': 'http://cowchop.roosterteeth.com/show',
        'image': 'https://pbs.twimg.com/profile_images/671530901734473728/CfowRP9t_400x400.png'
    }
]

##########################################################################################
def Start():
    # Setup the default attributes for the ObjectContainer
    ObjectContainer.title1     = TITLE
    ObjectContainer.art        = R(ART)

    HTTP.CacheTime  = CACHE_1HOUR
    HTTP.User_Agent = HTTP_USER_AGENT

###################################################################################################
def ValidatePrefs():
      
    if Prefs['login'] and Prefs['username'] and Prefs['password']:
        result = Login()
        
        if result:
            return ObjectContainer(
                header = "Login success",
                message = "You're now logged in!"
            )
        else:
            return ObjectContainer(
                header = "Login failure",
                message = "Please check your username and password"
            )

##########################################################################################
@handler('/video/roosterteeth', TITLE, thumb = ICON, art = ART)
def MainMenu():

    oc = ObjectContainer()
    
    oc.add(PrefsObject(title = "Preferences"))
    
    for channel in CHANNELS:
        oc.add(
            DirectoryObject(
                key = Callback(Shows, url=channel['url'], title=channel['title']),
                title = channel['title'],
                thumb = channel['image']
            )
        )
        
    return oc
    
##########################################################################################
@route('/video/roosterteeth/shows', TITLE, thumb = ICON, art = ART)
def Shows(url, title):

    oc = ObjectContainer(title2=title)

    shows       = []
    showNames   = []
        
    # Add shows by parsing the site
    element = HTML.ElementFromURL(url)

    for item in element.xpath("//*[@class = 'square-blocks']//a"):
        show = {}
        try:
            show["url"] = item.xpath("./@href")[0]
            show["img"] = item.xpath(".//img/@src")[0]
            
            if show["img"].startswith("//"):
                show["img"] = 'http:' + show["img"]
                
            show["name"] = item.xpath(".//*[@class='name']/text()")[0]
            show["desc"] = item.xpath(".//*[@class='post-stamp']/text()")[0]
        
            if not show["name"] in showNames:
                showNames.append(show["name"])
                shows.append(show)
        except:
            pass     
    
    sortedShows = sorted(shows, key=lambda show: show["name"])
    for show in sortedShows:

        if show["name"] in ('RT Sponsor Cut'):
            if not (Prefs['login'] and Prefs['username'] and Prefs['password']):
                continue

        oc.add(
            DirectoryObject(
                key = Callback(
                    EpisodeCategories, 
                    title = show["name"],
                    url = show["url"], 
                    thumb = show["img"]
                ), 
                title = show["name"],
                summary = show["desc"],
                thumb = show["img"]
            )
        )
    
    if len(oc) < 1:
        oc.header  = "Sorry"
        oc.message = "No shows found."
                     
    return oc

##########################################################################################
@route("/video/roosterteeth/EpisodeCategories")
def EpisodeCategories(title, url, thumb):

    oc = ObjectContainer(title2=title)
        
    oc.add(
        DirectoryObject(
            key = Callback(
                Recents, 
                title = "Recently Added Videos",
                url = url,
                thumb = thumb,
                xpath_string = "//*[@id='tab-content-trending']//*[@class='episodes--recent']"
            ), 
            title = "Recently Added Videos",
            thumb = thumb
        )
    )

    oc.add(
        DirectoryObject(
            key = Callback(
                Seasons, 
                title = title,
                url = url, 
                thumb = thumb
            ), 
            title = "Seasons",
            thumb = thumb
        )
    )

    return oc

##########################################################################################
@route("/video/roosterteeth/Seasons")
def Seasons(title, url, thumb):
    oc = ObjectContainer(title2="Seasons")
    
    content = HTTP.Request(url).content
    
    if 'Sponsor Only Content' in content:
        if not (Prefs['login'] and Prefs['username'] and Prefs['password']):
            return ObjectContainer(header="Sponsor Only", message="This show contains sponsor only content.\r\nPlease login to access this show")
    
    element = HTML.ElementFromString(content)
    
    try:
        art = element.xpath("//*[@class='cover-image']/@style")[0].split("(")[1].split(")")[0]
        
        if art.startswith("//"):
            art = 'http:' + art 
    except:
        art = None
    
    for item in element.xpath("//*[@id='tab-content-episodes']//*[@class='accordion']//label"):
        id = item.xpath("./@for")[0]
        
        if not id:
            continue
        
        try:
            season = id.split(" ")[1]
        except:
            season = None
        
        title = item.xpath(".//*[@class='title']/text()")[0]
        
        oc.add(
            DirectoryObject(
                key = Callback(
                    Items, 
                    title = title, 
                    url = url, 
                    thumb = thumb,
                    xpath_string = "//*[@id='tab-content-episodes']//*[@class='accordion']",
                    art = art,
                    id = id
                ), 
                title = title,
                thumb = thumb,
                art = art
            )
        )

    if len(oc) < 1:
        return Items(
            title = title,
            url = url,
            thumb = thumb,
            xpath_string = "//*[@id='tab-content-episodes']",
            art = art
        )
    else:
        return oc

##########################################################################################
@route("/video/roosterteeth/Recents")
def Recents(title, url, thumb, xpath_string):
    oc = ObjectContainer(title2=title)

    element = HTML.ElementFromURL(url)

    try:
        art = element.xpath("//*[@class='cover-image']/@style")[0].split("(")[1].split(")")[0]
        
        if art.startswith("//"):
            art = 'http:' + art 
    except:
        art = None
    
    episodes = []
    for item in element.xpath(xpath_string):
        
        for episode in item.xpath(".//*[@class='episode-blocks']//li"):
            url = episode.xpath(".//@href")[0]
            title = episode.xpath(".//*[@class='name']/text()")[0]
            thumb = episode.xpath(".//img/@src")[0]
            
            if thumb.startswith("//"):
                thumb = 'http:' + thumb
                
            try:
                index = int(title.split(" ")[1])
            except:
                index = None
                
            try:
                duration_string = episode.xpath(".//*[@class='timestamp']/text()")[0].strip()
                duration = ((int(duration_string.split(":")[0])*60) + int(duration_string.split(":")[1])) * 1000
            except:
                duration = None
            
            episodes.append(
                EpisodeObject(
                    url = url,
                    title = title,
                    thumb = thumb,
                    index = index,
                    duration = duration,
                    art = art
                )
            )
    
    if Prefs['sort'] == 'Latest First':
        for episode in episodes:
            oc.add(episode)   
    else:
        for episode in reversed(episodes):
            oc.add(episode)
        
    return oc



##########################################################################################
@route("/video/roosterteeth/Items")
def Items(title, url, thumb, xpath_string, art, id=None):
    oc = ObjectContainer(title2=title)

    element = HTML.ElementFromURL(url)
    
    episodes = []
    for item in element.xpath(xpath_string):
        if id:
            season_id = item.xpath(".//@id")[0]
             
            if id != season_id:
                continue
                
            try:
                season = int(id.split(" ")[1])
            except:
                season = None
        else:
            season = None
        
        for episode in item.xpath(".//*[@class='episode-blocks']//li"):
            url = episode.xpath(".//@href")[0]
            title = episode.xpath(".//*[@class='name']/text()")[0]
            thumb = episode.xpath(".//img/@src")[0]
            
            if thumb.startswith("//"):
                thumb = 'http:' + thumb
                
            try:
                index = int(title.split(" ")[1])
            except:
                index = None
                
            try:
                duration_string = episode.xpath(".//*[@class='timestamp']/text()")[0].strip()
                duration = ((int(duration_string.split(":")[0])*60) + int(duration_string.split(":")[1])) * 1000
            except:
                duration = None
            
            episodes.append(
                EpisodeObject(
                    url = url,
                    title = title,
                    thumb = thumb,
                    season = season,
                    index = index,
                    duration = duration,
                    art = art
                )
            )
    
    if Prefs['sort'] == 'Latest First':
        for episode in episodes:
            oc.add(episode)   
    else:
        for episode in reversed(episodes):
            oc.add(episode)
        
    return oc

