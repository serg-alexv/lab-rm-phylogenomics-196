suppressPackageStartupMessages({
  library(ape)
  library(phangorn)
  library(ggplot2)
  library(ggtree)
  library(svglite)
})

root <- "/work"
treefile <- file.path(root, "results", "stage06_figure", "primary196_host_tree.nwk")
matfile <- file.path(root, "results", "stage05_curated", "rm_type_presence_absence.tsv")
labfile <- file.path(root, "results", "stage06_figure", "tree_tip_display_labels.tsv")
out <- file.path(root, "results", "stage06_supp_nonmid_vibrant_true_arcs")
dir.create(out, recursive=TRUE, showWarnings=FALSE)

tree0 <- read.tree(treefile)
tree_sqrt <- tree0
if (is.null(tree_sqrt$edge.length)) stop("Tree has no branch lengths")
tree_sqrt$edge.length <- sqrt(pmax(tree_sqrt$edge.length, 0))

mat <- read.delim(matfile, sep="\t", check.names=FALSE, stringsAsFactors=FALSE, na.strings="__NO_NA__")
lab <- read.delim(labfile, sep="\t", check.names=FALSE, stringsAsFactors=FALSE, na.strings="__NO_NA__")

types <- c("Type_I","Type_II","Type_III","Type_IV")
stopifnot(
  length(tree0$tip.label) == 196,
  all(c("genome", types) %in% names(mat)),
  all(c("assembly_id","display_label","figure_genus") %in% names(lab)),
  setequal(tree0$tip.label, mat$genome),
  setequal(tree0$tip.label, lab$assembly_id)
)

lab$figure_genus[lab$assembly_id == "GCF_900240275.1"] <- "Limosilactobacillus"
lab <- lab[match(tree0$tip.label, lab$assembly_id), ]
mat <- mat[match(tree0$tip.label, mat$genome), ]

nt <- length(tree0$tip.label)
ng <- rep("Backbone", nt + tree0$Nnode)
ng[1:nt] <- lab$figure_genus
for (n in (nt+1):(nt+tree0$Nnode)) {
  d <- phangorn::Descendants(tree0, n, type="tips")[[1]]
  u <- unique(lab$figure_genus[d])
  ng[n] <- if (length(u) == 1) u else "Backbone"
}

genera <- sort(unique(lab$figure_genus))
gcols <- c(
  "Lacticaseibacillus"="#E11D48",
  "Lactiplantibacillus"="#E67700",
  "Lactobacillus"="#F4C430",
  "Lactococcus"="#9ACD32",
  "Leuconostoc"="#1F6B3A",
  "Limosilactobacillus"="#00A6A6",
  "Oenococcus"="#1098F7",
  "Pediococcus"="#1E40AF",
  "Streptococcus"="#A855F7",
  "Weissella"="#E649C1"
)
missing_pal <- setdiff(genera, names(gcols))
if(length(missing_pal)) stop("Missing genus palette entries: ", paste(missing_pal, collapse=", "))
branchcols <- c(gcols, "Backbone"="#000000")

tn <- c(
  Type_I="Type I",
  Type_II="Type II (incl. IIG)",
  Type_III="Type III",
  Type_IV="Type IV"
)
fills <- c(
  "Type I"="#009E73",
  "Type II (incl. IIG)"="#E69F00",
  "Type III"="#6C63B5",
  "Type IV"="#CC79A7",
  "Not detected"="#FFFFFF",
  "Unknown / NA"="#BDBDBD"
)
filllevels <- names(fills)

layoutdata <- function(tx, clad) {
  p <- ggtree(tx, layout="rectangular", branch.length=if(clad) "none" else "branch.length")
  d <- p$data
  d$r <- d$x / max(d$x, na.rm=TRUE)
  d$theta <- 2*pi*(d$y - 0.5)/nt
  d
}

edgepaths <- function(d, steps=48) {
  z <- list()
  k <- 1
  for(i in seq_len(nrow(d))) {
    ch <- d$node[i]
    pa <- d$parent[i]
    if(is.na(pa) || pa == ch) next
    j <- match(pa, d$node)
    pr <- d$r[j]
    cr <- d$r[i]
    pt <- d$theta[j]
    ct <- d$theta[i]
    delta <- ((ct - pt + pi) %% (2*pi)) - pi
    aa <- seq(pt, pt + delta, length.out=steps)
    rr <- rep(pr, length(aa))
    ar <- data.frame(x=rr*cos(aa), y=rr*sin(aa))
    nrad <- max(2, ceiling(steps/4))
    rseq <- seq(pr, cr, length.out=nrad)
    rad <- data.frame(x=rseq*cos(ct), y=rseq*sin(ct))
    q <- rbind(ar, rad[-1,])
    q$edge_id <- k
    q$branch_genus <- ng[ch]
    z[[k]] <- q
    k <- k + 1
  }
  do.call(rbind, z)
}

coerce_state <- function(v) {
  ch <- as.character(v)
  ch[is.na(ch) | ch==""] <- "NA"
  ifelse(ch %in% c("1","1.0","TRUE","T"), 1L,
         ifelse(ch %in% c("NA","-1"), -1L, 0L))
}

ringpolys <- function(d) {
  td <- d[d$isTip, c("label","theta")]
  ix <- match(td$label, mat$genome)
  base <- 1.025
  rw <- 0.025
  gap <- 0.006
  half <- pi/nt*0.92
  z <- list()
  k <- 1
  for(i in seq_len(nrow(td))) {
    for(j in seq_along(types)) {
      tp <- types[j]
      rin <- base + (j-1)*(rw+gap)
      rout <- rin + rw
      aa <- seq(td$theta[i]-half, td$theta[i]+half, length.out=12)
      x <- c(rout*cos(aa), rev(rin*cos(aa)))
      y <- c(rout*sin(aa), rev(rin*sin(aa)))
      st <- coerce_state(mat[[tp]][ix[i]])
      fc <- if(st == 1L) tn[[tp]] else if(st == -1L) "Unknown / NA" else "Not detected"
      z[[k]] <- data.frame(x=x, y=y, poly=k, fill_class=fc)
      k <- k + 1
    }
  }
  do.call(rbind, z)
}

render <- function(tx, clad, stem) {
  cat("START ", stem, "\n", sep="")
  flush.console()
  d <- layoutdata(tx, clad)
  ep <- edgepaths(d, 48)
  rp <- ringpolys(d)
  p <- ggplot() +
    geom_path(
      data=ep,
      aes(x=x, y=y, group=edge_id, color=branch_genus),
      linewidth=0.62, lineend="round", linejoin="round"
    ) +
    geom_polygon(
      data=rp,
      aes(x=x, y=y, group=poly, fill=fill_class),
      colour="#D0D0D0", linewidth=0.05
    ) +
    scale_color_manual(
      values=branchcols,
      breaks=genera,
      name="Branch genus",
      guide=guide_legend(override.aes=list(linewidth=1.45))
    ) +
    scale_fill_manual(
      values=fills,
      breaks=filllevels,
      name="R-M annotation"
    ) +
    coord_equal(xlim=c(-1.18,1.18), ylim=c(-1.18,1.18), clip="off") +
    theme_void() +
    theme(
      plot.title=element_blank(),
      legend.position="right",
      legend.title=element_text(size=11, face="bold"),
      legend.text=element_text(size=10),
      legend.key.width=grid::unit(9,"mm"),
      legend.key.height=grid::unit(5.5,"mm"),
      legend.spacing.y=grid::unit(1.5,"mm")
    )
  ggsave(file.path(out,paste0(stem,".svg")), p, width=12, height=12, device=svglite::svglite, bg="white")
  ggsave(file.path(out,paste0(stem,".pdf")), p, width=12, height=12, device=cairo_pdf, bg="white")
  ggsave(file.path(out,paste0(stem,".png")), p, width=12, height=12, dpi=400, bg="white")
  cat("DONE ", stem, "\n", sep="")
  flush.console()
}

render(tree0, TRUE, "supp_original_unrooted_cladogram_true_arcs48_vibrant")
render(tree_sqrt, FALSE, "supp_original_unrooted_sqrt_phylogram_true_arcs48_vibrant")

cat("STATUS=SUPP_NONMID_COMPLETE\n")
cat("files=", length(list.files(out)), "\n", sep="")
cat("output_dir=", out, "\n", sep="")
