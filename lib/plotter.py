"""Generic plotter interface for the irradiance figures."""

from abc import ABC, abstractmethod
from collections.abc import Callable

from matplotlib.figure import Figure

from lib.data import IrradianceData

PlotFunc = Callable[[IrradianceData, str, str], Figure]


class Plotter(ABC):
    """A named figure renderer for parsed irradiance data.

    Concrete plotters are usually created with the :func:`plotter` decorator,
    which wraps a plot function and sets ``name`` (used for automatic output
    filenames).
    """

    name: str

    @abstractmethod
    def plot(self, data: IrradianceData, cmap: str, ylabel: str) -> Figure:
        """Render the figure for one parsed input file.

        Args:
            data: Parsed irradiance data (norm, extent, datasets, bands).
            cmap: Matplotlib colormap name.
            ylabel: Label for irradiance values.

        Returns:
            The rendered figure; the caller decides whether to show or save it.
        """


class _FuncPlotter(Plotter):
    """Adapts a plot function into the Plotter interface."""

    def __init__(self, name: str, func: PlotFunc) -> None:
        self.name = name
        self._func = func

    def plot(self, data: IrradianceData, cmap: str, ylabel: str) -> Figure:
        return self._func(data, cmap, ylabel)


def plotter(name: str) -> Callable[[PlotFunc], Plotter]:
    """Turn a plot function into a named :class:`Plotter` instance.

    The decorated function must accept ``(data, cmap, ylabel)`` and return a
    matplotlib Figure.
    """

    def decorate(func: PlotFunc) -> Plotter:
        return _FuncPlotter(name, func)

    return decorate
