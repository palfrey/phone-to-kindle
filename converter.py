import urlgrab
import json
import os
from operator import itemgetter
from urlparse import urljoin
from lxml import etree
from BeautifulSoup import BeautifulSoup

import email.mime, smtplib, email.mime.application
from settings import *

path = os.path.expanduser(path)
complete = os.path.join(path, "complete")
path = os.path.join(path, "pages")
cache = urlgrab.Cache()

try:
	done = json.loads(open(complete).read())
except (IOError, EOFError):
	done = []

raw = open(path).read()
raw = raw[raw.find("{"):raw.rfind("}")+1]
pages = json.loads(raw)["pages"]

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

for page in sorted(pages, key=itemgetter("date")):
	print page
	url = page["url"]
	url = url[url.find("http"):] # fix Tweet shares which don't necessarily start with the url...
	
	if url in done:
		continue

	data = cache.get(url, max_age=-1)
	hash = data.hash()
	outPath = os.path.abspath(os.path.join(cache.cache, hash))
	mobi = os.path.join(outPath, "%s.mobi"%hash)
	print mobi
	if not os.path.exists(mobi):
		print outPath
		if not os.path.exists(outPath):
			os.mkdir(outPath)
		raw = data.read()
		if data.getmime() == ["text", "html"]:
			
			# script tags make beautiful soup unhappy
			while raw.find("<script")!=-1:
				raw = raw[:raw.find("<script")]+raw[raw.find("</script>")+9:]

			#soup = etree.HTML(raw)
			soup = BeautifulSoup(raw)
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
		assert ret == 0, ret
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

	done.append(url)
	json.dump(done, open(complete, "wb"))

