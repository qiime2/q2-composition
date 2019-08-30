#!/usr/bin/env Rscript

args <- commandArgs(TRUE)

feature_table_fp <- args[[1]]
metadata_fp <- args[[2]]
main_var <- args[[3]]
zero_cut <- args[[4]]
p_adjust_method <- args[[5]]
alpha <- args[[6]]
adj_formula <- args[[7]]
rand_formula <- args[[8]]
w_frame_fp <- args[[9]]


### LOAD LIBRARIES ###
library(readr)
library(tidyverse)

otu_data = read_tsv(feature_table_fp, skip = 1)
otu_id = otu_data$`feature-id`
otu_data = data.frame(t(otu_data[, -1]), check.names = FALSE)
colnames(otu_data) = otu_id
otu_data = otu_data%>%rownames_to_column("Sample.ID")

meta_data = read_tsv(metadata_fp)[-1, ]
meta_data = meta_data%>%rename(Sample.ID = `#SampleID`)

otu_data = otu_data%>%arrange(Sample.ID)
meta_data = meta_data%>%arrange(Sample.ID)
all(otu_data$Sample.ID == meta_data$Sample.ID)

# Run ANCOM
source("ancom_v2.0.R")

res = ANCOM(otu_data, meta_data, main_var, zero_cut, p_adjust_method, alpha,
            adj_formula, rand_formula)

write_csv(res, w_frame_fp)
