# DSN Reduction and Timing Pipeline

These scripts let you generate TOAs from archive files 
and then fit the TOAs to a model using PINT.

## Generating TOAs

The script `toa_reduce.py` takes in archive files and a 
template and produces TOAs which are writting to a tim file.
You can specify the subint duration for making TOAs or the 
min number of subints per obs.  Optionally, you can make 
time-frequency plots of the data for each observation as 
well.  The script is run with the following arguments:

     Reduce archives and generate TOAs
     
     positional arguments:
       ar_files              Input archive files (or glob str)
     
     optional arguments:
       -h, --help            show this help message and exit
       -temp TEMPLATE, --template TEMPLATE
                             Template file for timing
       -o OUTBASE, --outbase OUTBASE
                             Output tim file basename (no suffix)
       -pdir PLOT_DIR, --plot_dir PLOT_DIR
                             Plot directory (ignore if no plots)
       -tsub T_SUBINT, --t_subint T_SUBINT
                             Subint duration (s)
       -nsub N_SUBINT, --n_subint N_SUBINT
                             Minimum number of subints per obs (def=1)

You can use wildcards in the `ar_files` option, as in the following example:

     python toa_reduce.py -temp 22m180/d180.std -o apr15 -pdir plots -tsub 600 2*/*pazi

The result of this script will be plots for each obs (it will skip them 
if they already exist) and a TOA file `[outbase].tim`.

## Fitting a Model
