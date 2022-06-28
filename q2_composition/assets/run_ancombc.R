#!/usr/bin/env Rscript

# load libraries -----------------
suppressWarnings(library(phyloseq))
suppressWarnings(library(tidyverse))
suppressWarnings(library(ANCOMBC))

# load arguments -----------------
cat(R.version$version.string, "\n")
args=commandArgs(TRUE)

inp_abundances_path <- args[[1]]
inp_metadata_path   <- args[[2]]
formula             <- args[[3]]
p_adj_method        <- args[[4]]
prv_cut             <- as.numeric(args[[5]])
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
if(!path.exists(inp_abundances_path)) {
  errQuit("Input file path does not exist.")
} else {
  otu_file=t(read.delim(inp_abundances_path, check.names=FALSE,
                            row.names=1))
  }
if(!path.exists(inp_metadata_path)) {
  errQuit("Metadata file path does not exist.")
} else {
  metadata_file=read.delim(inp_metadata_path, check.names=FALSE,
                              row.names=1)
  }
OTU=otu_table(otu_file, taxa_are_rows=TRUE)
MD=sample_data(metadata_file)
row.names(MD)=rownames(metadata_file)
data=phyloseq(OTU, MD)

# analysis -----------------------
fit=ancombc(data, formula, p_adj_method)

# extract multivariate regression coefficients from the structure
beta  <- fit$res$beta    # beta
se    <- fit$res$se      # standard error
w     <- fit$res$W       # test statistic
p_val <- fit$res$p_val   # p-value
q_val <- fit$res$q_val   # q-value

# adding descriptors to each column
colnames(beta) <- modify(colnames(beta),
        function(x){return(paste(x, 'beta', sep='_'))})
colnames(se) <- modify(colnames(se),
        function(x){return(paste(x, 'se', sep='_'))})
colnames(w) <- modify(colnames(w),
        function(x){return(paste(x, 'W', sep='_'))})
colnames(p_val) <- modify(colnames(p_val),
        function(x){return(paste(x, 'p-value', sep='_'))})
colnames(q_val) <- modify(colnames(q_val),
        function(x){return(paste(x, 'q-value', sep='_'))})

# Concat everything into a distance matrix
diffs=as.data.frame(cbind(beta, se, w, p_val, q_val))

# Write distance matrix to file
write.csv(diffs, file=output)
