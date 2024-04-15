# DSN Reduction and Timing Pipeline

These scripts let you generate TOAs from archive files 
and then fit the TOAs to a model using PINT.

## Requirements

You will need to install `PINT`.  If you want to use data 
from the DSN telescopes, you will also need to include the 
relevant clock files and an observatory file.  These are 
included here in the `clock` and `obs` folders.  However, 
you will need to tell `PINT` where to find them by adding the 
following environment variables:

     export PINT_CLOCK_OVERRIDE=/path/to/timing_pipeline/clock
     export PINT_OBS_OVERRIDE=/path/to/timing_pipeline/obs/dsn_obs.json 


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

Once we have a tim file, we can go about fitting a model to the data.
We will use PINT in the `pint_timing.py` script.  This is probably 
best done interactively, so below is an example.

First we define our initial par file and the input tim file:

     parfile = 'par/B1937_tdb_nanoPX.par'
     timfile = 'b1937_09apr24.tim'

Next, we read in these two file and make a model and a 
list of TOAs.  Because they might not be in order, we also 
time sort them.

     m, t_all = get_model_and_toas(parfile, timfile)
     xx_srt = np.argsort(t_all.get_mjds())
     t_all = t_all[xx_srt]
     t_all.print_summary()

Now we make a plot of the TOA residuals for the initial 
model.  This will allow us to see how well the model fits 
and also a chance to examine the data for outliers.

     make_prefit_plot(t_all, m)

If neccessary, we can zap outliers.  There is a very simple 
convenience function in the script that removes TOAs that are 
more than `nsig` standard deviations from the model.  We don't 
want to be too aggressive here because the model may not be very 
good and the residuals could have a linear slope over time.

     t_zap = auto_zap_toas(t_all, m, nsig=10)

After zapping, we can make another plot to see how well it worked.

     make_prefit_plot(t_zap, m)

If that looks good enough to fit, then we can fit a timing model 
to our TOAs.  By default we will just fit for `F0` and `F1` (ie, 
the spin frequency and spin frequency derivative).  We can also set 
a maximum TOA uncertainty so that any TOAs with error bars larger than 
this will be excluded.

     t, f = fit_model(m, t_zap, max_err_us=2)

OK, now that we have a model, we can fit the residuals to this 
new model

     make_postfit_plot(t, f, m)

If the data look good, you can stop there.  Otherwise, it may be useful 
to do another round of zapping.  Now that we have a better model of the 
data, the zapping can be at a bit lower level.

     pt_zap = auto_zap_toas(f.toas, f.model, nsig=7)

Now we need to start over with these new TOAs.  First, we can 
plot the pre-fit residuals to make sure we haven't done anything 
too extreme:

     make_prefit_plot(pt_zap, m)

If that looks ok, then we re-fit the data:

     t2, f2 = fit_model(m, pt_zap, max_err_us=2)

and plot the post-fit residuals again:

     make_postfit_plot(t2, f2, m)

If that looks good, then we are good to go.  Otherwise, we should 
repeat the zapping and fitting cycle.

