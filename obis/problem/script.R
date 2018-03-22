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
original <- function() {
mygraph <- graph_from_data_frame(hierarchy, vertices = vertices)
relationships <- relationships[-1,]
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



}


getConnections <- function(layout, from, to, weight = NULL, mode = 'all') {
  from <- match(from, layout$.ggraph.orig_index)
  to <- match(to, layout$.ggraph.orig_index)
  if (is.null(weight)) {
    weight <- NA
  } else {
    weight <- getEdges(layout)[[weight]]
  }
  graph <- attr(layout, 'graph')
  
  connections <- lapply(seq_along(to), function(i) {
    paths <- shortest_paths(graph, from[i], to[i], mode = mode, weights = weight)$vpath
    lapply(paths, as.numeric)
  })
  # to <- split(to, from)
  # connections <- lapply(seq_along(to), function(i) {
  #   paths <- shortest_paths(graph, as.integer(names(to)[i]), to[[i]], mode = mode, weights = weight)$vpath
  #   lapply(paths, as.numeric)
  # })
  unlist(connections, recursive = FALSE)
}

get_con2 <- function (from = integer(), to = integer(), paths = NULL, ...) 
{
  if (length(from) != length(to)) {
    stop("from and to must be of equal length")
  }
  function(layout) {
    if (length(from) == 0) 
      return(NULL)
    connections <- getConnections(layout, from, to)
    nodes <- as.data.frame(layout)[unlist(connections), ]
    nodes$con.id <- rep(seq_along(connections), lengths(connections))
    if (!is.null(paths)) {
      extra <- as.data.frame(layout)[unlist(paths), ]
      extra$con.id <- rep(seq_along(paths) + length(connections), 
                          lengths(paths))
      nodes <- rbind(nodes, extra)
    }
    
    # nodes <- do.call(cbind, c(list(nodes), lapply(list(...), rep, length.out = nrow(nodes)), list(stringsAsFactors = FALSE)))
    nodes <- do.call(cbind, c(list(nodes), lapply(list(...), function(x) x[nodes$con.id]),list(stringsAsFactors = FALSE)))
    structure(nodes, type = "connection_ggraph")
  }
}


plot <- function() {
  mygraph <- graph_from_data_frame(hierarchy, vertices = vertices)
  
  relationships <- relationships %>% filter(from != to)
  con_from <- match(relationships$from, vertices$name)
  con_to <- match(relationships$to, vertices$name)
  con_to_order <- order(con_to)
  con_to <- con_to[con_to_order]
  con_from <- con_from[con_to_order]
  relationships <- relationships[con_to_order,]
  count <- relationships$count
  ggraph(mygraph, layout = "dendrogram", circular = TRUE) + 
    geom_conn_bundle(data = get_con2(from = con_from, to = con_to, value = relationships$count), aes(colour = value, width = value), tension = 2) + 
    scale_edge_colour_distiller(palette = "PuRd") +
    geom_node_point(aes(filter = leaf, colour = continent, size = count, alpha = 0.2)) +
    geom_node_text(aes(filter = leaf, label = name), size = 3, alpha = 1) +
    theme_void() +
    theme(
      legend.position = "none",
      panel.spacing = unit(c(2, 2, 2, 2), "cm"),
      plot.margin = unit(c(1, 1, 1, 1), "cm")
    )
}
#plot()