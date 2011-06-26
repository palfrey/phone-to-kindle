import urlgrab
import json
import os
from operator import itemgetter
from BeautifulSoup import BeautifulSoup

import email.mime, smtplib, email.mime.application
from settings import *

path = os.path.expanduser(path)
cache = urlgrab.Cache()

raw = open(path).read()
raw = raw[raw.find("{"):raw.rfind("}")+1]
pages = json.loads(raw)["pages"]

def rewriter(attr, tags, outPath):
	for item in tags:
		url = item[attr]
		print "rewriting", url
		data = cache.get(url, max_age=-1)
		ext = os.path.splitext(url)[1]
		if ext.find("?")!=-1:
			ext = ext[:ext.find("?")]
		imgPath = os.path.join(outPath, data.hash())+ext
		open(imgPath, "wb").write(data.read())
		item[attr] = data.hash()+ext

for page in sorted(pages, key=itemgetter("date")):
	print page
	data = cache.get(page["url"], max_age=-1)
	hash = data.hash()
	outPath = os.path.abspath(os.path.join(cache.cache, hash))
	mobi = os.path.join(outPath, "%s.mobi"%hash)
	print mobi
	if not os.path.exists(mobi):
		raw = data.read()
		
		# script tags make beautiful soup unhappy
		while raw.find("<script")!=-1:
			raw = raw[:raw.find("<script")]+raw[raw.find("</script>"):]

		open("dump", "wb").write(raw)

		soup = BeautifulSoup(raw)
		print outPath
		if not os.path.exists(outPath):
			os.mkdir(outPath)
		rewriter("src", soup.findAll("img"), outPath)
		rewriter("href", soup.findAll("link"), outPath)
		open(os.path.join(outPath, "index.html"), "wb").write(str(soup))

		os.chdir(outPath)
		cmd = "ebook-convert index.html %s.mobi --enable-heuristics --output-profile kindle" %hash
		ret = os.system(cmd)
		assert ret == 0, ret
		assert os.path.exists(mobi), mobi

	msg = email.mime.Multipart.MIMEMultipart()
	msg["From"] = srcEmail
	msg["To"] = destEmail
	doc = email.mime.application.MIMEApplication(open(mobi,"rb").read())
	doc.add_header("Content-Disposition", "attachment", filename=os.path.basename(mobi))
	msg.attach(doc)

	break

	s = smtplib.SMTP(server, port)
	if username!= None:
		s.ehlo()
		s.starttls()
		s.ehlo()
		s.login(username, password)
	s.sendmail(srcEmail, destEmail, msg.as_string())
	s.close()
	
	break
