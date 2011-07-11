import urlgrab
import json
import os
from operator import itemgetter
from urlparse import urljoin
from BeautifulSoup import BeautifulSoup
from urllib import quote_plus
from shutil import move

import email.mime, smtplib, email.mime.application
from settings import *

def rewriter(attr, tags, outPath, base):
	for item in tags:
		try:
			url = item[attr]
		except KeyError:
			continue # skip
		url = urljoin(base, url)
		print "rewriting", url
		try:
			data = cache.get(url, max_age=-1)
			if url.find("?")!=-1:
				url = url[:url.find("?")]
			ext = os.path.splitext(url)[1]
			imgPath = os.path.join(outPath, data.hash())+ext
			open(imgPath, "wb").write(data.read())
			item[attr] = data.hash()+ext
		except urlgrab.URLTimeoutError,e:
			continue # ignore

def generateMobi(url):
	data = cache.get(url, max_age=-1)
	hash = data.hash()
	outPath = os.path.abspath(os.path.join(cache.cache, hash))
	print outPath
	if not os.path.exists(outPath):
		os.mkdir(outPath)
	mobi = os.path.join(outPath, "%s.mobi"%hash)
	print mobi
	if not os.path.exists(mobi):
		raw = data.read()
		if data.getmime() in (["text", "html"], ["application", "xhtml+xml"]):
			# script tags make beautiful soup unhappy
			while raw.lower().find("<script")!=-1:
				raw = raw[:raw.lower().find("<script")]+raw[raw.lower().find("</script>")+9:]

			try:
				soup = BeautifulSoup(raw)
			except:
				return (-1, mobi)
			rewriter("src", soup.findAll("img"), outPath, data.url)
			rewriter("href", soup.findAll("link", rel="stylesheet"), outPath, data.url)
			open(os.path.join(outPath, "index.html"), "wb").write(str(soup))

			cmd = "ebook-convert index.html %s.mobi --enable-heuristics --output-profile kindle -v -v --max-levels=0 --no-inline-toc --mobi-ignore-margins" %hash
		
		elif data.getmime() == ["application", "pdf"]:
			open(os.path.join(outPath, "%s.pdf"%hash), "wb").write(raw)
			cmd = "ebook-convert %s.pdf %s.mobi --enable-heuristics --output-profile kindle" %(hash, hash)

		else:
			raise Exception, data.getmime()

		current = os.getcwd()
		os.chdir(outPath)
		print "converting"
		ret = os.system(cmd)
		os.chdir(current)
		return (ret, mobi)
	else:
		return (0, mobi)

def getPage(url):
	(ret, mobi) = generateMobi(url)
	if ret != 0: # try alternate url
		alturl = "http://www.skweezer.com/s.aspx?q=%s"%quote_plus(url)
		print alturl
		(ret, newmobi) = generateMobi(alturl)
		assert ret == 0, ret
		move(newmobi, mobi)
	assert os.path.exists(mobi), mobi

	msg = email.mime.Multipart.MIMEMultipart()
	msg["From"] = srcEmail
	msg["To"] = destEmail
	doc = email.mime.application.MIMEApplication(open(mobi,"rb").read())
	doc.add_header("Content-Disposition", "attachment", filename=os.path.basename(mobi))
	msg.attach(doc)

	s = smtplib.SMTP(server, port)
	if username!= None:
		s.ehlo()
		s.starttls()
		s.ehlo()
		s.login(username, password)
	s.sendmail(srcEmail, destEmail, msg.as_string())
	s.close()

def parsePages():
	try:
		done = json.loads(open(complete).read())
	except (IOError, EOFError):
		done = []

	raw = open(pages).read()
	raw = raw[raw.find("{"):raw.rfind("}")+1]
	try:
		data = json.loads(raw)["pages"]
	except ValueError:
		print "No valid 'pages' available yet"
		return

	for page in sorted(data, key=itemgetter("date")):
		print page
		url = page["url"]
		url = url[url.find("http"):] # fix Tweet shares which don't necessarily start with the url...

		if url in done:
			continue

		getPage(url)

		done.append(url)
		json.dump(done, open(complete, "wb"))

if __name__ == "__main__":
	import sys

	cache = urlgrab.Cache()

	if len(sys.argv)>1:
		for url in sys.argv[1:]:
			getPage(url)
		sys.exit(0)

	path = os.path.expanduser(path)
	complete = os.path.join(path, "complete")
	pages = os.path.join(path, "pages")

	parsePages()

	print "waiting for change..."

	import pyinotify

	wm = pyinotify.WatchManager()  # Watch Manager
	mask = pyinotify.ALL_EVENTS

	class EventHandler(pyinotify.ProcessEvent):
		def process_IN_CREATE(self, event):
			parsePages()

		def process_IN_MODIFY(self, event):
			parsePages()

		def process_IN_MOVED_TO(self, event):
			parsePages()

	handler = EventHandler()
	notifier = pyinotify.Notifier(wm, handler)
	wdd = wm.add_watch(path, mask, rec=True)

	notifier.loop()
