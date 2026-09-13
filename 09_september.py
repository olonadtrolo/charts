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
end_date = "2026-09-11"


# halloween
compare("10014718", "1692943563", end_date, start_date="2026-08-15", imgur=imgur)
# onimusha
compare("10013248", "2131196662", end_date, imgur=imgur)
