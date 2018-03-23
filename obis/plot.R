# look into this for pacific centered map: http://web.stanford.edu/~cengel/cgi-bin/anthrospace/great-circles-on-a-recentered-worldmap-in-ggplot

require(RSQLite)
require(ggplot2)
require(RColorBrewer)
library(DBI)
require(mapdata)
require(ggplot2)
require(dplyr)
library(reshape2)
library(cluster)
library(factoextra)
library(ggraph)
library(igraph)

### data prep

con <- dbConnect(RSQLite::SQLite(), "wos.db")

res <- dbSendQuery(con, "select country, count(*) as count from wos group by country order by count(*) desc")
counts <- dbFetch(res)

counts$country <- factor(counts$country, levels = counts$country)

center <- read.csv("country_centroids_all.csv", na.strings = "", stringsAsFactors = FALSE)
center <- center %>% select(LAT, LONG, SHORT_NAME, continent)

res <- dbSendQuery(con, "select * from wos")
aff <- dbFetch(res)

refs <- unique(aff$brefid)
aff <- left_join(aff, center, by = c("country" = "SHORT_NAME"))
locations <- aff %>% distinct(LONG, LAT)

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

pie <- function() {
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
}

map <- function() {
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
    coord_map()
}

### https://www.r-graph-gallery.com/310-custom-hierarchical-edge-bundling/
### -> not working yet

source("fixes.R")

uaff <- aff %>% distinct(brefid, country)
relationships <- uaff %>% left_join(uaff, by = "brefid") %>% select(brefid, from = country.x, to = country.y)
relationships <- relationships %>% distinct(brefid, from, to)
for (i in 1:nrow(relationships)) {
  if (relationships$from[i] > relationships$to[i]) {
    f <- relationships$from[i]
    relationships$from[i] <- relationships$to[i]
    relationships$to[i] <- f
  }
}
relationships <- relationships %>% distinct(brefid, from, to) %>% group_by(from, to) %>% summarize(count = n())
#relationships <- relationships[1:100,]
relationships <- relationships %>% filter(from != to)

countries <- data.frame(country = unique(c(relationships$from, relationships$to))) %>% arrange(country)
countries <- countries %>% left_join(center, by = c("country" = "SHORT_NAME")) %>% select(country, continent) %>% arrange(continent, country)
countries <- countries %>% left_join(counts, by = "country")
hierarchy <- countries %>% select(from = continent, to = country) %>% filter(!is.na(from)) %>% arrange(from, to)
or <- data.frame(from = "origin", to = unique(hierarchy$from)) %>% arrange(to)
hierarchy <- bind_rows(or, hierarchy)

v <- unique(c(hierarchy$from, hierarchy$to))
vertices <- data.frame(
  name = v,
  count = countries$count[match(v, countries$country)],
  continent = countries$continent[match(v, countries$country)],
  stringsAsFactors = FALSE)
myleaves <- which(is.na(match(vertices$name, hierarchy$from)))
nleaves <- length(myleaves)
vertices$id[myleaves] <- seq(1:nleaves)
vertices$angle <- 160 - 360 * vertices$id / nleaves
vertices$hjust <- ifelse(vertices$angle < -90 | vertices$angle > 90, 0, 1)
vertices$angle <- ifelse(vertices$angle < -90 | vertices$angle > 90, vertices$angle + 180, vertices$angle)

mygraph <- graph_from_data_frame(hierarchy, vertices = vertices)

con_from <- match(relationships$from, vertices$name)
con_to <- match(relationships$to, vertices$name)
con_to_order <- order(con_to)
con_to <- con_to[con_to_order]
con_from <- con_from[con_to_order]
relationships <- relationships[con_to_order,]

colors <- brewer.pal(9, "Paired")[c(1, 3, 2, 5, 7, 4)]

ggraph(mygraph, layout = "dendrogram", circular = TRUE) +
  theme_void() +
  theme(
    legend.position = "none",
    panel.spacing = unit(c(0, 0, 0, 0), "cm"),
    plot.margin = unit(c(0, 0, 0, 0), "cm"),
    panel.background = element_rect(fill = "transparent"),
    plot.background = element_rect(fill = "transparent")
  ) + 
  geom_conn_bundle(data = get_con2(from = con_from, to = con_to, value = relationships$count),
                   aes(colour = value, width = value, alpha = value), tension = 1) +
  #scale_edge_colour_gradient(low = "#db408c", high = "#77196e") +
  scale_edge_colour_gradient(low = "#db408c", high = "#db408c") +
  scale_edge_width(range = c(0.1, 5)) +
  scale_edge_alpha(range = c(0.2, 0.5)) +
  geom_node_point(aes(filter = leaf, x = x*1.05, y = y*1.05, colour = continent, size = count, alpha = 0.2)) +
  scale_colour_manual(values = colors) +
  scale_size_continuous(range = c(1, 16)) +
  geom_node_text(aes(x = x*1.15, y = y*1.15, filter = leaf, label = name, colour = continent, angle = angle, hjust = hjust), size = 3, alpha = 1) +
  expand_limits(x = c(-1.3, 1.3), y = c(-1.3, 1.3))

ggsave("pub_singlecolor.png", height = 10, width = 10, dpi = 600, bg = "transparent")
ggsave("pub_singlecolor.pdf", height = 10, width = 10, dpi = 600, bg = "transparent")
