# look into this for pacific centered map: http://web.stanford.edu/~cengel/cgi-bin/anthrospace/great-circles-on-a-recentered-worldmap-in-ggplot

require(RSQLite)
require(ggplot2)
require(RColorBrewer)
library(DBI)

con <- dbConnect(RSQLite::SQLite(), "wos.db")

res <- dbSendQuery(con, "select country, count(*) as count from wos group by country order by count(*) desc")
counts <- dbFetch(res)

counts$country <- factor(counts$country, levels = counts$country)
ncolors <- 25

number_ticks <- function(n) { function(limits) pretty(limits, n) }

ggplot() + geom_bar(data = counts, aes(x = "", y = count, fill = country), stat = "identity", width = 3) +
  coord_polar("y", start = 0) +
  scale_fill_manual(values = c(colorRampPalette(brewer.pal(12, "Spectral"))(ncolors), rep("#cccccc", nrow(counts) - ncolors))) +
  xlab("") +
  ylab("") +
  scale_y_continuous(breaks = number_ticks(10)) +
  theme(
    axis.ticks = element_blank(),
    panel.grid.minor = element_blank(),
    panel.grid.major = element_line(colour="gray95"),
    panel.background = element_blank()
  ) +
  guides(fill = guide_legend(ncol = 3))

############ map

require(mapdata)
require(ggplot2)
require(dplyr)

center <- read.csv("country_centroids_all.csv", sep="\t")
center <- center %>% select(LAT, LONG, SHORT_NAME)

res <- dbSendQuery(con, "select * from wos")
aff <- dbFetch(res)

refs <- unique(aff$brefid)
aff <- left_join(aff, center, by = c("country" = "SHORT_NAME"))
locations <- aff %>% distinct(LONG, LAT)

#countries <- data.frame(country=unique(aff$country))
#left_join(countries, center, by=c("country" = "SHORT_NAME"))

connections <- data.frame(x=numeric(0), xend=numeric(0), y=numeric(0), yend=numeric(0))

for (ref in refs) {
  cdata <- aff %>% filter(brefid == ref) %>% distinct(country, LAT, LONG)
  if (nrow(cdata) > 1) {
    for (i in 1:(nrow(cdata)-1)) {
      for (j in (i + 1):nrow(cdata)) {
        connections <- rbind(connections, data.frame(x=cdata$LON[i], y=cdata$LAT[i], xend=cdata$LON[j], yend=cdata$LAT[j]))
      }
    }
  }
}

world <- map_data("world")
colour <- "#cc3300"
ggplot(world, aes(long, lat)) +
  geom_polygon(aes(group = group), fill = "gray90", color = "gray90") +
  labs(x = "", y = "") + theme(
    axis.line=element_blank(),
    axis.text.x=element_blank(),
    axis.text.y=element_blank(),
    axis.ticks=element_blank(),
    axis.title.x=element_blank(),
    axis.title.y=element_blank(),
    legend.position="none",
    panel.background=element_blank(),
    panel.border=element_blank(),
    panel.grid.major=element_blank(),
    panel.grid.minor=element_blank(),
    plot.background=element_blank()) +
  geom_segment(data=connections, aes(x=x, xend=xend, y=y, yend=yend), colour=colour, alpha=0.1) +
  geom_point(data=locations, aes(x=LONG, y=LAT), colour=colour, size=0.6) +
  #coord_map("ortho", orientation = c(41, -74, 0))
  #coord_map("ortho", orientation = c(41, 200, 0))
  #coord_map(orientation = c(90, 0, -100))
  coord_map()













