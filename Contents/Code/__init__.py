TITLE = 'Rooster Teeth'
ART   = 'art-default.jpg'
ICON  = 'icon-default.png'
BASE_URL = "http://roosterteeth.com"
HTTP_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/536.30.1 (KHTML, like Gecko) Version/6.0.5 Safari/536.30.1"

##########################################################################################
def Start():
    # Setup the default attributes for the ObjectContainer
    ObjectContainer.title1     = TITLE
    ObjectContainer.art        = R(ART)

    HTTP.CacheTime  = CACHE_1HOUR
    HTTP.User_Agent = HTTP_USER_AGENT
    
##########################################################################################
@handler('/video/roosterteeth', TITLE, thumb = ICON, art = ART)
def MainMenu():

    oc = ObjectContainer()
    
    shows       = []
    showNames   = []
        
    # Add shows by parsing the site
    element = HTML.ElementFromURL('http://roosterteeth.com/show')

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
        oc.add(
            DirectoryObject(
                key = Callback(
                    Seasons, 
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
@route("/video/roosterteeth/Seasons")
def Seasons(title, url, thumb):
    oc = ObjectContainer(title2 = title)
    
    content = HTTP.Request(url).content
    
    if 'Sponsor Only Content' in content:
        return ObjectContainer(header="Sorry", message="This show contains sponsor only content")
    
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
@route("/video/roosterteeth/Items")
def Items(title, url, thumb, xpath_string, art, id=None):
    oc = ObjectContainer()

    element = HTML.ElementFromURL(url)
    
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
            
            oc.add(
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
            
    return oc

