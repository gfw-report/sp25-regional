import platform
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# Define text and column widths (converted from points)
TEXTWIDTH = 524.09975 / 72.27  # \the\textwidth
COLUMNWIDTH = 243.91125 / 72.27  # \the\columnwidth

# Detect the operating system
system = platform.system()
if system == 'Linux':
    serif_font = 'Nimbus Roman'  # USENIX/NDSS: Linux
elif system == 'Darwin':
    serif_font = 'Times'         # USENIX/NDSS: MacOS
else:
    serif_font = 'serif'         # Fallback option

# Set the default plot style with seaborn using a uniform look
sns.set_theme(style="whitegrid", rc={
    'font.family': 'serif',
    'font.serif': serif_font,
    'font.size': 10,
    'legend.fontsize': 10,
    'axes.labelsize': 10,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'xtick.major.size': 0,
    'xtick.minor.size': 0,
    'ytick.major.size': 0,
    'ytick.minor.size': 0,
    'patch.force_edgecolor': False,
    'legend.fancybox': False,
    'mathtext.default': 'regular',
    'axes.linewidth': 1.0,
    'text.color': 'black',
    'xtick.color': 'black',
    'ytick.color': 'black',
})
