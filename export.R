require(RSQLite)
require(dplyr)

con = dbConnect(drv = RSQLite::SQLite(), dbname = "bib.db")
checked = dbGetQuery(con, "select count(*) from species where checked")
total = dbGetQuery(con, "select count(*) from species")
pubs = dbGetQuery(con, "select * from publications")

cat(paste0("Checked ", checked, " species of ", total, "."))
cat(paste0("Found ", nrow(pubs), " publications."))

result <- pubs %>%
  group_by(uid, title) %>%
  summarise(species = paste(species, collapse=", ")) %>%
  arrange(uid)
write.csv(result, "publications.csv", row.names = FALSE)