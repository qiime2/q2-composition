#!/usr/bin/env Rscript
# load libraries -----------------
suppressWarnings(library(phyloseq))
suppressWarnings(library(tidyverse))
suppressWarnings(library(ANCOMBC))

# load arguments -----------------
cat(R.version$version.string, "\n")
args <- commandArgs(TRUE)

inp.abundances.path <- args[[1]]
inp.metadata.path   <- args[[2]]
formula             <- args[[3]]
p_adj_method        <- args[[4]]
zero_cut            <- as.numeric(args[[5]])
lib_cut             <- as.numeric(args[[6]])
group               <- args[[7]]
struc_zero          <- as.logical(args[[8]])
neg_lb              <- as.logical(args[[9]])
tol                 <- as.numeric(args[[10]])
max_iter            <- as.numeric(args[[11]])
conserve            <- as.logical(args[[12]])
alpha               <- as.numeric(args[[13]])
global              <- as.logical(args[[14]])
output              <- args[[15]]
# load data ----------------------
if(!path.exists(inp.abundances.path)) {
  errQuit("Input file path does not exist.")
} else {
  otu.file <- t(read.delim(inp.abundances.path, check.names=FALSE,
                            row.names=1))
  }
if(!path.exists(inp.metadata.path)) {
  errQuit("Metadata file path does not exist.")
} else {
  metadata.file <- read.delim(inp.metadata.path, check.names=FALSE,
                              row.names=1)
  }
OTU <- otu_table(otu.file, taxa_are_rows=TRUE)
MD <- sample_data(metadata.file)
row.names(MD) <- rownames(metadata.file)
data <- phyloseq(OTU, MD)
# analysis -----------------------
