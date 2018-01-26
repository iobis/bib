# sudo pip install --ignore-installed six

import requests
import re
import sys
import HTMLParser
import mechanize
import psycopg2
import time
import traceback
import sqlite3

reload(sys)
sys.setdefaultencoding("utf-8")

# config

searchurl = "https://apps.webofknowledge.com"
baseurl = "https://apps.webofknowledge.com/"
countries = ["Afghanistan", "Albania", "Algeria", "American Samoa", "Andorra", "Angola", "Anguilla", "Antarctica", "Antigua and Barbuda", "Argentina", "Armenia", "Aruba", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bermuda", "Bhutan", "Bolivia", "Bosnia and Herzegowina", "Botswana", "Bouvet Island", "Brazil", "British Indian Ocean Territory", "Brunei", "Brunei Darussalam", "Bulgaria", "Burkina Faso", "Burundi", "Cambodia", "Cameroon", "Canada", "Cape Verde", "Cayman Islands", "Central African Republic", "Chad", "Chile", "China", "Christmas Island", "Cocos (Keeling) Islands", "Colombia", "Comoros", "Congo", "Congo, the Democratic Republic of the", "Cook Islands", "Costa Rica", "Cote d'Ivoire", "Croatia (Hrvatska)", "Cuba", "Cyprus", "Czech Republic", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "East Timor", "Ecuador", "Egypt", "El Salvador", "England", "Equatorial Guinea", "Eritrea", "Estonia", "Ethiopia", "Falkland Islands (Malvinas)", "Faroe Islands", "Fiji", "Finland", "France", "France Metropolitan", "French Guiana", "French Polynesia", "French Southern Territories", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Gibraltar", "Greece", "Greenland", "Grenada", "Guadeloupe", "Guam", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Heard and Mc Donald Islands", "Holy See (Vatican City State)", "Honduras", "Hong Kong", "Hungary", "Iceland", "India", "Indonesia", "Iran (Islamic Republic of)", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Korea, Democratic People's Republic of", "Korea, Republic of", "Kuwait", "Kyrgyzstan", "Lao, People's Democratic Republic", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libyan Arab Jamahiriya", "Liechtenstein", "Lithuania", "Luxembourg", "Macau", "Macedonia, The Former Yugoslav Republic of", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Martinique", "Mauritania", "Mauritius", "Mayotte", "Mexico", "Micronesia, Federated States of", "Moldova, Republic of", "Monaco", "Mongolia", "Montserrat", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "Netherlands Antilles", "New Caledonia", "New Zealand", "Nicaragua", "Niger", "Nigeria", "Niue", "Norfolk Island", "Northern Mariana Islands", "Norway", "Oman", "Pakistan", "Palau", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Pitcairn", "Poland", "Portugal", "Puerto Rico", "Qatar", "Reunion", "Romania", "Russian Federation", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Seychelles", "Sierra Leone", "Singapore", "Slovakia (Slovak Republic)", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Georgia and the South Sandwich Islands", "Spain", "Sri Lanka", "St. Helena", "St. Pierre and Miquelon", "Sudan", "Suriname", "Svalbard and Jan Mayen Islands", "Swaziland", "Sweden", "Switzerland", "Syrian Arab Republic", "Taiwan, Province of China", "Tajikistan", "Tanzania, United Republic of", "Thailand", "Togo", "Tokelau", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Turks and Caicos Islands", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "USA", "United States Minor Outlying Islands", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Virgin Islands (British)", "Virgin Islands (U.S.)", "Wales", "Wallis and Futuna Islands", "Western Sahara", "Yemen", "Yugoslavia", "Zambia", "Zimbabwe"]
maxresults = 3
log = False
reprint = True
offset = None

# get publications from database

con = psycopg2.connect("dbname=imis user=imis password=imis host=obisdata.vliz.be connect_timeout=10")
cur = con.cursor()
query = "select brefid, sttitleclear, details -> 'anarec' -> 'StandardTitleSer' from imis.publications order by brefid"
cur.execute(query)
pubs = cur.fetchall()

# set up sqlite

conn = sqlite3.connect("wos.db")
c = conn.cursor()
c.execute("create table if not exists wos (brefid integer, country text)")
c.execute("create table if not exists authors (brefid integer, author text)")
conn.commit()

# offset

skip = False
if offset is not None:
    skip = True

# pocess

def cleanup(title):
    title = title.strip()
    if title.endswith("?"):
        title = title[:-1]
    return title

h = HTMLParser.HTMLParser()
br = mechanize.Browser()
br.set_handle_robots(False)

for pub in pubs:

    id = pub[0]
    title = pub[1]
    journal = pub[2]

    if skip:
        if id == offset:
            skip = False
        else:
            continue

    message = str(id) + " " + title
    if journal is not None:
        message = message + " (" + journal + ")"
    print message

    query = "delete from wos where brefid = " + str(id)
    c.execute(query)
    conn.commit()

    query = "delete from authors where brefid = " + str(id)
    c.execute(query)
    conn.commit()

    try:

        br.open(searchurl)
        br.select_form(name="WOS_GeneralSearch_input_form")
        br["value(input1)"] = "\"" + cleanup(title) + "\""
        res = br.submit()
        content = res.read()

        if log:
            f = open("log/" + str(id) + ".html", "w")
            f.write(content)
            f.close()

        warnings = re.findall("STARTING A NEW SESSION", content)
        if len(warnings) > 0:
            print "Error: new session needed"
            #sys.exit()
            br._ua_handlers['_cookies'].cookiejar.clear()
            br.open("http://www.webofknowledge.com")
            time.sleep(10)
            continue

        warnings = re.findall("To run more searches", content)
        if len(warnings) > 0:
            print "Error: search history full"
            #sys.exit()
            br._ua_handlers['_cookies'].cookiejar.clear()
            br.open("http://www.webofknowledge.com")
            time.sleep(10)
            continue

        urls = re.findall("full_record\.do\?[^\"]*", content)

        if len(urls) > 0 and len(urls) <= maxresults:
            full = h.unescape(baseurl + urls[0])
            r = requests.get(full)
            page = r.text

            if log:
                f = open("log/" + str(id) + "_page.html", "w")
                f.write(page)
                f.close()

            # authors

            authors = re.findall("author_name=(.*?)&amp", page)

            for author in authors:
                print "\t" + author
                query = "insert into authors values (%s, '%s')" % (id, author.replace("'", ""))
                c.execute(query)
                conn.commit()

            # author addresses

            found = False

            addresses = re.findall("addressWOS(.*),(.*?)</a>", page)
            for a in addresses:
                address = a[1]

                for country in countries:
                    n = address.lower().count(country.lower())
                    if n > 0:

                        print "\t" + country
                        found = True

                        # insert record

                        query = "insert into wos values (%s, '%s')" % (id, country)
                        c.execute(query)
                        conn.commit()

                        break

                if not found:
                    print "\tNo country found in \"" + address + "\""

            # reprint address

            addresses = re.findall("fr_address_row2\">(.*?)<", page)

            for address in addresses:

                for country in countries:
                    n = address.lower().count(country.lower())
                    if n > 0:

                        print "\tReprint address: " + country
                        found = True

                        # insert record

                        if reprint and not found:
                            query = "insert into imis.wos values (%s, '%s')" % (id, country)
                            c.execute(query)
                            conn.commit()
                            print "\tUsed reprint address"

                        break

                if not found:
                    print "\tNo country found in \"" + address + "\""

    except Exception, e:
        print "Error: " + str(e)
        traceback.print_exc()
        sys.exit()

cur.close()
con.close()
c.close()
conn.close()
