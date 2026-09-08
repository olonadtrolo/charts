from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Callable, Tuple


@dataclass
class PlotStyle:
    """
    Configuration for chart plotting.
    """

    title: Optional[str] = None
    xlabel: str = "Date"
    ylabel: str = "Chart Position"

    # Visuals
    dark_mode: bool = True
    simple: bool = False  # If True, uses simple lines; False cycles markers/styles
    parallel: bool = False  # Ribbon/Parallel plot mode
    figsize: Tuple[int, int] = (12, 6)

    # Line properties
    line_width: int = 2
    line_alpha: float = 0.9
    markersize: float = 4.0

    # Double Y-axis setting (plots rank on left, playerbase percentage on right)
    double_y: bool = False
    percentage_only: bool = False

    # Advanced
    custom_hook: Optional[Callable] = None  # Function(ax) -> None
    grid: bool = True
    legend: bool = True

    # Internal Matplotlib kwargs
    legend_kwargs: Dict[str, Any] = field(default_factory=dict)
    grid_kwargs: Dict[str, Any] = field(default_factory=dict)
