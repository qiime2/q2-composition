# Colin's notes

## Metadata convert

```sh
cd /home/biouser/bin/github-repos/q2-composition/q2_composition/tests/data
qiime feature-table group \
    --i-table table-ancombc.qza \
    --m-metadata-file sample-md-ancombc-IDE.tsv \
    --m-metadata-column sample-IDE \
    --p-mode sum \
    --p-axis sample \
    --o-grouped-table table-ancombc-IDE.qza

```

## Testing

```python
flake8
make dev

pytest -v -k 'test_ids_in_table_with_upper_Es'

pytest -k 'test_ancombc.py'

```

## qza table to csv

```python
from qiime2 import Artifact
import pandas as pd
table = Artifact.load("q2_composition/tests/data/table-ancombc.qza")
df = table.view(pd.DataFrame)
df.to_csv("table-dada2-mp.tsv", sep = "\t", header = True)
# edit ids in txt to not have "E"
# Go to R

```

## From python, save dfs for testing

```python
md = Metadata(pd.DataFrame(
    index=pd.Index(['33001E607', '33002E607', '33003E607',
                    '33004E607', '33005E607', '33006E607'],
                    name='sample-id'),
    columns=['bodysite', 'animal'],
    data=np.array([['gut', 'dog'], ['right palm', 'cat'],
                    ['gut', 'bird'], ['left palm', 'cow'],
                    ['left palm', 'cat'], ['tongue', 'bird']])
))
table = Table(np.array([[5, 1, 4, 2, 6, 3],
                        [3, 2, 1, 1, 5, 4],
                        [1, 4, 2, 4, 5, 6],
                        [3, 2, 5, 1, 2, 4],
                        [5, 6, 2, 3, 1, 1],
                        [1, 1, 4, 2, 3, 6]]),
                ['33001E607', '33002E607', '33003E607',
                '33004E607', '33005E607', '33006E607'],
                ['O1', 'O2', '03', '04', '05', '06']).to_dataframe()

md.to_dataframe().to_csv("md-newtest.tsv", sep = "\t", header = True)
table.to_csv("table-newtest.tsv", sep = "\t", header = True)

```

## Run dev plugin on .qza files

```sh
ll q2_composition/tests/data/
make dev

# typical IDs
qiime composition ancombc \
    --i-table q2_composition/tests/data/table-ancombc.qza \
    --m-metadata-file q2_composition/tests/data/sample-md-ancombc.tsv \
    --p-formula "testcolumn" --verbose \
    --o-differentials differentials-typicalIDs.qza

# new SI notation look'n 100e2 IDs
qiime composition ancombc \
    --i-table q2_composition/tests/data/table-ancombc-IDE.qza \
    --m-metadata-file q2_composition/tests/data/sample-md-ancombc-IDE.tsv \
    --p-formula "testcolumn" --verbose \
    --o-differentials differentials2.qza

```

## Playing with R functions

Base R utils: https://www.rdocumentation.org/packages/utils/versions/3.6.2/topics/read.table
Tidyverse: https://readr.tidyverse.org/reference/read_delim.html

```R
library(phyloseq)
library(tidyverse)
library(ANCOMBC)



# This current import function is broken
otu_file <- t(read.delim("colin-table.tsv", check.names = F, row.names = 1))
otu_file |> colnames()
otu_file |> glimpse()

# Possible fix, setting class for just the initial empty column works well:
otu_file <- NULL
otu_file <- t(read.delim("colin-table.tsv", check.names = T, row.names = 1, colClasses = c(X = "character")))
otu_file |> colnames() # works!
otu_file               # note feature id starting with zeros have an X added, like 03 -> X03
otu_file |> class()

# Test on file from forums and @cherman2
otu_file <- NULL
otu_file <- t(read.delim("q2_composition/tests/data/forum-table-2-with-E.txt", check.names = T, row.names = 1, colClasses = c(X = "character")))
otu_file |> colnames()
otu_file |> glimpse()
otu_file |> head()

# Alt using tidyverse
otu_file2 = NULL
otu_file2 = "table-dada2-mp.tsv" |>
  read_tsv(col_names = T, col_types = cols("character", .default = col_double())) |>
  column_to_rownames("...1") |> t()
otu_file2 |> head() # note feature ids now start with zero, and are not changed
otu_file2 |> class() # same as before
otu_file2 |> colnames()

# Forums file
otu_fileF = "q2_composition/tests/data/forum-table-2-with-E.txt" |>
  read_tsv(col_names = T, col_types = cols("character", .default = col_double())) |>
  column_to_rownames("...1") |> t()
otu_fileF |> colnames()
otu_fileF |> glimpse()
otu_fileF |> head()

# Does this same problem happen with metadata?
# It can, as the non-number in the #q2:types columns are optional!
# Before PR (broken)
inp_metadata_path = "colin-md.tsv"
md_file <- NULL
md_file <- read.delim(inp_metadata_path, check.names = FALSE, row.names = 1)
# After PR (base R)
md_file <- NULL
md_file <- read.delim(inp_metadata_path,
  check.names = FALSE, row.names = 1,
  colClasses = list(`sample-id` = "character"))
row.names(md_file)
rownames(md_file)

metadata_file <- NULL
metadata_file <- read.delim("colin-md.tsv", check.names = F, row.names = 1, colClasses = list(`sample-id` = "character"))
metadata_file
metadata_file |> glimpse()
row.names(metadata_file)
rownames(metadata_file)

# Alt using tidyverse
metadata_file2 <- NULL
metadata_file2 = "colin-md-SampleID.tsv" |>
  read_tsv(col_names = T, col_types = cols("character", .default = col_guess())) |>
  data.frame()
metadata_file2
glimpse(metadata_file2)

# Select drops row names, so we can't use it...
# metadata_file2 |> select(-1) |> row.names()

# make rownames from first column
row.names(metadata_file2) <- metadata_file2[[1]]
# Then drop first column
metadata_file2 = metadata_file2[-1]
# It's supprisingly hard to do this by index alone with the Tidyverse!
# Tidyverse Tibbles don't like indexes or rownames
metadata_file2
glimpse(metadata_file2)


```
