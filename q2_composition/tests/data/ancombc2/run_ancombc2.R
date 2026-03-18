library("ANCOMBC")
library("phyloseq")

args <- commandArgs(trailingOnly = TRUE)
feature_table_path <- args[1]
metadata_path <- args[2]
output_dir <- args[3]

table <- read.table(
    feature_table_path, sep = "\t", header = TRUE, row.names = 1
)
table <- as.matrix(table)
otu_table <- otu_table(table, taxa_are_rows = TRUE)

metadata <- read.table(
    metadata_path,
    sep = "\t",
    header = TRUE,
    comment.char = "#",
    row.names = 1
)
sample_data <- sample_data(metadata)

phyloseq_obj <- phyloseq(otu_table, sample_data)

abc2_output <- ancombc2(
    data = phyloseq_obj,
    fix_formula = "body.site + year",
    rand_formula = NULL,
    p_adj_method = "holm",
    prv_cut = 0.1,
    group = "body.site",
    struc_zero = TRUE,
    alpha = 0.05,
    neg_lb = FALSE,
    n_cl = 1
)

write.table(
    abc2_output$res,
    file = file.path(output_dir, "abc2-output.tsv"),
    sep = "\t",
    row.names = FALSE
)
write.table(
    abc2_output$zero_ind,
    file = file.path(output_dir, "abc2-struc-zeros.tsv"),
    sep = "\t",
    row.names = FALSE
)
