# q2-composition

![](https://github.com/qiime2/q2-composition/workflows/ci/badge.svg)

This is a QIIME 2 plugin. For details on QIIME 2, see https://qiime2.org.

## Install Guide

This plugin is a wrapper for the ANCOMBC package. We are working with the
[RELEASE_3_15](https://github.com/FrederickHuangLin/ANCOMBC/tree/RELEASE_3_15)
branch, as this is where the functionality for ANCOM, ANCOM-BC, and SECOM are
all located. This bioconductor release hasn't been published on bioconda yet,
so the steps to install this latest release (for development purposes) are as
follows:

### Install R

If you do not currently have R installed, you will need to do that prior to
installing ANCOMBC. The best way to do this for our purposes will be to use
the version of R that is included in the latest release of QIIME 2, used within
a conda environment. Install instructions for QIIME 2 can be found
[here](https://docs.qiime2.org/2022.2/install/native/#install-qiime-2-within-a-conda-environment).
Once installed, you can activate R by typing `R` into the command line.

### Install missing dependencies
nloptr is a dependency for ANCOMBC that is currently missing within the R package,
and thus needs to be installed prior to ANCOMBC.
This can be easily done using conda with the following command:
```
conda install -c conda-forge r-nloptr
```

You will need the phyloseq package in order to run the QIIME 2 ANCOMBC plugin.
This package can be installed with the following command:
```
conda install -c conda-forge -c bioconda bioconductor-phyloseq
```

You will also need the frictionless package for R in order to run the QIIME 2 ANCOMBC plugin.
You can install this package with the following command:
```
conda install -c conda-forge -c bioconda r-frictionless
```

The last two dependencies that you'll need to install are frictionless (separate from the R package)
and formulaic. These can be installed with the following commands:
```
conda install -c conda-forge frictionless
```
```
conda install -c conda-forge formulaic
```

### Install devtools
Once you have installed R on your machine, you will need devtools to install
ANCOMBC. Install instructions for devtools can be found
[here](https://github.com/r-lib/devtools). The easiest install method will be
through CRAN, using the following command:
```
install.packages("devtools")
```

### Install ANCOMBC using devtools
ANCOMBC can be installed using devtools with the following command:
```
devtools::install_github("https://github.com/FrederickHuangLin/ANCOMBC/tree/RELEASE_3_15")
```

### Dev install q2-stats plugin
The final dependency that needs to be installed is the q2-stats plugin within the QIIME 2 Organization.
This can be done by cloning [this repository](https://github.com/qiime2/q2-stats) to your local machine
and running `make dev` in your development environment.

### Dev install q2-composition
Now you're ready to install ANCOM-BC within q2-composition! You'll need to clone this repository to your local machine, run `git fetch` from this remote and checkout the ANCOM-wrapper branch. Once you've done that you can run `make dev` and you'll be ready to use ANCOM-BC!
