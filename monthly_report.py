# %%
import polars as pl
from plotting.csv_plotter import CSVPlotter
from plotting.versus_plotter import VersusPlotter
from plotting.plotting_config import PlotStyle

from datetime import datetime, timedelta

dfps = pl.read_csv("data_playstation.csv")
dfx = pl.read_csv("data_xbox.csv")


def retrieve_date_ps(title_id: str, df: pl.DataFrame | None = None):
    if df is None:
        df = pl.read_csv("data_playstation.csv")

    return df.filter(pl.col("title_id") == int(title_id)).select("release_date").item()


def retrieve_name_ps(title_id: str, df: pl.DataFrame | None = None):
    if df is None:
        df = pl.read_csv("data_playstation.csv")

    return df.filter(pl.col("title_id") == int(title_id)).select("title_name").item()


def retrieve_date_xbox(title_id: str, df: pl.DataFrame | None):
    if df is None:
        df = pl.read_csv("data_xbox.csv")

    return df.filter(pl.col("title_id") == int(title_id)).select("release_date").item()


def plot_ps_single_title(title_id: str, end_date: str, imgur: bool = False):

    title_name = retrieve_name_ps(title_id, dfps)

    start_date = datetime.strftime(
        datetime.strptime(retrieve_date_ps(title_id, df=dfps), r"%Y-%m-%d")
        + timedelta(days=4),
        r"%Y-%m-%d",
    )

    style = PlotStyle(double_y=True, title=title_name + " | Playstation")

    plotter = CSVPlotter(platform="ps")
    plotter.compare_titles(
        [
            title_id,
        ],
        time_span=[
            start_date,
            end_date,
        ],  # specifies the date range, otherwise it would plot the entire history of each title
        style=style,
        imgur=imgur,
    )


def compare(
    title_id_ps: str,
    title_id_xbox: str,
    end_date: str,
    start_date: str | None = None,
    imgur: bool = False,
):
    title_name = retrieve_name_ps(title_id_ps, dfps)
    title = title_name + " - Playstation vs Xbox"
    style = PlotStyle(double_y=True, title=title)

    plotter = VersusPlotter()
    if start_date is None:
        start_date = datetime.strftime(
            datetime.strptime(retrieve_date_ps(title_id_ps, df=dfps), r"%Y-%m-%d")
            + timedelta(days=4),
            r"%Y-%m-%d",
        )
    plotter.compare_platforms(
        title_id_ps,
        title_id_xbox,
        time_span=[start_date, end_date],
        style=style,
        imgur=imgur,
    )


# %%
imgur = False
big_walk = "10017189"
tokon = "10008019"
plot_ps_single_title(big_walk, "2026-09-11", imgur=imgur)
plot_ps_single_title(tokon, "2026-09-11", imgur=imgur)


# %%
# 10016736 = Madden
# 10008019 - Marvel Tokon
# 10010865 - LOTR Remaster
# 10016651 - Grounded 2
# 10014425 - Hell Let Loose: Vietnam
# 10014600 - Duskfade
# 10009208 - Sinking City 2
# 10015004 - Starsand Island
# 10017298 - CloverPit
# 10010058 - Mortal Shell II
# 10015762 - Once Human
# 10014695 - Aliens: Fireteam Elite 2
# 10009075 - METAL GEAR SOLID: MASTER COLLECTION Vol.2
# 10009029 - STAR WARS Zero Company™

# versusplotter

# %%
imgur = True
end_date = "2026-10-11"

# %% The Blood of Dawnwalker
compare("10013855", "1982295121", end_date, imgur=imgur)

# %% Onimusha
compare("10013248", "2131196662", end_date, imgur=imgur)

# %% nba
compare("10018502", "1731722945", end_date, imgur=imgur)

# %% crimson moon
compare("10013260", "2083389920", end_date, imgur=imgur)
# %% nhl

compare("10017367", "1700133950", end_date, imgur=imgur)
# %% halloween
compare("10014718", "1692943563", end_date, imgur=imgur)
# %% mewgenics
compare("10019219", "1748418988", end_date, imgur=imgur)
# %% valheim
compare("10014397", "1745661457", end_date, imgur=imgur)
# %% active matter
compare("10016388", "1619206606", end_date, imgur=imgur)

# %% runescape
compare("10017405", "2116052231", end_date, imgur=imgur)

# %% tcg
compare("10018739", "1689317374", end_date, imgur=imgur)


# %%
from datetime import date
from pathlib import Path

import polars as pl


def sep_top_title_ids(
    platform: str,
    start: date,
    end: date,
    top: int = 50,
    root: str | Path = r"C:\Projects\charts",
) -> list[int]:
    root = Path(root)
    platform_dir = root / "charts" / platform

    if platform == "ps":
        platform = "playstation"
    # 1. Titles released in [start, end)
    data_path = f"data_{platform}.csv"
    candidates = (
        pl.read_csv(data_path, columns=["title_id", "release_date"])
        .with_columns(pl.col("release_date").str.to_date("%Y-%m-%d"))
        .filter((pl.col("release_date") >= start) & (pl.col("release_date") < end))
        .get_column("title_id")
        .unique()
    )
    if candidates.is_empty():
        return []

    # 2. Scan daily chart files (YYYY-MM-DD.csv, not *_recent.csv)
    found: set[int] = set()

    for path in (platform_dir / "7_days").glob("????-??-??.csv"):
        file_date = date.fromisoformat(path.stem)

        if file_date < start:
            continue

        ids = (
            pl.read_csv(path, columns=["rank", "title_id"])
            .filter((pl.col("rank") <= top) & pl.col("title_id").is_in(candidates))
            .get_column("title_id")
            .to_list()
        )
        found.update(ids)

    return list(found)


#print(sep_top_title_ids("ps", date(2026, 9, 1), date(2026, 9, 16)))
#print(sep_top_title_ids("xbox", date(2026, 9, 1), date(2026, 9, 16)))


# %%
def monthly_report(
    platform: str, top: int, start: date, end: date, end_plot: date, imgur
):
    plotter = CSVPlotter(platform)

    def hook(ax):
        ax.set_ylim([top, 1])

    platforms_dist = {"ps": "Playstation", "xbox": "Xbox"}

    style = PlotStyle(
        custom_hook=hook,
        title=f"Overview of the {platforms_dist[platform]} early September releases that hit the top {top} at any point",
    )
    titles = sep_top_title_ids(platform, start, end, top=top)
    print(titles)
    plotter.compare_titles(
        titles,
        time_span=[start.strftime("%Y-%m-%d"), end_plot.strftime("%Y-%m-%d")],
        style=style,
        imgur=imgur,
    )


# %%
imgur = False
monthly_report("ps", 50, date(2026, 9, 16), date(2026, 10, 16), date.today(), imgur)
# %%
monthly_report("ps", 100, date(2026, 9, 16), date(2026, 10, 16), date.today(), imgur)
# %%
monthly_report("ps", 200, date(2026, 9, 16), date(2026, 10, 16), date.today(), imgur)
# %%
monthly_report("xbox", 50, date(2026, 9, 16), date(2026, 10, 16), date.today(), imgur)
# %%
monthly_report("xbox", 100, date(2026, 9, 16), date(2026, 10, 16), date.today(), imgur)

# %%
monthly_report("xbox", 200, date(2026, 9, 16), date(2026, 10, 16), date.today(), imgur)

# %%
plotter = CSVPlotter("xbox")


def hook(ax):
    ax.set_ylim([50, 1])


style = PlotStyle(
    custom_hook=hook,
    title="Overview of the Xbox early September releases that hit the top 50 at any point",
)

plotter.compare_titles(
    [1731722945, 1692943563, 1799950478, 2116052231],
    time_span=["2026-09-01", "2026-10-11"],
    style=style,
    imgur=imgur,
)

# %%
# %% resonance

compare("10015413", "1790707834", end_date, imgur=imgur)
# %%
!pip install colorcet
# %%
