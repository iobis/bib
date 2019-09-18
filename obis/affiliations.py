# sudo pip install --ignore-installed six

import requests
import re
from html.parser import HTMLParser
import html
import mechanize
import time
import sqlite3
import lib
import logging
from termcolor import colored

logging.basicConfig(level=logging.ERROR, format="%(asctime)s %(levelname)-8s %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("bib")
logger.setLevel(logging.DEBUG)

# config

search_url = "https://apps.webofknowledge.com"
base_url = "https://apps.webofknowledge.com/"
max_results = 3
log_to_html = True
reprint = True
offset = None

# fetch OBIS publications (brefid and title) from API and order by brefid

publications = requests.get("https://api.obis.org/publications/2019").json()["results"]
publications = sorted(publications, key=lambda p: p["brefid"])

# set up sqlite

conn = sqlite3.connect("affiliations.db")
lib.create_tables(conn)
c = conn.cursor()

# process

h = HTMLParser()
br = mechanize.Browser()
br.set_handle_robots(False)

for pub in publications:

    title = pub["standardtitle"]
    brefid = pub["brefid"]

    logger.info(colored(pub["standardtitle"], "white"))

    if offset is not None and id < offset:
        continue

    # clear publication and authors in sqlite

    lib.database_cleanup(conn, brefid)

    logger.debug("Opening search page")
    br.open(search_url)
    logger.debug("Received page, performing search")
    br.select_form(name="WOS_GeneralSearch_input_form")
    br["value(input1)"] = "\"" + lib.clean_title(title) + "\""
    res = br.submit()
    content = res.read().decode("utf-8")
    logger.debug("Received search results")

    if log_to_html:
        with open("log/" + str(brefid) + ".html", "w") as f:
            f.write(content)
            logger.debug("Response written to file " + str(brefid) + ".html")

    warnings = re.findall("STARTING A NEW SESSION", content)
    if len(warnings) > 0:
        logger.error("New session needed")
        br._ua_handlers["_cookies"].cookiejar.clear()
        br.open("http://www.webofknowledge.com", timeout=120)
        time.sleep(10)
        continue

    warnings = re.findall("To run more searches", content)
    if len(warnings) > 0:
        logger.error("Search history full")
        br._ua_handlers["_cookies"].cookiejar.clear()
        br.open("http://www.webofknowledge.com", timeout=120)
        logger.info("Sleeping for 10 seconds")
        time.sleep(10)
        continue

    for link in br.links():

        # alternative strategy
        if "full_record" in link.url:
            logger.debug("Found search result link: " + link.url)
            response = br.follow_link(link)
            page = response.read()

            if log_to_html:
                with open("log/" + str(brefid) + "_page.html", "w") as f:
                    f.write(content)
                    logger.debug("Response written to file " + str(brefid) + "_page.html")

            # authors

            authors = re.findall("author_name=(.*?)&amp", page)
            logger.info("Found " + str(len(authors)) + " authors")

            for author in authors:
                query = "insert into authors values (%s, '%s')" % (id, author.replace("'", ""))
                c.execute(query)
                conn.commit()

            # author addresses

            found = False

            addresses = re.findall("addressWOS(.*),(.*?)</a>", page)
            for a in addresses:
                address = a[1]

                for country in lib.countries:
                    n = address.lower().count(country.lower())
                    if n > 0:

                        logger.debug(country)
                        found = True

                        # insert record

                        query = "insert into wos values (%s, '%s')" % (id, country)
                        c.execute(query)
                        conn.commit()

                        break

                if not found:
                    logger.warning("No country found in \"" + address + "\"")

            # reprint address

            addresses = re.findall("fr_address_row2\">(.*?)<", page)

            for address in addresses:

                for country in lib.countries:
                    n = address.lower().count(country.lower())
                    if n > 0:

                        logger.info("Reprint address: " + country)
                        found = True

                        # insert record

                        if reprint and not found:
                            query = "insert into imis.wos values (%s, '%s')" % (id, country)
                            c.execute(query)
                            conn.commit()
                            logger.info("Used reprint address")

                        break

                if not found:
                    logger.warning("No country found in \"" + address + "\"")

c.close()
conn.close()
