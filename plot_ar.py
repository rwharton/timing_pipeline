import psrchive
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import numpy as np

# if you want serif fonts
# if not, comment out
#plt.rcParams["font.family"] = "serif"
#plt.rcParams["mathtext.fontset"] = "dejavuserif"


def make_plot(ar_file, uflo=None, ufhi=None, shade_pulse=False, 
              find_peak=True, outfile=None):
    """
    Test plot from psrchive documentation

    uflo (optional): set the minimum display freq
    ufhi (optional): set the maximum display freq

    shade_pulse (bool): shade region used for spectrum

    find_peak (bool): find peak for spec if True, else 
                      just average over all phase
    """
    if outfile is not None:
        plt.ioff()
    # get data
    arch = psrchive.Archive_load(ar_file)
    #arch.bscrunch_to_nbin(1024)
    #print(arch.get_nbin())
    print("  Dedispersing...")
    arch.dedisperse()
    print("  Scrunching subints...")
    arch.tscrunch()
    print("  Removing baseline...")
    arch.remove_baseline()
    print("  Centering...")
    arch.centre_max_bin()
    print("  Getting data...")
    data = arch.get_data()
    freqs = arch.get_frequencies()

    freq_lo = arch.get_centre_frequency() - arch.get_bandwidth()/2.0
    freq_hi = arch.get_centre_frequency() + arch.get_bandwidth()/2.0

    # set up figure
    print("  Making plot...")
    fig = plt.figure(constrained_layout=True)
    gs = GridSpec(3, 3, figure=fig)

    ax_t  = fig.add_subplot(gs[0, 0:2])
    ax_ds = fig.add_subplot(gs[1:, 0:2])
    ax_f  = fig.add_subplot(gs[1:, 2])
    ax_l  = fig.add_subplot(gs[0, 2])

    ax_t.sharex(ax_ds)
    ax_f.sharey(ax_ds)

    # dynamic spectrum
    dat = np.mean(data[:,0,:,:], axis=0).T
    ax_ds.imshow(dat.T, extent=(0,1,freq_lo,freq_hi), 
                 aspect='auto', origin='lower', interpolation='nearest')

    ax_ds.set_xlabel("Pulse Phase", fontsize=14)
    ax_ds.set_ylabel("Frequency (MHz)", fontsize=14)

    # Time series
    ts = np.mean(dat, axis=1)
    tt = np.linspace(0, 1, len(ts))
    ts_vals = np.sort(ts)[ int(0.2 * len(ts)) : int(0.8 * len(ts)) ]
    sig = np.std(ts_vals)
    ts /= sig
    ax_t.plot(tt, ts)
    ax_t.tick_params(axis='x', labelbottom=False)
    tylim = ax_t.get_ylim()
    ax_t.set_xlim(tt[0], tt[-1])

    # Spectrum
    xpk = np.argmax(ts)
    xx_below = np.where( ts <= 0.1*np.max(ts) )[0]
    xx_lo = np.max(xx_below[xx_below <= xpk ])
    xx_hi = np.min(xx_below[xx_below >= xpk ])

    if find_peak:
        spec = np.mean(dat[xx_lo:xx_hi], axis=0)
    else:
        spec = np.mean(dat, axis=0)

    ax_f.plot(spec, freqs)
    ax_f.set_ylim(freqs[0], freqs[-1])
    ax_f.tick_params(axis='y', labelleft=False)

    # Shade region used for spec if desired
    if shade_pulse:
        tlo = tt[xx_lo]
        thi = tt[xx_hi]
        fb_lo  = min(-10, -1 * np.max(ts) )
        fb_hi  = max(100, 10 * np.max(ts))
        ax_t.fill_betweenx([fb_lo, fb_hi], tlo, thi, color='r', alpha=0.1)
        print(tlo, thi)
    
    ax_t.set_ylim(tylim)

    # Check to see if there is any zero padding in freq
    s = np.sum(dat, axis=0)
    s_nz = np.abs(s[np.abs(s) > 0])
    s_nz_lo = np.sort(s_nz)[int(0.10 * len(s_nz))] / 10
    xxz = np.where( np.abs(s) > s_nz_lo )[0]
    df = np.diff(freqs)[0]
    if np.min(xxz) > 0:
        xxz_lo = np.min(xxz) - 1
    else: xxz_lo = 0

    if np.max(xxz) < ( len(s) - 1):
        xxz_hi = np.max(xxz) + 1
    else: xxz_hi = len(s) - 1

    if df < 0:
        flo = freqs[xxz_hi]
        fhi = freqs[xxz_lo] 
    else:
        flo = freqs[xxz_lo] 
        fhi = freqs[xxz_hi]

    # If freq range, set lim
    if uflo is not None and ufhi is not None:
        ax_f.set_ylim(uflo, ufhi)
    else:
        ax_f.set_ylim(flo, fhi)

    # Label section
    #lfont = {'family':'sans-serif','sans-serif':['Helvetica']}
    ax_l.axis('off')
    lstr = ""
    fpath = arch.get_filename()
    fname = fpath.rsplit('/', 1)[-1]
    lstr += "%s\n" %fname
    lstr += "%s\n" %arch.get_telescope()
    lstr += "%s\n" %arch.get_source()
    lstr += "%.1f MHz\n" %arch.get_centre_frequency()
    lstr += "MJD:  %.2f\n" %arch.get_mjds()[0]
    ax_l.text(0.5, 0.5, lstr, ha='center', va='center', 
              transform=ax_l.transAxes, fontsize=12)
    
    if outfile is not None:
        plt.savefig(outfile, dpi=150, bbox_inches='tight')
        plt.close()
        plt.ion()
    else:
        plt.show()
    return


def get_prof(ar_file):
    """
    Get de-dispersed profile
    """
    # get data
    arch = psrchive.Archive_load(ar_file)
    #arch.bscrunch_to_nbin(1024)
    print(arch.get_nbin())
    print("Dedispersing...")
    arch.dedisperse()
    print("Scrunching subints...")
    arch.tscrunch()
    print("Removing baseline...")
    arch.remove_baseline()
    print("Getting data...")
    data = arch.get_data()
    freqs = arch.get_frequencies()

    freq_lo = arch.get_centre_frequency() - arch.get_bandwidth()/2.0
    freq_hi = arch.get_centre_frequency() + arch.get_bandwidth()/2.0
    
    dat = np.mean(data[:,0,:,:], axis=0).T
    ts = np.mean(dat, axis=1)
    tt = np.linspace(0, 1, len(ts))
    ts_vals = np.sort(ts)[ int(0.2 * len(ts)) : int(0.8 * len(ts)) ]
    sig = np.std(ts_vals)
    ts /= sig

    return tt, ts
