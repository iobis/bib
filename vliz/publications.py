import sqlite3
import time
import lib
import logging
from termcolor import colored
from suds.client import Client

logging.basicConfig(level=logging.ERROR, format="%(asctime)s %(levelname)-8s %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("bib")
logger.setLevel(logging.DEBUG)

filename = "lists/WoRMS_english_vernaculars_marine_20190328.csv"
userQuery = "TS=%s AND AD=Belgi* AND PY=(2016-2019)"
populate = False

# wsdl

wsdl_auth = "http://search.webofknowledge.com/esti/wokmws/ws/WOKMWSAuthenticate?wsdl"
wsdl_search = "http://search.webofknowledge.com/esti/wokmws/ws/WokSearchLite?wsdl"

# database

conn = sqlite3.connect("publications.db")
lib.create_tables(conn)

# create species list

if populate:
    lib.populate_species(conn, filename)

# read species list

species_list = conn.execute("select name from species where not checked").fetchall()
species_list = [element for tupl in species_list for element in tupl]

# authenticate

session_requests = 0
key = lib.refresh_key(conn, wsdl_auth)

# search

client = Client(wsdl_search)

for species in species_list:

    session_requests = session_requests + 1

    if session_requests > 2500:
        key = lib.refresh_key(conn, wsdl_auth)
        session_requests = 1

    client.set_options(headers={"Cookie": "SID=" + key})
    query = client.factory.create("queryParameters")
    retrieve = client.factory.create("retrieveParameters")
    query.databaseId = "WOS"
    query.queryLanguage = "en"
    retrieve.firstRecord = 1
    retrieve.count = 100

    logger.info(colored("%s - Looking for publications on %s" % (session_requests, species), "white"))

    search = lib.clean_term(species)
    query.userQuery = userQuery % search

    try:
        results = client.service.search(query, retrieve)

        if "records" in results:
            for result in results.records:

                uid = result.uid
                title = result.title[0][1][0]
                logger.info(colored("Publication %s for %s: %s" % (uid, species, title), "green"))

                conn.execute("delete from publications where uid = ?", (uid,))
                conn.execute("insert into publications values (?, ?, ?)", (uid, species, title))
                conn.commit()

        conn.execute("update species set checked = 1 where name = ?", (species,))
        conn.commit()

    except Exception as e:
        logger.error("Unexpected error: " + str(e))
        time.sleep(10)
        key = lib.refresh_key(conn, wsdl_auth)
        session_requests = 1

    time.sleep(1)
