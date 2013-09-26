TITLE = 'Rooster Teeth'
ART   = 'art-default.jpg'
ICON  = 'icon-default.png'

RE_ID              = Regex('(?<=id=)[0-9]+')
RE_MATH_EXPRESSION = Regex('a\.value *= *([0-9]+) *\+ *([0-9]+) *\* *([0-9]+)')

ITEMS_PER_PAGE = 10

BASE_URL = "http://roosterteeth.com"

HTTP_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/536.30.1 (KHTML, like Gecko) Version/6.0.5 Safari/536.30.1"

CHANNELS = [ 
	{
		'title': 	'Rooster Teeth',
		'url':		'http://roosterteeth.com',
		'thumb':	'http://s3.roosterteeth.com/assets/style/flashy/www/headerRand1.jpg',
		'desc':		'Rooster Teeth is the official home of Red vs. Blue, Achievement Hunter, Rooster Teeth Comics, and lots more.'
	},
	{
		'title': 	'Achievement Hunter',
		'url':		'http://ah.roosterteeth.com',
		'thumb':	'http://s3.roosterteeth.com/assets/style/flashy/ah/headerRand1.jpg',
		'desc':		'Showing you tips, tricks and walkthroughs to getting Achievements in the latest and greatest video games.'
	}
]

##########################################################################################
def Start():
	# Setup the default attributes for the ObjectContainer
	ObjectContainer.title1     = TITLE
	ObjectContainer.art        = R(ART)

	HTTP.CacheTime             = CACHE_1HOUR
	HTTP.Headers['User-agent'] = HTTP_USER_AGENT

##########################################################################################
def UpdateCookiesForAuthentication(url):
	needsUpdate = False

	try:
		req     = HTTP.Request(url, cacheTime = 0)
		content = req.content
		headers = req.headers
		
	except Ex.HTTPError, e:
		needsUpdate = True
		content     = e.content
		headers     = e.headers
	
	if needsUpdate:
		cookies = {}
		if 'Set-Cookie' in headers:
			cookies = headers['Set-Cookie']
			
		pageElement = HTML.ElementFromString(content)
		postData    = {}
		
		for item in pageElement.xpath("//*[@id = 'challenge-form']//input"):
		
			name = item.xpath("./@name")[0]
		
			if name in ['jschl_vc']:
				value          = item.xpath("./@value")[0]
				postData[name] = value

		Log(postData)

		for script in pageElement.xpath("//script[@type = 'text/javascript']"):			
			if script.xpath("./text()") != []:
				result = RE_MATH_EXPRESSION.search(script.xpath("./text()")[0]).groups()
				Log(result)
				if len(result) > 0:
					answer = int(result[0]) + (int(result[1]) * int(result[2])) + 16
					postData['jschl_answer'] = str(answer)
				
		ansURL = BASE_URL + pageElement.xpath("//*[@id = 'challenge-form']/@action")[0] + "?jschl_vc=" + postData['jschl_vc'] + "&jschl_answer=" + postData['jschl_answer']
	
		Thread.Sleep(5.850)
		
		try:
			req = HTTP.Request(
						ansURL, 
						headers = cookies,
						follow_redirects = False,
						cacheTime = 0
			)
			content = req.content
			headers = req.headers
			
		except Ex.RedirectError, e:
			headers = e.headers
		
		Log(headers)
		if 'Set-Cookie' in headers:
			HTTP.Headers['Cookie'] = headers['Set-Cookie']
	
##########################################################################################
@handler('/video/roosterteeth', TITLE, thumb = ICON, art = ART)
def MainMenu():
	UpdateCookiesForAuthentication(BASE_URL)

	menu = ObjectContainer()
	
	# Add all channels
	for channel in CHANNELS:
		menu.add(
			DirectoryObject(
				key = Callback(
						Shows, 
						title = channel["title"], 
						url = channel["url"],
						thumb = channel["thumb"]), 
				title = channel["title"], 
				thumb = channel["thumb"],
				summary = channel["desc"]
			)
		)		
	
	return menu
	
##########################################################################################
@route("/video/roosterteeth/Shows")
def Shows(title, url, thumb):
	oc = ObjectContainer()
	
	# Add shows by parsing the site
	shows       = []
	showNames   = []
	pageElement = HTML.ElementFromURL(url + '/archive/series.php')

	for item in pageElement.xpath("//*[@class = 'content']//a"):
		show = {}
		try:
			show["url"]  = item.xpath("./@href")[0]
			show["img"]  = item.xpath("./img/@src")[0]
			show["name"] = item.xpath("../..//b/text()")[0]
			show["desc"] = item.xpath("../..//span/text()")[0]
		
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
						base_url = url, 
						url = show["url"], 
						thumb = show["img"]), 
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
def Seasons(title, base_url, url, thumb):
	oc = ObjectContainer()
	
	pageElement = HTML.ElementFromURL(base_url + url)
	
	for item in pageElement.xpath("//*[contains(@class, 'seasonsBox')]//a"):
		url    = item.xpath("./@href")[0]
		season = item.xpath("./text()")[0]
		
		if 'all' in season.lower():
			continue
		
		oc.add(
			DirectoryObject(
				key = Callback(
						Videos, 
						title = title,
						base_url = base_url, 
						url = url, 
						thumb = thumb), 
				title = season,
				thumb = thumb
			)
		)

	if len(oc) < 1:
		return Videos( 
			title = title,
			base_url = base_url, 
			url = url, 
			thumb = thumb
		)
	else:			 
		return oc

##########################################################################################
@route("/video/roosterteeth/Videos", offset = int)
def Videos(title, base_url, url, thumb, offset = 0):
	oc = ObjectContainer()

	pageElement = HTML.ElementFromURL(base_url + url)
	
	counter = 0
	
	for item in pageElement.xpath("//a[contains(@class, 'videoChooseA')]"):
		if counter < offset:
			counter = counter + 1
			continue
		
		video = {}

		# Extract video ID
		videoURL = item.xpath("./@href")[0]
		m        = RE_ID.search(videoURL)
		videoID  = m.group(0)
			
		# Fetch JSON details(primarily to get URL of video object)
		data = JSON.ObjectFromURL('http://roosterteeth.com/archive/new/_loadEpisode.php?id=%s' % videoID)
			
		try:
			video["url"]  = HTML.ElementFromString(data['embed']['html']).xpath("//iframe/@src")[0]
		except:
			continue
			
		try:
			video["img"] = item.xpath(".//img/@src")[0]
		except:
			video["img"] = HTML.ElementFromString(data['embed']['details']).xpath("//img/@src")[0]
			
		video["name"] = data['title']
			
		try:
			video["desc"] = HTML.ElementFromString(data['embed']['details']).xpath("//*[contains(@class, 'Description')]/text()")[0]
		except:
			video["desc"] = None
			
		oc.add(
			EpisodeObject(
				url = video["url"],
				title = video["name"],
				show = title,
				summary = video["desc"],
				thumb = video["img"])
		)
		
		counter = counter + 1
		
		if counter - offset >= ITEMS_PER_PAGE:
			oc.add(
				NextPageObject(
					key = Callback(
						Videos, 
							title = title, 
							base_url = base_url, 
							url = url,
							thumb = thumb,
							offset = offset + ITEMS_PER_PAGE), 
							title = "More ...")
			)
			return oc
		
	for item in pageElement.xpath("//*[contains(@class, 'streamLoadMore')]"):
		if 'next' in item.xpath("./text()")[0].lower():
			nextPageUrl = item.xpath("./@href")[0]
	
			if len(oc) < 1:
				return Videos( 
					title = title,
					base_url = base_url, 
					url = nextPageUrl, 
					thumb = thumb,
					offset = 0
				) 
			else:
				oc.add(
					NextPageObject(
						key = Callback(
							Videos, 
								title = title, 
								base_url = base_url, 
								url = nextPageUrl,
								thumb = thumb,
								offset = 0), 
								title = "More ...")
				)
				break

	return oc
