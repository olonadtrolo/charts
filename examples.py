# %%
from plotting.csv_plotter import CSVPlotter
from plotting.plotting_config import PlotStyle

style = PlotStyle(double_y=True)
plotter = CSVPlotter("xbox")

plotter.compare_titles(
    ["267695549", "342226876"], time_span=["2026-06-01", "2026-06-30"], style=style
)

# %%
plotter.compare_titles(["94618376", "1794906646"])
# %%
from plotting.versus_plotter import VersusPlotter

style = PlotStyle(double_y=True)
plotter = VersusPlotter()

plotter.compare_platforms(
    "10013987", "1661962317", time_span=["2026-07-15", "2026-08-30"], style=style
)

# %%
from plotting.versus_plotter import VersusPlotter

style = PlotStyle(double_y=True)
plotter = VersusPlotter()

plotter.compare_platforms(
    "10013987", "1661962317", time_span=["2026-07-15", "2026-08-30"], style=style
)

# %%


from plotting.versus_plotter import VersusPlotter

style = PlotStyle(double_y=True)
plotter = VersusPlotter()

plotter.compare_platforms(
    "10014022", "1921196301", launch_aligned=True, time_span=[5, 15], style=style
)

# %%

from plotting.versus_plotter import VersusPlotter

style = PlotStyle(double_y=True)
plotter = VersusPlotter()

plotter.compare_platforms(
    "10010058", "1645215415", launch_aligned=True, time_span=[0, 15], style=style
)
# %%
plotter.compare_platforms(
    "10010058", "1645215415", launch_aligned=True, time_span=[0, 15], style=style
)
