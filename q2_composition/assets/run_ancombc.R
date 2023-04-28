#!/usr/bin/env Rscript

# error handling -----------------
options(error = function() {
  sink(stderr())
  on.exit(sink(NULL))
  traceback(3)
  if (!interactive()) {
    q(status = 1)
  }
})

# load libraries -----------------
suppressWarnings(library(phyloseq))
suppressWarnings(library(tidyverse))
suppressWarnings(library(ANCOMBC))
library("optparse")
library("frictionless")
library("jsonlite")

# load arguments -----------------
cat(R.version$version.string, "\n")

option_list <- list(
  make_option("--inp_abundances_path", action = "store", default = "NULL",
              type = "character"),
  make_option("--inp_metadata_path", action = "store", default = "NULL",
              type = "character"),
  make_option("--md_column_types", action = "store", default = "NULL",
              type = "character"),
  make_option("--formula", action = "store", default = "NULL",
              type = "character"),
  make_option("--p_adj_method", action = "store", default = "NULL",
              type = "character"),
  make_option("--prv_cut", action = "store", default = "NULL",
              type = "character"),
  make_option("--lib_cut", action = "store", default = "NULL",
              type = "character"),
  make_option("--reference_levels", action = "store", default = "NULL",
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
  make_option("--output_loaf", action = "store", default = "NULL",
              type = "character")
)
opt <- parse_args(OptionParser(option_list = option_list))

# Assign each arg (in positional order) to an appropriately named R variable
inp_abundances_path <- opt$inp_abundances_path
inp_metadata_path   <- opt$inp_metadata_path
md_column_types     <- opt$md_column_types
formula             <- opt$formula
p_adj_method        <- opt$p_adj_method
prv_cut             <- as.numeric(opt$prv_cut)
lib_cut             <- as.numeric(opt$lib_cut)
reference_levels    <- opt$reference_levels
neg_lb              <- as.logical(opt$neg_lb)
tol                 <- as.numeric(opt$tol)
max_iter            <- as.numeric(opt$max_iter)
conserve            <- as.logical(opt$conserve)
alpha               <- as.numeric(opt$alpha)
output_loaf         <- opt$output_loaf

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
                              fill = TRUE, header = TRUE)
  }

# convert column types to numeric/categorical as specified in metadata
md_column_types <- fromJSON(md_column_types)

for (i in seq(1, length(md_column_types))) {
  if (md_column_types[i] == "numeric") {
    metadata_file[[names(md_column_types[i])]] <-
      as.numeric(metadata_file[[names(md_column_types[i])]])
  } else if (md_column_types[i] == "categorical") {
    metadata_file[[names(md_column_types[i])]] <-
      as.character(metadata_file[[names(md_column_types[i])]])
  }
}

otu <- otu_table(otu_file, taxa_are_rows = TRUE)
md <- sample_data(metadata_file)
row.names(md) <- rownames(metadata_file)

intercept_groups <- c()
# split the reference_levels param into each column and associated level order
level_vectors <- unlist(strsplit(reference_levels, ", "))

for (i in level_vectors) {
  column <- unlist(strsplit(i, "::"))[1]
  column <- gsub("\\'", "", column)
  column <- gsub("\\]", "", column)
  column <- gsub("\\[", "", column)

  intercept_vector <- unlist(strsplit(i, "::"))[2]
  intercept_vector <- unlist(strsplit(intercept_vector, ","))
  intercept_vector <- gsub("\\'", "", intercept_vector)
  intercept_vector <- gsub("\\]", "", intercept_vector)
  intercept_vector <- gsub("\\[", "", intercept_vector)

  intercept_groups <- append(intercept_groups,
                              paste(column, intercept_vector, sep = "::"))

  # handling formula input(s)
  md[[column]] <- factor(md[[column]])
  md[[column]] <- relevel(md[[column]], ref = intercept_vector)
}

# create phyloseq object for use in ancombc
data <- phyloseq(otu, md)

# analysis -----------------------
fit <- ancombc(data = data, formula = formula, p_adj_method = p_adj_method,
               prv_cut = prv_cut, lib_cut = lib_cut, neg_lb = neg_lb,
               tol = tol, max_iter = max_iter, conserve = conserve,
               alpha = alpha)

# Diagnostics - we'll deal with these later
# samp_frac <- fit$samp_frac
# resid     <- fit$resid
# delta_em  <- fit$delta_em
# delta_wls <- fit$delta_wls

# Re-naming index for each data slice
colnames(fit$res$lfc)[1]   <- "id"
colnames(fit$res$se)[1]    <- "id"
colnames(fit$res$W)[1]     <- "id"
colnames(fit$res$p_val)[1] <- "id"
colnames(fit$res$q_val)[1] <- "id"

# DataLoafPackageDirFmt slices
lfc   <- fit$res$lfc
se    <- fit$res$se
w     <- fit$res$W
p_val <- fit$res$p_val
q_val <- fit$res$q_val

# Constructing data slices for each structure in the DataLoaf
# and saving to the output_loaf
dataloaf_package <- create_package()
# Dataloaf attribute containing the reference levels
# Used in the tabulate viz for listing out the intercept columns
dataloaf_package$metadata <- list(intercept_groups = intercept_groups)

dataloaf_package <- add_resource(package = dataloaf_package,
                                 resource_name = "lfc_slice", data = lfc)
dataloaf_package <- add_resource(package = dataloaf_package,
                                 resource_name = "se_slice", data = se)
dataloaf_package <- add_resource(package = dataloaf_package,
                                 resource_name = "w_slice", data = w)
dataloaf_package <- add_resource(package = dataloaf_package,
                                 resource_name = "p_val_slice", data = p_val)
dataloaf_package <- add_resource(package = dataloaf_package,
                                 resource_name = "q_val_slice", data = q_val)

write_package(package = dataloaf_package, directory = output_loaf)
