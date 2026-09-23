import os
import glob
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from typing import List, Optional, Tuple, Dict

# Imports from the repository's plotting suite
import plotting.plotting_utils as u
from plotting.plotting_config import PlotStyle


class CSVvsDBPlotter:
    def __init__(self, csv_dir: str = "charts/xbox/ungrouped"):
        """
        Initializes the plotter, automatically setting up the DB connection
        and configuring the path to the CSV charts.
        """
        self.csv_dir = csv_dir

        # Load environment variables for the database
        load_dotenv()
        sql_connection = os.getenv("SQL_CONNECTION")
        if not sql_connection:
            raise ValueError("SQL_CONNECTION environment variable not found in .env")

        # Establish DB Engine and Session factory
        self.engine = create_engine(sql_connection)
        self.Session = sessionmaker(bind=self.engine)

        # Target Region ID for the Xbox US Store
        self.region_id = 1

    def _fetch_db_positions(self, session, product_id: str) -> pd.DataFrame:
        """
        Fetches chart position data from the SQL database for the Xbox US store.
        """
        product_id = str(product_id).strip().upper()

        sql_dates = text(
            "SELECT DISTINCT date FROM charts WHERE region_id = :rid ORDER BY date"
        )
        all_dates = pd.read_sql(sql_dates, session.bind, params={"rid": self.region_id})

        if all_dates.empty:
            return pd.DataFrame(columns=["position"], index=pd.to_datetime([]))

        sql_pos = text("""
            SELECT date, position FROM charts 
            WHERE region_id = :rid AND product_id = :pid 
            ORDER BY date
        """)
        pid_positions = pd.read_sql(
            sql_pos, session.bind, params={"rid": self.region_id, "pid": product_id}
        )

        result = (
            all_dates.merge(pid_positions, on="date", how="left")
            .set_index("date")
            .sort_index()
            .astype({"position": "Int64"})
        )
        result.index = pd.to_datetime(result.index)
        return result

    def _fetch_csv_positions(self, title_id: str) -> pd.DataFrame:
        """
        Fetches chart position data from the CSV database (charts/xbox/ungrouped).
        Normalizes column names to avoid KeyErrors from unpredictable CSV capitalization.
        """
        title_id = str(title_id).strip()
        df_list = []

        # Scenario A: Files are structured as one CSV per title (e.g. 12345.csv)
        specific_file = os.path.join(self.csv_dir, f"{title_id}.csv")

        if os.path.exists(specific_file):
            df = pd.read_csv(specific_file)
            df.columns = df.columns.str.lower()

            # Map 'rank' to 'position' if necessary
            if "rank" in df.columns and "position" not in df.columns:
                df = df.rename(columns={"rank": "position"})

            if "date" in df.columns and "position" in df.columns:
                df_list.append(df)
        else:
            # Scenario B: Files are dumped by date/week, we must scan the directory
            csv_files = glob.glob(os.path.join(self.csv_dir, "*.csv"))
            for file in csv_files:
                try:
                    # Sniff columns
                    header_df = pd.read_csv(file, nrows=0)
                    orig_cols = header_df.columns.tolist()
                    lower_cols = [c.lower() for c in orig_cols]

                    if "title_id" not in lower_cols:
                        continue

                    # Target 'position' or 'rank'
                    has_pos = "position" in lower_cols
                    has_rank = "rank" in lower_cols

                    if not (has_pos or has_rank):
                        continue

                    # Find exact original column names so pd.read_csv doesn't crash
                    usecols = [
                        orig
                        for orig, low in zip(orig_cols, lower_cols)
                        if low in ["title_id", "date", "position", "rank"]
                    ]

                    df = pd.read_csv(file, usecols=usecols)
                    df.columns = df.columns.str.lower()

                    if "rank" in df.columns and "position" not in df.columns:
                        df = df.rename(columns={"rank": "position"})

                    df["title_id"] = df["title_id"].astype(str)

                    match = df[df["title_id"] == title_id]
                    if not match.empty:
                        # Infer date from filename if missing
                        if "date" not in match.columns:
                            date_str = (
                                os.path.basename(file).replace(".csv", "").split("_")[0]
                            )
                            match = match.copy()
                            match["date"] = pd.to_datetime(date_str)
                        df_list.append(match)
                except Exception:
                    pass

        # If absolutely no data matched the criteria
        if not df_list:
            return pd.DataFrame(columns=["position"], index=pd.to_datetime([]))

        combined = pd.concat(df_list, ignore_index=True)

        # Hard fail-safe against the KeyError
        if "position" not in combined.columns:
            return pd.DataFrame(columns=["position"], index=pd.to_datetime([]))

        combined["date"] = pd.to_datetime(combined["date"])

        # Group by date in case of duplicates (taking the highest chart position / lowest int)
        combined = combined.groupby("date")["position"].min().reset_index()
        combined = combined.set_index("date").sort_index()

        # Explicitly build an unbroken date range to expose NaN gaps to the interpolation function
        full_range = pd.date_range(start=combined.index.min(), end=combined.index.max())
        combined = combined.reindex(full_range)
        combined.index.name = "date"

        combined = combined.astype({"position": "Int64"})
        return combined

    def compare_titles(
        self,
        comparisons: List[Dict[str, str]],
        time_span: Optional[Tuple[str, str]] = None,
        style: Optional[PlotStyle] = None,
        show: bool = True,
        imgur: bool = False,
    ):
        """
        Plots a visual comparison between CSV and DB data for one or more titles.
        """
        style = style or PlotStyle()
        series_data = []

        parsed_span = None
        if time_span:
            parsed_span = (pd.to_datetime(time_span[0]), pd.to_datetime(time_span[1]))

        with self.Session() as session:
            for item in comparisons:
                title = item.get("title", "Unknown Title")
                title_id = item.get("title_id")
                product_id = item.get("product_id")

                # --- Fetch CSV Tracker Data ---
                if title_id:
                    df_csv = self._fetch_csv_positions(title_id)
                    df_csv = u.fill_isolated_nans_with_average(df_csv)

                    if parsed_span:
                        df_csv = df_csv.loc[parsed_span[0] : parsed_span[1]]

                    if not df_csv.empty and not df_csv["position"].isna().all():
                        series_data.append(
                            (
                                df_csv.index,
                                df_csv["position"],
                                f"{title} (CSV Dataset)",
                                {"linestyle": "--", "marker": "x"},
                            )
                        )
                    else:
                        print(
                            f"Warning: No valid CSV data found for title '{title}' (ID: {title_id})"
                        )

                # --- Fetch DB Xbox US Data ---
                if product_id:
                    df_db = self._fetch_db_positions(session, product_id)
                    df_db = u.fill_isolated_nans_with_average(df_db)

                    if parsed_span:
                        df_db = df_db.loc[parsed_span[0] : parsed_span[1]]

                    if not df_db.empty and not df_db["position"].isna().all():
                        series_data.append(
                            (
                                df_db.index,
                                df_db["position"],
                                f"{title} (DB Xbox US)",
                                {"linestyle": "-", "marker": "o"},
                            )
                        )
                    else:
                        print(
                            f"Warning: No DB data found for title '{title}' (Product ID: {product_id})"
                        )

        if not series_data:
            print("No data available to plot for the provided titles.")
            return

        if not style.title:
            title_names = ", ".join([c.get("title", "Game") for c in comparisons])
            style.title = f"Data Origin Comparison: {title_names}"

        u.render_plot(series_data, style, show=show, imgur=imgur)

    def __del__(self):
        """Cleanup connection pool properly when plotter instance is garbage collected."""
        if hasattr(self, "engine"):
            self.engine.dispose()
