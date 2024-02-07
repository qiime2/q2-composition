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

pytest -k 'test_ancombc.py'

pytest -v -k 'test_ids_in_table_with_upper_Es'

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

```R
suppressWarnings(library(phyloseq))
suppressWarnings(library(tidyverse))
suppressWarnings(library(ANCOMBC))



# This current import function is broken
otu_file <- t(read.delim("table-newtest.tsv", check.names = F, row.names = 1))
otu_file |> colnames()
otu_file |> glimpse()

# Possible fix, setting class for just the initial empty column works well:
otu_file <- NULL
otu_file <- t(read.delim("table-newtest.tsv", check.names = T, row.names = 1, colClasses = c(X = "character")))
otu_file |> colnames() # works!
otu_file               # note feature id '03' becomes 'X03'

# Does this same problem happen with metadata?
# It can, as the non-number in the #q2:types columns are optional!
metadata_file <- NULL
metadata_file <- read.delim("md-newtest.tsv", check.names = F, row.names = 1, colClasses = list(`sample-id` = "character"))
metadata_file
metadata_file |> glimpse()

# Test on file from forums and @cherman2
otu_file <- NULL
otu_file <- t(read.delim("q2_composition/tests/data/forum-table-2-with-E.txt", check.names = T, row.names = 1, colClasses = c(X = "character")))
otu_file |> colnames()
otu_file |> glimpse()
otu_file |> head()



```
