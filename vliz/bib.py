import sqlite3
from suds.client import Client
import requests
import time
import csv
import sys

filename = "lists/Aphia_soortnamen_20181120.csv"
userQuery = "TS=%s AND AD=Belgi* AND PY=(2016-2019)"

# wsdl

wsdl_auth = "http://search.webofknowledge.com/esti/wokmws/ws/WOKMWSAuthenticate?wsdl"
wsdl_search = "http://search.webofknowledge.com/esti/wokmws/ws/WokSearchLite?wsdl"

# database

db = sqlite3.connect("bib.db")
db.execute("create table if not exists auth (key text)")
db.execute("create table if not exists species (name text, checked boolean)")
db.execute("create table if not exists publications (uid text, species text, title text)")
db.commit()

# create species list

with open(filename, "rb") as csvfile:
	reader = csv.reader(csvfile)
	for row in reader:
		sp = row[0].decode("utf8")
		print sp
		res = db.execute("select count(*) from species where name = ?", (sp,)).fetchone()[0]
		if res == 0:
			db.execute("insert into species values (?, ?)", (sp, False))
			db.commit()

# read species list

specieslist = db.execute("select name from species where not checked").fetchall()
specieslist = [element for tupl in specieslist for element in tupl]

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

#
#keys = db.execute("select key from auth").fetchone()
#if (keys is not None and len(keys) > 0):
#	key = keys[0]
#	print "Authentication key from database: %s" % key
#else:

# search

client = Client(wsdl_search)

for species in specieslist:

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

	print "%s - Looking for publications on %s" % (session_requests, species)

	search = species.replace("(", "")
	search = search.replace(")", "")
	query.userQuery = userQuery % search

	try:
		results = client.service.search(query, retrieve)

		if "records" in results:
			for result in results.records:

				uid = result.uid
				title = result.title[0][1][0]
				print "Publication %s for %s: %s" % (uid, species, title)

				db.execute("delete from publications where uid = ?", (uid,))
				db.execute("insert into publications values (?, ?, ?)", (uid, species, title))
				db.commit()

		db.execute("update species set checked = 1 where name = ?", (species,))
		db.commit()
	
	except Exception, e:
		print "Unexpected error: " + str(e)
		time.sleep(10)
		key = refreshkey()
		session_requests = 1

	time.sleep(1)
