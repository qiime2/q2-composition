# q2-composition

![](https://github.com/qiime2/q2-composition/workflows/ci/badge.svg)

This is a QIIME 2 plugin. For details on QIIME 2, see https://qiime2.org.

## Install Guide

This plugin is a wrapper for the ANCOMBC package. We are working with the
[RELEASE_3_15](https://github.com/FrederickHuangLin/ANCOMBC/tree/RELEASE_3_15)
branch, as this is where the functionality for ANCOM, ANCOM-BC, and SECOM are
all located. This release hasn't been published on bioconductor yet, so the
steps to install this latest release (for development purposes) are as follows:

### Install R

If you do not currently have R installed, you will need to do that prior to
installing ANCOMBC. The appropriate CRAN mirror for your machine can be found
[here](https://cran.r-project.org/mirrors.html).

### Install devtools
Once you have installed R on your machine, you will need devtools to install
ANCOMBC. Install instructions for devtools can be found
[here](https://github.com/r-lib/devtools).

### Install missing dependencies
nloptr is a dependency for ANCOMBC that is currently missing, and thus needs to
be installed prior to ANCOMBC. This can be easily done using conda with the
following command:
```
conda install -c conda-forge r-nloptr
```

### Install ANCOMBC using devtools
ANCOMBC can be installed using devtools with the following command:
```
devtools::install_github("git@github.com:FrederickHuangLin/ANCOMBC.git")
```
