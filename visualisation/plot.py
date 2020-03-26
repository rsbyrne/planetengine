import numpy as np
import math

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

from everest.disk import tempname
from ._fig import Fig as _Fig
from .. import analysis

def _rectilinear(
        x,
        y,
        size = (3, 3),
        nTicks = 5,
        slicer = slice(None, None, None),
        fig_kws = {},
        plot_kws = {},
        **kwargs
        ):
    x, y = x[slicer], y[slicer]
    aspect = size[0] / size[1]
    nxticks, nyticks = round(aspect * nTicks), nTicks
    xticks = _make_nice_ticks(x, nxticks, 0.)
    yticks = _make_nice_ticks(y, nyticks - 1, 0.)
    yticks = np.append(yticks, yticks[-1] + yticks[-1] - yticks[-2])
    xticklabels = [str(val) for val in xticks]
    yticklabels = [str(val) for val in yticks]
    canvas = Canvas(size = size, **{**kwargs, **fig_kws})
    plot = canvas.add_rectilinear(
        labels = ('t', 'Nu'),
        lims = ((0., np.max(x)), (0., np.max(y))),
        ticks = (xticks, yticks),
        ticklabels = (xticklabels, yticklabels),
        **{**kwargs, **plot_kws}
        )
    return canvas, plot

def line(*args, line_kws = dict(), **kwargs):
    canvas, plot = _rectilinear(*args, **kwargs)
    plot.plot(*args, **line_kws)
    return canvas

def scatter(*args, scatter_kws = dict(), **kwargs):
    canvas, plot = _rectilinear(*args, **kwargs)
    plot.scatter(*args, **scatter_kws)
    return canvas

def _get_nice_interval(data, nTicks):
    bases = {1, 2, 5}
    maxNum = np.max(data)
    nomInterval = maxNum / nTicks
    checkDict = {base: math.log(nomInterval / base, 10.) % 1 for base in bases}
    base = min(checkDict, key = checkDict.get)
    power = round(math.log(nomInterval / base, 10.))
    interval = base * 10. ** power
    return interval

def _make_nice_ticks(data, nTicks, start = None):
    if start is None:
        start = np.min(data)
    stop = np.max(data)
    step = _get_nice_interval(data, nTicks)
    ticks = np.arange(start, stop, step)
    while ticks[-1] < stop:
        ticks = np.append(ticks, ticks[-1] + step)
    return ticks

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

    def add_plot(self,
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

    def add_rectilinear(self,
            place = (0, 0), # (x, y) coords of plot on canvas
            title = 'myplot', # the title to be printed on the plot
            position = None, # [left, bottom, width, height]
            margins = (0., 0.), # (xmargin, ymargin)
            lims = ((0., 1.), (0., 1.)), # ((float, float), (float, float))
            scales = ('linear', 'linear'), # (xaxis, yaxis)
            labels = ('x', 'y'), # (xaxis, yaxis)
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

        ax = self.add_plot(
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
