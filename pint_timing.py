import astropy.units as u
import matplotlib.pyplot as plt
import numpy as np

import pint.fitter
from pint.models import get_model_and_toas
from pint.residuals import Residuals
import pint.logging

pint.logging.setup(level="INFO")

def make_prefit_plot(t, m):
    """
    Make a plot of prefit residuals
    """
    rs = Residuals(t, m).time_resids.to(u.us).value
    xt = t.get_mjds()
    fig = plt.figure(figsize=(7,4))
    ax = fig.add_subplot()
    #ax.plot(xt, rs, "x")

    obs_list = np.unique(t.table['obs'])[::-1]
    obs_num  = np.array([ np.sum( t.table['obs'] == obsi ) \
                          for obsi in obs_list ])
    xx = np.argsort(obs_num)[::-1]
    obs_list = obs_list[xx]

    freq_GHz  = np.floor(t.table['freq'].to(u.GHz).value * 10) / 10
    freq_list = np.unique(freq_GHz)[::-1]

    obs_markers = ['s', 'o', 'x']
    obs_dict = {'goldstone': 'GS', 'robledo': 'RO'}
    
    for ii, obs in enumerate(obs_list):
        xxi = np.where(t.table['obs'] == obs)[0]
        for jj, freq in enumerate(freq_list):
            yyj = np.where(freq_GHz[xxi] == freq)[0]
            zzk = xxi[yyj]
            lab = "%s - %.1f GHz" %(obs_dict[obs], freq)
            if len(zzk) == 0:
                continue
            marker = obs_markers[ii]
            ax.errorbar(
                xt.value[zzk],
                rs[zzk],
                t.get_errors().to(u.us).value[zzk],
                fmt=marker, ms=3, elinewidth=1, label=lab
                )

    plt.title(f"{m.PSR.value} Pre-Fit Timing Residuals")
    ax.set_xlabel("MJD")
    ax.set_ylabel("Residual (us)")
    plt.grid(alpha=0.75)
    plt.legend()
    plt.show()
    return rs

def make_postfit_plot(t, f, m):
    """
    plot postfit residuals
    """
    fig = plt.figure(figsize=(7,4))
    ax = fig.add_subplot()
    xt = t.get_mjds()

    obs_list = np.unique(t.table['obs'])[::-1]
    obs_num  = np.array([ np.sum( t.table['obs'] == obsi ) \
                          for obsi in obs_list ])
    xx = np.argsort(obs_num)[::-1]
    obs_list = obs_list[xx]

    freq_GHz  = np.floor(t.table['freq'].to(u.GHz).value * 10) / 10
    freq_list = np.unique(freq_GHz)[::-1]

    obs_markers = ['s', 'o', 'x']
    obs_dict = {'goldstone': 'GS', 'robledo': 'RO'}
    
    for ii, obs in enumerate(obs_list):
        xxi = np.where(t.table['obs'] == obs)[0]
        for jj, freq in enumerate(freq_list):
            yyj = np.where(freq_GHz[xxi] == freq)[0]
            zzk = xxi[yyj]
            lab = "%s - %.1f GHz" %(obs_dict[obs], freq)
            if len(zzk) == 0:
                continue
            marker = obs_markers[ii]
            ax.errorbar(
                xt.value[zzk],
                f.resids.time_resids.to(u.us).value[zzk],
                t.get_errors().to(u.us).value[zzk],
                fmt=marker, ms=3, elinewidth=1, label=lab
                )
    plt.title(f"{m.PSR.value} Post-Fit Timing Residuals")
    ax.set_xlabel("MJD")
    ax.set_ylabel("Residual (us)")
    plt.grid(alpha=0.75)
    plt.legend()
    plt.show()
    return


def fit_model(m, t_all, max_err_us=3):
    """
    Fit F0 and F1
    """
    # Unfreeze the parameters you want to fit
    m.components['Spindown'].F0.frozen = False
    m.components['Spindown'].F1.frozen = False
    
    error_ok = t_all.table["error"] <= max_err_us * u.us
    t = t_all[error_ok]
    
    f = pint.fitter.Fitter.auto(t, m)
    f.fit_toas()
    # Print some basic params
    print("Best fit has reduced chi^2 of", f.resids.chi2_reduced)
    print("RMS in phase is", f.resids.phase_resids.std())
    print("RMS in time is", f.resids.time_resids.std().to(u.us))
    return t, f


def auto_zap_toas(toas, m, nsig=6):
    """
    Zap toas with residuals (from model `m`) with 
    magnitudes greater than `nsig` standard deviations 
    (calcluated with inner 80% values) from zero.

    WARNING: this is very course and for prefit data 
    there may be issues if you don't have a good starting 
    model
    """
    rs = Residuals(toas, m).time_resids.to(u.us).value 
    rs_sort = np.sort(rs)
    N = len(rs)
    rs_80 = rs_sort[ int(0.1 * N) : int(0.9 * N) ]
    rsig = np.std(rs_80)
    print(nsig * rsig)
    xx = np.where( np.abs(rs) > nsig * rsig )[0]
    xxc = np.setdiff1d( np.arange(N), xx )
    return toas[xxc]
        
        

#"""
parfile = 'par/B1937_tdb_nanoPX.par'
timfile = 'b1937_09apr24.tim'
"""
m, t_all = get_model_and_toas(parfile, timfile)
xx_srt = np.argsort(t_all.get_mjds())
t_all = t_all[xx_srt]
t_all.print_summary()
"""
