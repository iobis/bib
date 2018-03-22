getConnections <- function(layout, from, to, weight = NULL, mode = 'all') {
  from <- match(from, layout$.ggraph.orig_index)
  to <- match(to, layout$.ggraph.orig_index)
  if (is.null(weight)) {
    weight <- NA
  } else {
    weight <- getEdges(layout)[[weight]]
  }
  graph <- attr(layout, 'graph')
  to <- split(to, from)
  connections <- lapply(seq_along(to), function(i) {
    paths <- shortest_paths(graph, as.integer(names(to)[i]), to[[i]], mode = mode, weights = weight)$vpath
    lapply(paths, as.numeric)
  })
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

