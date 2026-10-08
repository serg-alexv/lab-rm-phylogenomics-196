# SYNTHETIC_ONLY: evaluate selected expressions from the pinned installed PADLOC.
# Do not source its CLI or run HMM searches, system clustering or biology.
suppressMessages(library(dplyr))
suppressMessages(library(jsonlite))
args <- commandArgs(trailingOnly=TRUE)
stopifnot(length(args)==3)
source <- args[[1]]; fixtures_path <- args[[2]]; output <- args[[3]]
expected <- "d21ba942e80720d80027aa1740d756322560feaeb168bfa2890640d88950d4c0"
actual <- strsplit(system2("sha256sum", shQuote(source), stdout=TRUE), " +")[[1]][[1]]
stopifnot(identical(actual, expected))
program <- parse(file=source, keep.source=FALSE)
is_assignment <- function(x, name) is.call(x) && as.character(x[[1]]) %in% c("<-", "=") && identical(x[[2]], as.name(name))
functions <- Filter(function(x) is_assignment(x, "search_system"), as.list(program))
stopifnot(length(functions)==1)
body <- as.list(functions[[1]][[3]][[3]])[-1]
start <- which(vapply(body, function(x) is_assignment(x, "max_space"), logical(1)))
end <- which(vapply(body, function(x) is_assignment(x, "top_hits"), logical(1)))
stopifnot(length(start)==1, length(end)==1, start<end)
expressions <- body[start:end]
fixtures <- fromJSON(fixtures_path, simplifyVector=FALSE)
results <- lapply(fixtures$cases, function(case) {
  env <- new.env(parent=globalenv())
  env$system_param <- case$system_param
  env$merged_tbls <- bind_rows(case$native_rows)
  env$hmm_meta <- bind_rows(case$hmm_meta)
  env$include.crispr.arrays <- FALSE
  env$include.retron.ncrnas <- FALSE
  for (expression in expressions) eval(expression, envir=env)
  selected <- sort(as.character(env$top_hits$fixture_hit_id))
  stopifnot(identical(selected, sort(as.character(unlist(case$expected_hit_ids)))))
  list(case_id=case$case_id, selected_hit_ids=selected, expected_hit_ids=unlist(case$expected_hit_ids),
       status="PASS_INSTALLED_NATIVE_EXPRESSION_EQUIVALENCE_SYNTHETIC_ONLY")
})
write_json(list(status="PASS_ALL_INSTALLED_PADLOC_SELECTION_EXPRESSIONS_SYNTHETIC_ONLY",
                native_source_sha256=actual, native_source_path=source,
                selected_native_expression_count=length(expressions), cases=results,
                biological_HMM_searches=0, production_adoption="NOT_ADOPTED"), output,
           auto_unbox=TRUE, pretty=TRUE)
