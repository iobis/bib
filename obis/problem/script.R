require(ggplot2)
require(RColorBrewer)
require(ggplot2)
require(dplyr)
library(ggraph)
library(igraph)

### data

load("relationships.dat")
load("vertices.dat")
load("hierarchy.dat")

### plot

mygraph <- graph_from_data_frame(hierarchy, vertices = vertices)

con_from <- match(relationships$from, vertices$name)
con_to <- match(relationships$to, vertices$name)

ggraph(mygraph, layout = "dendrogram", circular = TRUE) + 
  geom_conn_bundle(data = get_con(from = con_from, to = con_to, value = relationships$count), aes(colour = value, width = value), tension = 2) + 
  scale_edge_colour_distiller(palette = "PuRd") +
  geom_node_point(aes(filter = leaf, colour = continent, size = count, alpha = 0.2)) +
  geom_node_text(aes(filter = leaf, label = name), size = 3, alpha = 1) +
  theme_void() +
  theme(
    legend.position = "none",
    panel.spacing = unit(c(2, 2, 2, 2), "cm"),
    plot.margin = unit(c(1, 1, 1, 1), "cm")
  )


