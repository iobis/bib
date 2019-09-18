import sqlite3
from suds.client import Client
import requests
import time
import csv

userQuery = "TS=(OBIS) AND AD=Belgi* AND PY=(%s)"

# wsdl

wsdl_auth = "http://search.webofknowledge.com/esti/wokmws/ws/WOKMWSAuthenticate?wsdl"
wsdl_search = "http://search.webofknowledge.com/esti/wokmws/ws/WokSearchLite?wsdl"

# database

db = sqlite3.connect("bib.db")
db.execute("create table if not exists auth (key text)")
db.execute("create table if not exists publications (uid text, title text, year integer)")
db.commit()

# authenticate

session_requests = 0

def refreshkey():
	client = Client(wsdl_auth)
	key = client.service.authenticate()
	db.execute("insert into auth values (?)", (key,))
	db.commit()
	print "Fetched authentication key from service: %s" % key
	return key

key = refreshkey()

# search

client = Client(wsdl_search)

for year in range(2000, 2020):

	session_requests = session_requests + 1

	if session_requests > 2500:
		key = refreshkey()
		session_requests = 1

	client.set_options(headers = {"Cookie": "SID=" + key})
	query = client.factory.create("queryParameters")
	retrieve = client.factory.create("retrieveParameters")
	query.databaseId = "WOS"
	query.queryLanguage = "en"
	retrieve.firstRecord = 1
	retrieve.count = 100

	print "%s - Looking for publications for %s" % (session_requests, year)

	query.userQuery = userQuery % year
	print query.userQuery

	try:
		results = client.service.search(query, retrieve)

		if "records" in results:
			for result in results.records:

				uid = result.uid
				title = result.title[0][1][0]
				print "Publication %s: %s" % (uid, title)

				db.execute("delete from publications where uid = ?", (uid,))
				db.execute("insert into publications values (?, ?, ?)", (uid, title, year))
				db.commit()

	except Exception, e:
		print "Unexpected error: " + str(e)
		time.sleep(10)
		key = refreshkey()
		session_requests = 1

	time.sleep(1)
