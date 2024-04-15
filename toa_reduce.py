import numpy as np
import psrchive as psr
import plot_ar
import time
import glob
import os
from argparse import ArgumentParser


def make_dspec_plot(ar_file, plot_dir):
    """
    Make an plot of the dynamic spectrum of 
    the archive data and put it in plot_dir

    plot name will just be [archive base]_plot.png
    """
    ar_fn = ar_file.rsplit('/', 1)[-1]
    ar_base = ar_fn.rsplit('.', 1)[0]
    outfile = "%s/%s.png" %(plot_dir, ar_base)

    if os.path.isfile(outfile):
        print("Plot already exists: %s" %outfile)
        print("... skipping")

    else:
        plot_ar.make_plot(ar_file, outfile=outfile)

    return


def calc_nsub(tobs, tsub, nmin):
    """
    Calculate number of subints for an obs 
    of duration tobs seconds to get approx 
    tsub seconds per subint while making sure 
    there are at least nmin
    """
    nsub = int(tobs / tsub)
    if nsub * tsub < tobs:
        nsub += 1
    else: pass

    if nsub < nmin:
        nsub = nmin

    return nsub


def prepare_ar(arfile, tsub=-1, nmin=1):
    """
    Read in an archive file to an archive object
    and prepare for timing:

       * fscrunch (sum freqs)
       * pscrunch (sum pol)
        
    Optionally average in time to (approx) tsub
    seconds per subint

    If nmin > 0,  make sure we have at least nmin 
    subints

    Return archive object
    """
    # Load data file
    obs = psr.Archive_load(arfile)
   
    # tscrunch (if desired)
    if tsub > 0:
        tobs = (obs.end_time() - obs.start_time()).in_seconds() 
        nsub = calc_nsub(tobs, tsub, nmin)
        obs.tscrunch_to_nsub(nsub)

    # pscrunch - average pols
    obs.pscrunch()

    # fscrunch - average freqs
    obs.fscrunch()

    return obs


def get_toas_from_obs(obs, template):
    """
    Calculate toas from obs and template 
    archive objects

    returns toas (*.time file line string)
    """
    # Timing Object
    arrtim = psr.ArrivalTime() 
    arrtim.set_shift_estimator('PGS')
    arrtim.set_format('Tempo2')

    # Add template
    arrtim.set_standard(template)

    # Add obs 
    arrtim.set_observation(obs)

    # Get toas
    toas = arrtim.get_toas()

    return toas


def get_toas_from_list(ar_list, tmp_ar, tsub=-1, nmin=1, 
                       make_plots=False, plot_dir='.'):
    """
    Calcuate toas from many obs archive files 
    in the list ar_list using a template in 
    the file tmp_ar

    if tsub > 0: gives the approx desired subintegration 
    time (if possible)

    nmin is the minimum number of subints to allow per file 

    if make_plots == True, we will make plots of the archive
    data and put them in plot_dir.  The file name will be 
    based on the archive name
    """ 
    # Make template object
    tmp = psr.Archive_load(tmp_ar)    
    tmp.pscrunch()
    tmp.fscrunch()

    # set toa_list 
    toas_list = []

    # Loop over ar_list file list, load archive and 
    # calculate toas 
    for ar_file in ar_list:
        print("Processing: %s" %ar_file)
        if make_plots:
            make_dspec_plot(ar_file, plot_dir)
        obs = prepare_ar(ar_file, tsub=tsub, nmin=nmin)
        toas = get_toas_from_obs(obs, tmp)
        toas_list += list(toas)
        del obs
    
    return toas_list


def write_tim_file(toas_list, outfile, offset="+1.0"):
    """
    Write toas to tim file

    If there is a time offset, include as string, eg:

            offset="+1.0"

    for a 1 second offset. If offset=None, will skip
    """ 
    hdr = "FORMAT 1\n"
    if offset is not None:
        hdr += "TIME %s\n" %offset
    else: pass

    with open(outfile, 'w') as fout:
        fout.write(hdr)
        for toa in toas_list:
            fout.write("%s\n" %toa)

    return


def parse_input():
    """
    Use argparse to parse input
    """
    prog_desc = "Reduce archives and generate TOAs"
    parser = ArgumentParser(description=prog_desc)

    parser.add_argument('ar_files', nargs="*", 
                        help='Input archive files (or glob str)')
    parser.add_argument('-temp', '--template', 
                        help='Template file for timing', 
                        required=True)
    parser.add_argument('-o', '--outbase',
                        help='Output tim file basename (no suffix)',
                        required=True)
    parser.add_argument('-pdir', '--plot_dir',
                        help='Plot directory (ignore if no plots)',
                        required=False, default=None)
    parser.add_argument('-tsub', '--t_subint',
                        help='Subint duration (s)',
                        required=False, type=float)
    parser.add_argument('-nsub', '--n_subint',
                        help='Minimum number of subints per obs (def=1)',
                        default=1, required=False, type=int)

    args = parser.parse_args()

    fnames = args.ar_files
    temp = args.template
    pdir = args.plot_dir
    tsub = args.t_subint
    nsub = args.n_subint 
    outbase = args.outbase

    return fnames, temp, pdir, tsub, nsub, outbase


debug = 0
if __name__ == "__main__":
    if not debug:
        tstart = time.time()
        
        fnames, temp, pdir, tsub, nsub, outbase = parse_input()
        if pdir is None:
            make_plots = False
        else:
            make_plots = True

        if tsub is None:
            tsub = -1

        if len(fnames) == 0:
            print("No archive files found!")
            sys.exit(0)
        else: pass
        
        toas_list = get_toas_from_list(fnames, temp, tsub=tsub, 
                            nmin=nsub, make_plots=make_plots, 
                            plot_dir=pdir)

        outfile = '%s.tim' %outbase
        write_tim_file(toas_list, outfile, offset="+1.0")

        tstop = time.time()
        dt = tstop - tstart
        print("Took %.2f minutes" %(dt/60.0))
        
    else:
        pass

