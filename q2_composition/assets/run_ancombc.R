#!/usr/bin/env Rscript

# load libraries -----------------
suppressWarnings(library(phyloseq))
suppressWarnings(library(tidyverse))
suppressWarnings(library(ANCOMBC))
library("optparse")

# load arguments -----------------
cat(R.version$version.string, "\n")

option_list <- list(
  make_option("--inp_abundances_path", action = "store", default = "NULL",
              type = "character"),
  make_option("--inp_metadata_path", action = "store", default = "NULL",
              type = "character"),
  make_option("--formula", action = "store", default = "NULL",
              type = "character"),
  make_option("--p_adj_method", action = "store", default = "NULL",
              type = "character"),
  make_option("--prv_cut", action = "store", default = "NULL",
              type = "character"),
  make_option("--lib_cut", action = "store", default = "NULL",
              type = "character"),
  make_option("--group", action = "store", default = "NULL",
              type = "character"),
  make_option("--level_ordering", action = "store", default = "NULL",
              type = "character"),
  make_option("--struc_zero", action = "store", default = "NULL",
              type = "character"),
  make_option("--neg_lb", action = "store", default = "NULL",
              type = "character"),
  make_option("--tol", action = "store", default = "NULL", type = "character"),
  make_option("--max_iter", action = "store", default = "NULL",
              type = "character"),
  make_option("--conserve", action = "store", default = "NULL",
              type = "character"),
  make_option("--alpha", action = "store", default = "NULL",
              type = "character"),
  make_option("--global", action = "store", default = "NULL",
              type = "character"),
  make_option("--output", action = "store", default = "NULL",
              type = "character")
)
opt <- parse_args(OptionParser(option_list = option_list))

# Assign each arg (in positional order) to an appropriately named R variable
inp_abundances_path <- opt$inp_abundances_path
inp_metadata_path   <- opt$inp_metadata_path
formula             <- opt$formula
p_adj_method        <- opt$p_adj_method
prv_cut             <- as.numeric(opt$prv_cut)
lib_cut             <- as.numeric(opt$lib_cut)
group               <- opt$group
level_ordering      <- opt$level_ordering
struc_zero          <- as.logical(opt$struc_zero)
neg_lb              <- as.logical(opt$neg_lb)
tol                 <- as.numeric(opt$tol)
max_iter            <- as.numeric(opt$max_iter)
conserve            <- as.logical(opt$conserve)
alpha               <- as.numeric(opt$alpha)
global              <- as.logical(opt$global)
output              <- opt$output

# load data ----------------------
if (!file.exists(inp_abundances_path)) {
  errQuit("Input file path does not exist.")
} else {
  otu_file <- t(read.delim(inp_abundances_path, check.names = FALSE,
                            row.names = 1))
  }
if (!file.exists(inp_metadata_path)) {
  errQuit("Metadata file path does not exist.")
} else {
  metadata_file <- read.delim(inp_metadata_path, check.names = FALSE,
                              row.names = 1)
  }

otu <- otu_table(otu_file, taxa_are_rows = TRUE)
md <- sample_data(metadata_file)
row.names(md) <- rownames(metadata_file)

print(level_ordering)

# level ordering for model.matrix calculation
formula_vector  <- unlist(strsplit(formula, " "))
level_vector    <- unlist(strsplit(level_ordering, ", "))

# split the level_ordering param into each column and associated level order
if (!is.null(level_ordering)) {
  for (i in level_vector) {
    column          <- unlist(strsplit(i, "::"))[1]
    ordering_vector <- unlist(strsplit(i, "::"))[2]
    ordering_vector <- unlist(strsplit(ordering_vector, ","))
    ordering_vector <- gsub("\\'", "", ordering_vector)
    ordering_vector <- gsub("\\]", "", ordering_vector)
    ordering_vector <- gsub("\\[", "", ordering_vector)

    # handling formula input(s)
    for (j in formula_vector) {
      if (grepl(j, column, fixed = TRUE) == TRUE) {
        md[[j]] <- factor(md[[j]], levels = ordering_vector)
      }
    }
    # handling group input
    if ((!is.null(group)) && (all(group == column))) {
      md[[group]] <- factor(md[[group]], levels = ordering_vector)
    }
  }
}

# create phyloseq object for use in ancombc
data <- phyloseq(otu, md)

# analysis -----------------------
fit <- ancombc(data, formula, p_adj_method, prv_cut, lib_cut, group,
               struc_zero, neg_lb, tol, max_iter, conserve, alpha)

# extract stuff from the structure
feature_table <- fit$feature_table
zero_ind      <- fit$zero_ind
samp_frac     <- fit$samp_frac
resid         <- fit$resid
delta_em      <- fit$delta_em
delta_wls     <- fit$delta_wls

# result details
lfc      <- fit$res$lfc
se       <- fit$res$se
w        <- fit$res$W
p_val    <- fit$res$p_val
q_val    <- fit$res$q_val
diff_abn <- fit$res$diff_abn

# global test result details
global_w        <- fit$res_global$W
global_p_val    <- fit$res_global$p_val
global_q_val    <- fit$res_global$q_val
global_diff_abn <- fit$res_global$diff_abn

# ############################################################
# adding descriptors to each column
# colnames(feature_table) <- modify(colnames(feature_table),
#         function(x) {
#           return(paste(x, "feature_table", sep = "_"))})

# Concat everything into a distance matrix
# coeffs <- unlist(coeffs)
# diffs <- as.data.frame(x = coeffs)
# fit <- unlist(fit)
# diffs <- as.data.frame(x = fit)
# ############################################################

# Write distance matrix to file
# write.csv(feature_table, file = "feature_table.csv")
write.csv(zero_ind, file = "zero_ind.csv")
# write.csv(samp_frac, file = "samp_frac.csv")
# write.csv(resid, file = "resid.csv")
# write.csv(delta_em, file = "delta_em.csv")
# write.csv(delta_wls, file = "delta_wls.csv")

# write.csv(lfc, file = "lfc.csv")
# write.csv(se, file = "se.csv")
write.csv(w, file = "w.csv")
write.csv(p_val, file = "p_val.csv")
# write.csv(q_val, file = "q_val.csv")
# write.csv(diff_abn, file = "diff_abn.csv")

# write.csv(global_w, file = "global_w.csv")
# write.csv(global_p_val, file = "global_p_val.csv")
# write.csv(global_q_val, file = "global_q_val.csv")
# write.csv(global_diff_abn, file = "global_diff_abn.csv")

##### determine whether phyloseq object takes only the intersection of md/table
