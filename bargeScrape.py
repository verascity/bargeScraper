import requests
import hashlib
import time
import sys
import re
from datetime import date
from bs4 import BeautifulSoup

# bargeScrape.py
# Craftyviking 
# March 1st 2016 
# - A small script to generate DW friendly html for tread tracking. 

#User input 
#Fill in this 
#User info
USERNAME = 'yourusernamehere'
PASSWORD = 'yourpasspwhere'
# communities to scrape
coms = ["http://lastvoyageslogs.dreamwidth.org/", "http://lastvoyages.dreamwidth.org/","http://tlvgreatesthitsdw.dreamwidth.org/"]
comsTitle = ["Logs", "Network", "Greatest Hits"]
#Months to scrape for. If all are left blank the scraper will scrape only the current month.
startMonth = "" #The first month you want to scrape for, leave this blank if you want to set idividual months
endMonth = ""  #The last month you want to scrape for, leave this blank to end with current month
months = [""] #Individual months you want the scraper to scrape. Write as "2016/02" and seperate each by a comma ,
#Options
filename = "scrapeOutput.html" #Output file name
condensed = False #If you want the links to be hidden behind a cut for each month set this to True
displayName = "" #if your username shows up as different than the username you use to log in. For ex. your login has a - but your username has a _ 
tagsToCheck = [] #If you want a list of your character is not tagged. If you do not leave this empty.


#A few constants, leave these alone
loginurl = 'http://www.dreamwidth.org/login'
logs = []
logsComments = []
needToAddTags = []

def findComments(toplevelcomments, title,tags):
	for toplevelcomment in toplevelcomments:
		delTest = toplevelcomment.find(class_="comment-poster")
		if delTest is not None:
			poster = delTest.span['lj:user']
			commentUrl = toplevelcomment.find(class_="commentpermalink").a['href']
			if (poster == USERNAME.lower()):	
				#user posted a toplevel comment
				entry = {"title": title,
					"address": commentUrl}
				logsComments.append(entry)	
				checkForTags(tags, commentUrl, title)
			else:
				#check if user has treadjacked
				findThreadjack(commentUrl, title, tags)
	return
	
def findThreadjack(url, title, tags):
	commentThreadRaw = c.get(url)
	commentThreadSoup = BeautifulSoup(commentThreadRaw.content, "html.parser")
	comments = commentThreadSoup.find_all(class_="comment")
	for comment in comments:
		delTest = comment.find(class_="comment-poster")
		if delTest is not None:
			poster = delTest.span['lj:user']
			if (poster == USERNAME.lower()):	
				#user posted a has threadjacked
				hiddenUrl = comment.find(class_="comment-title").a
				if hiddenUrl is not None:
					commentUrl = hiddenUrl['href']
				else: 
					commentUrl = comment.find(class_="commentpermalink").a['href']
				entry = {"title": title,
						"address": commentUrl}
				logsComments.append(entry)
				checkForTags(tags, commentUrl, title)
				break
	return
def processOneComm(url):
	resetLists();
	#Get posts in a month 
	monthRaw = c.get(url)
	monthSoup = BeautifulSoup(monthRaw.content, "html.parser")
	posts = monthSoup.find_all(class_="entry-title")
	postsNum = len(posts)
	print("Checking " +str(postsNum)+ " posts and their comments.")
	for index in range(postsNum):
		post = posts[index]
		percet = str(int(index*100/postsNum))
		print("\r{} %".format(percet), end='')
		url = post.find("a")['href']
		fullPostRaw = c.get(url)
		fullPostSoup = BeautifulSoup(fullPostRaw.content, "html.parser")
		user = fullPostSoup.find(class_ = "ljuser")['lj:user']
		titleRaw = fullPostSoup.find(class_ = "entry-title").a['title']
		title = titleRaw.encode('charmap', 'ignore').decode("utf-8", "ignore")
		tagsRaw = fullPostSoup.find_all(rel="tag")
		tags = []
		for tag in tagsRaw:
			tags.append(tag.contents[0])
		if (user == USERNAME.lower()):
			#This entry was made by the user
			entry = {"title": title,
					"address": url}
			logs.append(entry)
			checkForTags(tags, url, title)
		else:
			#Check if user commented on this entry 			
			toplevelcomments = fullPostSoup.find_all(class_="comment-depth-1")
			findComments(toplevelcomments, title,tags)
			#Check if the entry has pages of comments
			pagesRaw = fullPostSoup.find(class_="page-links")
			if pagesRaw is not None: 
				pages = pagesRaw.find_all('a')
				for page in pages:
					pageCommentsRaw = c.get(page['href'])
					pageCommentsSoup = BeautifulSoup(pageCommentsRaw.content, "html.parser")
					toplevelcomments = pageCommentsSoup.find_all(class_="comment-depth-1")
					findComments(toplevelcomments, title,tags)
	print("\r{} %".format("100"), end='')
	print(" Done with this community")
	return
def resetLists():
	logs[:] = []
	logsComments[:] =[]
	return
def checkForTags(tags, url, title):
	for tag in tagsToCheck:
		if (tag not in tags):
			entry = {"title": title,
					"address": url}
			needToAddTags.append(entry)
	return
def login():
	page = c.get(loginurl)
	soup = BeautifulSoup(page.content, "html.parser")
	chal = soup.find(class_="lj_login_chal")['value']
	temp = hashlib.md5(PASSWORD.encode('utf-8')).hexdigest()
	temp2 = chal+temp
	response = hashlib.md5(temp2.encode('utf-8')).hexdigest()
	loginData = {"user" : USERNAME,
				"password" : "",
				"response" : response,
				"chal": chal}
	result = c.post(loginurl, data =loginData, headers = dict(referer = loginurl) )
	resultSoup = BeautifulSoup(result.content, "html.parser")
	logBtn = resultSoup.find(class_="lj_login_chal")
	if logBtn is not None:
		return False
	else:
		return True
def makeMonthArray( startMonth, endMonth, months):
	monthsToScrape = []
	#Remove empty months from 
	months = [month for month in months if month != ""]
	monthFormat = re.compile("20[0-1][0-9]/[0-1][0-9]")
	if len(months) > 0 :
		for month in months:
			if monthFormat.match(month) is None or len(month)!=7:
				sys.exit("A month does not have a valid format. Valid format is \"YYYY/MM\". Month is " +month)

		monthsToScrape = months
	else:
		today = date.today()
		if startMonth == "" :
			monthsToScrape.append(str(today.year)+"/"+str(today.month).zfill(2))
		else:
			if endMonth == "":
				endMonth = str(today.year)+"/"+str(today.month).zfill(2)
			if monthFormat.match(startMonth) is None or len(startMonth)!=7:
				sys.exit("Startmonth does not have a valid format. Valid format is \"YYYY/MM\". Startmonth is " +startMonth)
			if monthFormat.match(endMonth) is None or len(endMonth)!=7:
				sys.exit("Endmonth does not have a valid format. Valid format is \"YYYY/MM\". Endmonth is " +endMonth)
			monthToAdd = startMonth
			while monthToAdd < endMonth:
				monthsToScrape.append(monthToAdd)
				dateSplit = monthToAdd.split('/')
				year = int(dateSplit[0])
				month = int(dateSplit[1])
				if month +1 < 13 :
					monthToAdd = str(year) + "/"+str(month+1).zfill(2)
				else:
					monthToAdd = str(year +1) +"/01"
			monthsToScrape.append(endMonth)
	return monthsToScrape

	

#Main program to run
with requests.Session() as c:
	monthsToScrape = makeMonthArray(startMonth, endMonth, months)
	print("Logging in")
	login()
	print("Login complete. Begin Scraping")
	if displayName != "":
		USERNAME = displayName
	f = open(filename, 'w')
	for month in monthsToScrape:
		print("Scraping for " + month)
		f.write("<span style=\"font-size:x-large;\"><b>"+month+"</b></span></br>\n")
		if condensed:
			f.write("<cut>")
		for index in range(len(coms)):
			print("Scraping "+ comsTitle[index])
			f.write("<span style=\"font-size:large;\"><b>"+comsTitle[index]+"</b></span></br>\n")
			processOneComm(coms[index]+month)
			f.write("<b> Post by <user name="+USERNAME.lower()+"></b></br>\n")
			for log in logs:
				f.write("<a href=\""+log["address"]+"\">"+log["title"]+"</a></br>\n")
			f.write("<b> Comments by <user name="+USERNAME.lower()+"></b></br>\n")
			for log in logsComments:
				f.write("<a href=\""+log["address"]+"\">"+log["title"]+"</a></br>\n")
		if condensed:
			f.write("</cut>")
	if len(tagsToCheck) > 0:
		f.write("</br><span style=\"font-size:large;\"><b>Tags needed here:</b></span></br>\n")
		for tag in needToAddTags:
			f.write("<a href=\""+tag["address"]+"\">"+tag["title"]+"</a></br>\n")
		
	f.write("</br></br><small>This log list was created using bargescraper.py. For more infor <a href=\"http://ataashihunter.dreamwidth.org/3725.html\">click here</a></small>")
	f.close()
	print("Scrape complete. Outout saved to "+filename)