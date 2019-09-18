import csv
import logging
from suds.client import Client

logger = logging.getLogger("bib")


def create_tables(conn):
    conn.execute("create table if not exists auth (key text)")
    conn.execute("create table if not exists species (name text, checked boolean)")
    conn.execute("create table if not exists publications (uid text, species text, title text)")
    conn.commit()


def populate_species(conn, filename):
    with open(filename, "rt") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            sp = row[0]
            logger.debug(sp)
            res = conn.execute("select count(*) from species where name = ?", (sp,)).fetchone()[0]
            if res == 0:
                conn.execute("insert into species values (?, ?)", (sp, False))
                conn.commit()


def refresh_key(conn, wsdl_auth):
    client = Client(wsdl_auth)
    key = client.service.authenticate()
    conn.execute("insert into auth values (?)", (key,))
    conn.commit()
    logger.info("Fetched authentication key from service: %s" % key)
    return key


def clean_term(term):
    search = term.replace("(", "")
    search = search.replace(")", "")
    search = search.replace(" and ", " \"and\" ")
    search = search.replace(" or ", " \"or\" ")
    search = search.replace("=", "")
    return search
