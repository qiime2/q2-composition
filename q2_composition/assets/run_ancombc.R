#!/usr/bin/env Rscript

# load libraries -----------------
suppressWarnings(library(phyloseq))
suppressWarnings(library(tidyverse))
suppressWarnings(library(ANCOMBC))
library('optparse')

# load arguments -----------------
cat(R.version$version.string, "\n")

option_list=list(
  make_option('--inp_abundances_path', action='store', default='NULL',
              type='character'),
  make_option('--inp_metadata_path', action='store', default='NULL',
              type='character'),
  make_option('--formula', action='store', default='NULL', type='character'),
  make_option('--p_adj_method', action='store', default='NULL',
              type='character'),
  make_option('--prv_cut', action='store', default='NULL', type='character'),
  make_option('--lib_cut', action='store', default='NULL', type='character'),
  make_option('--group', action='store', default='NULL', type='character'),
  make_option('--struc_zero', action='store', default='NULL',type='character'),
  make_option('--neg_lb', action='store', default='NULL', type='character'),
  make_option('--tol', action='store', default='NULL', type='character'),
  make_option('--max_iter', action='store', default='NULL', type='character'),
  make_option('--conserve', action='store', default='NULL', type='character'),
  make_option('--alpha', action='store', default='NULL', type='character'),
  make_option('--global', action='store', default='NULL', type='character'),
  make_option('--output', action='store', default='NULL', type='character'),
)
opt=parse_args(OptionParser(option_list=option_list))

# Assign each arg (in positional order) to an appropriately named R variable
inp_abundances_path <- opt$inp_abundances_path
inp_metadata_path   <- opt$inp_metadata_path
formula             <- opt$formula
p_adj_method        <- opt$p_adj_method
prv_cut             <- as.numeric(opt$prv_cut)
lib_cut             <- as.numeric(opt$lib_cut)
group               <- opt$group
struc_zero          <- as.logical(opt$struc_zero)
neg_lb              <- as.logical(opt$neg_lb)
tol                 <- as.numeric(opt$tol)
max_iter            <- as.numeric(opt$max_iter)
conserve            <- as.logical(opt$conserve)
alpha               <- as.numeric(opt$alpha)
global              <- as.logical(opt$global)
output              <- opt$global

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
