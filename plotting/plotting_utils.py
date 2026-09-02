import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator
import matplotlib as mpl
import pandas as pd
import numpy as np
import itertools
import pyimgur
import colorcet as cc
from cycler import cycler
from plotting.plotting_config import PlotStyle

# Global Style Setup
colors = cc.glasbey[:20]
plt.rcParams["axes.prop_cycle"] = cycler(color=colors)


def render_plot(
    series_data: list, style: PlotStyle, show: bool = True, imgur: bool = False
):
    """
    Renders the plot based on the provided PlotStyle configuration.
    series_data: List of tuples (x, y_pos, y_pct, label, [optional_line_kwargs])
    """

    # 1. Apply Theme
    _apply_theme(style.dark_mode)

    # 2. Setup Figure
    fig, ax1 = plt.subplots(figsize=style.figsize)

    # Cycles for complex plots
    line_styles = itertools.cycle(["-", "--", "-.", ":"])
    markers = itertools.cycle(["o", "s", "D", "^", "v"])
    colors_cycle = itertools.cycle(colors)

    # Setup twin axes if double y-axis is requested
    if style.double_y:
        ax2 = ax1.twinx()
        if style.dark_mode:
            ax1.yaxis.label.set_color("white")
            ax2.yaxis.label.set_color("white")
            ax2.tick_params(colors="white")
    else:
        ax2 = None

    # 3. Render Lines
    for item in series_data:
        x = item[0]
        y_pos = item[1]
        y_pct = item[2] if len(item) > 2 else None
        label = item[3] if len(item) > 3 else "Title"
        extra = item[4] if len(item) > 4 else {}

        # Check if a custom color is specified in the options; fallback to cycle if not
        color = extra.get("color", next(colors_cycle))
        linestyle = extra.get("linestyle", next(line_styles))
        marker = extra.get("marker", next(markers))

        # Plot position (Rank) on left axis
        ax1.plot(
            x,
            y_pos,
            label=f"{label} (Rank)",
            color=color,
            linestyle=linestyle,
            marker=marker,
            linewidth=style.line_width,
            alpha=style.line_alpha,
            markersize=style.markersize,
        )

        # Plot percentage on right axis (shares the exact same color)
        if style.double_y and y_pct is not None and ax2 is not None:
            ax2.plot(
                x,
                y_pct,
                label=f"{label} (%)",
                color=color,
                linestyle=":",
                marker="x",
                linewidth=style.line_width,
                alpha=style.line_alpha * 0.7,
                markersize=style.markersize,
            )

    # 4. Axis Formatting
    ax1.invert_yaxis()  # Rank 1 is top
    ax1.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax1.set_xlabel(style.xlabel)
    ax1.set_ylabel(style.ylabel)

    if style.double_y and ax2 is not None:
        ax2.set_ylabel("Player Percentage (%)")
        all_pcts = [
            item[2].dropna()
            for item in series_data
            if len(item) > 2 and item[2] is not None
        ]
        if all_pcts:
            flat_pcts = pd.concat(all_pcts)
            if not flat_pcts.empty:
                ax2.set_ylim(0, flat_pcts.max() * 1.1)

    # Handle Date Formatting if X is datetime
    if len(series_data) > 0 and isinstance(
        series_data[0][0], (pd.DatetimeIndex, np.datetime64)
    ):
        ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))

    # 5. Labels & Titles
    if style.title:
        plt.title(style.title)

    # 6. Grid & Legend
    if style.grid:
        ax1.grid(**{"linestyle": "--", "alpha": 0.5, **style.grid_kwargs})

    if style.legend:
        # Combine handles and labels across both axes for a clean merged legend
        lines1, labels1 = ax1.get_legend_handles_labels()
        if style.double_y and ax2 is not None:
            lines2, labels2 = ax2.get_legend_handles_labels()
            lines = lines1 + lines2
            labels = labels1 + labels2
        else:
            lines, labels = lines1, labels1

        l_kwargs = style.legend_kwargs.copy()
        if style.dark_mode and "labelcolor" not in l_kwargs:
            l_kwargs["labelcolor"] = "white"
        ax1.legend(lines, labels, **l_kwargs)

    # 7. Custom Hooks
    if style.custom_hook:
        style.custom_hook(ax1)

    # 8. Finalize
    plt.tight_layout()

    if imgur:
        plt.savefig("output.png")
        if style.title:
            _upload_to_imgur("output.png", style.title)
        else:
            _upload_to_imgur("output.png", "")
    if show:
        plt.show()


def fill_isolated_nans_with_average(
    df: pd.DataFrame, column="position"
) -> pd.DataFrame:
    """Mathematical helper to smooth gaps."""
    if df.empty or column not in df.columns:
        return df
    df = df.copy()
    series = df[column]
    for i in range(1, len(series) - 1):
        if pd.isna(series.iloc[i]):
            if not pd.isna(series.iloc[i - 1]) and not pd.isna(series.iloc[i + 1]):
                avg = round((series.iloc[i - 1] + series.iloc[i + 1]) / 2)
                df.iloc[i, df.columns.get_loc(column)] = avg
    return df


# --- Internal Render Helpers ---


def _apply_theme(dark_mode: bool):
    if dark_mode:
        mpl.rcParams.update(
            {
                "figure.facecolor": "#121212",
                "axes.facecolor": "#121212",
                "axes.edgecolor": "#BBBBBB",
                "axes.labelcolor": "#FFFFFF",
                "xtick.color": "#DDDDDD",
                "ytick.color": "#DDDDDD",
                "text.color": "#FFFFFF",
                "legend.facecolor": "#1E1E1E",
                "grid.color": "#444444",
            }
        )
    else:
        mpl.rcParams.update(mpl.rcParamsDefault)


def _upload_to_imgur(filepath, title):
    CLIENT_ID = "5f93ce2d1b6aafd"
    try:
        im = pyimgur.Imgur(CLIENT_ID)
        uploaded = im.upload_image(filepath, title="Graph")
        print(f"""[SPOILER="{title}"][IMG]{uploaded.link}[/IMG][/SPOILER]""")
    except Exception as e:
        print(f"Imgur upload failed: {e}")
