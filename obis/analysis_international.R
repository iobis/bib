require(RSQLite)
library(DBI)
require(dplyr)
library(reshape2)

con <- dbConnect(RSQLite::SQLite(), "wos.db")
center <- read.csv("country_centroids_all.csv", na.strings = "", stringsAsFactors = FALSE)
center <- center %>% select(LAT, LONG, SHORT_NAME, continent)
res <- dbSendQuery(con, "select * from wos")
aff <- dbFetch(res)
refs <- unique(aff$brefid)
aff <- left_join(aff, center, by = c("country" = "SHORT_NAME"))

pubs <- aff %>% group_by(brefid) %>% summarize(countries = length(unique(country)), continents = length(unique(continent)))

nrow(pubs)
nrow(pubs %>% filter(countries > 1))
nrow(pubs %>% filter(continents > 1))
