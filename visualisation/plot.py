import numpy as np
import math

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

from everest.disk import tempname
from ._fig import Fig as _Fig
from .. import analysis

def get_rectilinear_plot(
        *args,
        lims = None,
        labels = None,
        title = '',
        size = None,
        ticksPerInch = 1,
        slicer = slice(None, None, None),
        canvas_kws = {},
        plot_kws = {}
        ):
    if lims is None: lims = [[None, None] for arg in args]
    if labels is None: labels = ['' for arg in args]
    if size is None: size = [3 for arg in args]
    labels = list(labels)
    ticks = [None for arg in args]
    ticklabels = [None for arg in args]
    for i, arg in enumerate(args):
        arg = arg[slicer]
        nTicks = ticksPerInch * size[i]
        ext, ticks[i], ticklabels[i], lims[i] = \
            auto_axis_configs(arg, lims[i], nTicks)
        labels[i] += '({0})'.format(ext)
    canvas = Canvas(size = size, **canvas_kws)
    plot = canvas._add_blank_rectilinear(
        labels = labels,
        title = title,
        lims = lims,
        ticks = ticks,
        ticklabels = ticklabels,
        **plot_kws
        )
    return canvas, plot

def line(*args, **kwargs):
    return quickPlot(*args, variety = 'line', **kwargs)
def scatter(*args, **kwargs):
    return quickPlot(*args, variety = 'scatter', **kwargs)

def quickPlot(
        x,
        y,
        # co_y = None,
        lims = None,
        variety = 'line',
        labels = ('', ''),
        title = '',
        size = (3., 3.),
        ticksPerInch = 1,
        **kwargs
        ):
    canvas, plot = get_rectilinear_plot(
        x,
        y,
        lims = lims,
        labels = labels,
        title = title,
        size = size,
        ticksPerInch = ticksPerInch
        )

    if variety == 'line':
        plot.plot(x, y, **kwargs)
    elif variety == 'scatter':
        plot.scatter(x, y, **kwargs)
    else:
        raise ValueError("Plot variety not recognised.")
    return canvas

def _get_nice_interval(lims, nTicks):
    bases = {1, 2, 5}
    nomInterval = (lims[1] - lims[0]) / nTicks
    powers = [(base, math.log10(nomInterval / base)) for base in bases]
    base, power = min(powers, key = lambda c: c[1] % 1)
    return base * 10. ** round(power)

def _make_nice_ticks(data, nTicks, lims = (None, None)):
    minD, maxD = np.min(data), np.max(data)
    if lims[0] is None: lims[0] = minD
    if lims[1] is None: lims[1] is maxD
    step = _get_nice_interval(lims, nTicks)
    start = lims[0] - lims[0] % step
    stop = lims[1]
    ticks = [start,]
    while ticks[-1] < stop + 0.5 * step:
        ticks.append(ticks[-1] + step)
    return np.array(ticks)

def _abbreviate_ticks(ticks):
    maxLog10 = math.log10(np.max(np.abs(ticks)))
    adjPower = - math.floor(maxLog10 / 3.) * 3
    adjTicks = np.round(ticks * 10. ** adjPower, 2)
    return adjTicks, -adjPower

def auto_axis_configs(data, lims = (None, None), nTicks = 5):
    minD, maxD = np.min(data), np.max(data)
    minCon = minD >= 0 and maxD > 2. * minD
    maxCon = maxD <= 0 and minD > 2. * maxD
    lims = list(lims)
    if lims[0] is None: lims[0] = 0. if minCon else minD
    if lims[1] is None: lims[1] = 0. if maxCon else maxD
    ticks = _make_nice_ticks(data, nTicks, lims)
    adjTicks, adjDataPower = _abbreviate_ticks(ticks)
    ticklabels = [str(tick) for tick in adjTicks]
    label = ''
    if abs(adjDataPower) > 0:
        label += 'E{0}'.format(adjDataPower)
    return label, ticks, ticklabels, lims

class Canvas(_Fig):

    def __init__(self,
            name = None,
            shape = (1, 1),
            share = (False, False),
            size = (3, 3), # inches
            dpi = 100, # pixels per inch
            facecolour = 'white',
            edgecolour = 'black',
            fig_kws = {},
            **kwargs
            ):

        fig = Figure(
            figsize = size,
            dpi = dpi,
            facecolor = facecolour,
            edgecolor = edgecolour,
            **{**kwargs, **fig_kws}
            )

        nrows, ncols = shape
        axes = [[None for col in range(ncols)] for row in range(nrows)]

        self.shape = shape
        self.nrows, self.ncols = nrows, ncols
        self.axes = axes

        self._updateFns = []
        self.fig = fig

        self._update_axeslist()

        super().__init__()

    def _update_axeslist(self):
        self.axesList = [item for sublist in self.axes for item in sublist]

    def _add_blank_plot(self,
            place = (0, 0),
            projection = 'rectilinear',
            share = (None, None),
            name = None,
            **kwargs
            ):

        if name is None:
            name = tempname()

        index = self._calc_index(place)
        if not self.axesList[index] is None:
            raise Exception("Already a plot at those coordinates.")

        ax = self.fig.add_subplot(
            self.nrows,
            self.ncols,
            index + 1,
            projection = projection,
            label = name,
            sharex = share[0],
            sharey = share[1],
            **kwargs
            )

        self.axes[place[0]][place[1]] = ax
        self._update_axeslist()

        return ax

    def _add_blank_rectilinear(self,
            place = (0, 0), # (x, y) coords of plot on canvas
            title = '', # the title to be printed on the plot
            position = None, # [left, bottom, width, height]
            margins = (0., 0.), # (xmargin, ymargin)
            lims = ((0., 1.), (0., 1.)), # ((float, float), (float, float))
            scales = ('linear', 'linear'), # (xaxis, yaxis)
            labels = ('', ''), # (xaxis, yaxis)
            grid = True,
            ticks = (
                [i / 10. for i in range(0, 11, 2)],
                [i / 10. for i in range(0, 11, 2)],
                ), # (ticks, ticks) OR ((ticks, labels), (ticks, labels))
            ticklabels = ([], []),
            share = (None, None), # (sharex, sharey)
            name = None, # provide a name to the Python object
            zorder = 0., # determines what overlaps what
            **kwargs # all other kwargs passed to axes constructor
            ):

        ax = self._add_blank_plot(
            place = place,
            projection = 'rectilinear',
            share = share,
            zorder = zorder,
            name = name,
            **kwargs
            )

        ax.set_xscale(scales[0])
        ax.set_yscale(scales[1])

        if all([lim is None for lim in lims[0]]):
            ax.set_xlim(auto = True)
        else:
            ax.set_xlim(*lims[0])
        if all([lim is None for lim in lims[1]]):
            ax.set_ylim(auto = True)
        else:
            ax.set_ylim(*lims[1])

        ax.set_xticks(ticks[0])
        ax.set_xticklabels(ticklabels[0], rotation = 'vertical')
        ax.set_yticks(ticks[1])
        ax.set_yticklabels(ticklabels[1])

        if grid:
            if type(grid) is float:
                alpha = grid
            else:
                alpha = 0.2
            ax.grid(which = 'major', alpha = alpha)

        ax.set_xlabel(labels[0])
        ax.set_ylabel(labels[1])

        ax.set_xmargin(margins[0])
        ax.set_ymargin(margins[1])

        ax.set_title(title)

        return ax

    # def add_

    def _calc_index(self, place):
        rowNo, colNo = place
        if colNo >= self.shape[0] or rowNo >= self.shape[1]:
            raise ValueError("Prescribed row and col do not exist.")
        return (self.ncols * rowNo + colNo)

    def __getitem__(self, arg):
        if type(arg) is int:
            return self.axGrid[arg]
        elif type(arg) is tuple:
            return self.axGrid[arg[0], arg[1]]
        elif type(arg) is str:
            raise TypeError("Accessing axes by name is not yet supported.")

    def _update(self):
        for fn in self._updateFns:
            fn()

    def _save(self, filepath):
        self.fig.savefig(filepath)

    def _show(self):
        FigureCanvas(self.fig)
        return self.fig
