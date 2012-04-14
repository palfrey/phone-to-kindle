import email.mime, smtplib, email.mime.application
from settings import *
from sys import argv

for f in sys.argv[1:]:
	msg = email.mime.Multipart.MIMEMultipart()
	msg["From"] = srcEmail
	msg["To"] = destEmail
	doc = email.mime.application.MIMEApplication(open(f,"rb").read())
	doc.add_header("Content-Disposition", "attachment", filename=os.path.basename(f))
	msg.attach(doc)

	s = smtplib.SMTP(server, port)
	if username!= None:
		s.ehlo()
		s.starttls()
		s.ehlo()
		s.login(username, password)
	s.sendmail(srcEmail, destEmail, msg.as_string())
	s.close()

