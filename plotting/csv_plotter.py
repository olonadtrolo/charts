import pandas as pd
import os
from pathlib import Path
from typing import Optional, Tuple, Any
from datetime import datetime

import plotting.plotting_utils as u
from plotting.plotting_config import PlotStyle


class CSVPlotter:
    """
    Handles data extraction from CSV files in charts/ directory.
    Supports Xbox and PlayStation platforms, different compilation types,
    and launch-aligned timelines using local data CSVs.
    """

    def __init__(
        self,
        platform: str = "xbox",
        chart_type: str = "7_days",
        base_dir: str = "charts/",
    ):
        self.base_dir = Path(base_dir)
        self.platform = platform.lower()
        self._title_cache = {}
        self.metadata = pd.DataFrame()

        self._load_metadata()
        self.set_chart_type(chart_type)

    def set_chart_type(self, chart_type: str):
        # Maps compilation settings to directories in current conventions
        mapping = {
            "daily": "daily",
            "sliding": "7_days",
            "sliding window": "7_days",
            "7 day sliding": "7_days",
            "7_days": "7_days",
        }

        mapped_type = mapping.get(chart_type.lower(), chart_type)
        self.charts_dir = self.base_dir / self.platform / mapped_type

        if not self.charts_dir.exists():
            print(f"Warning: Charts directory not found: {self.charts_dir}")

    def _load_metadata(self):
        """Loads release dates and product titles dynamically from disk."""
        filename = (
            "data_xbox.csv" if self.platform == "xbox" else "data_playstation.csv"
        )
        # Search parent or current working folder
        path = Path(__file__).resolve().parent.parent / filename
        if not path.exists():
            path = Path(filename)

        if path.exists():
            try:
                df = pd.read_csv(path, dtype={"title_id": str})
                df.columns = [c.strip() for c in df.columns]
                self.metadata = df.set_index("title_id")
            except Exception as e:
                print(f"Warning: Failed to parse metadata file {filename}: {e}")
        else:
            print(f"Warning: Metadata file '{filename}' was not found.")

    def _resolve_xbox_id(self, title_id: str) -> str:
        """
        Looks up multi_stack.csv, redirects queries for grouped Xbox SKUs
        to the collapsed representative value, and logs an alert.
        """
        if self.platform != "xbox":
            return title_id

        path = Path(__file__).resolve().parent.parent / "multi_stack.csv"
        if not path.exists():
            path = Path("multi_stack.csv")

        if path.exists():
            try:
                df = pd.read_csv(path, dtype={"title_id": str})
                df.columns = [c.strip() for c in df.columns]

                df["title_id"] = df["title_id"].str.strip()
                t_col = "title_name" if "title_name" in df.columns else " title_name"
                df["title_name"] = df[t_col].str.strip()

                target_id = str(title_id).strip()
                if target_id in df["title_id"].values:
                    matched_name = df.loc[
                        df["title_id"] == target_id, "title_name"
                    ].values[0]
                    matched_group_ids = df.loc[
                        df["title_name"] == matched_name, "title_id"
                    ].values

                    # Convert to numeric values to evaluate the minimum collapsed representative
                    numeric_ids = []
                    for gid in matched_group_ids:
                        try:
                            numeric_ids.append((int(gid), gid))
                        except ValueError:
                            pass

                    if numeric_ids:
                        representative_id = min(numeric_ids, key=lambda x: x[0])[1]
                        if representative_id != target_id:
                            print(
                                f"Notice: Redirecting Xbox title_id {target_id} "
                                f"to representative group ID {representative_id} ('{matched_name}')."
                            )
                            return representative_id
            except Exception as e:
                print(f"Warning: Error resolving multi_stack.csv mapping: {e}")

        return title_id

    def _get_release_date(self, title_id: str) -> Optional[datetime]:
        """Fetches the release date from local platform CSV metadata."""
        resolved_id = self._resolve_xbox_id(title_id)
        if resolved_id in self.metadata.index:
            row = self.metadata.loc[resolved_id]
            date_val = (
                row.get("release_date")
                if isinstance(row, pd.Series)
                else row.iloc[0].get("release_date")
            )
            if pd.notna(date_val):
                try:
                    return pd.to_datetime(date_val)
                except Exception:
                    pass
        return None

    def plot_title(
        self,
        title_id: str,
        time_span: Optional[Tuple[Any, Any]] = None,
        launch_aligned: bool = False,
        style: Optional[PlotStyle] = None,
        show: bool = True,
        imgur: bool = False,
    ):
        style = style or PlotStyle()

        df = self._fetch_positions(title_id, time_span, launch_aligned)
        df = u.fill_isolated_nans_with_average(df, "position")
        if "percentage" in df.columns:
            df = u.fill_isolated_nans_with_average(df, "percentage")

        title_name = self._get_title_name(title_id)

        if df.empty or df["position"].isna().all():
            raise ValueError(f"No chart data found for title_id: {title_id}")

        series_data = [(df.index, df["position"], df["percentage"], title_name)]

        if not style.title:
            style.title = f"Chart Performance: {title_name}"

        if launch_aligned and style.xlabel == "Date":
            style.xlabel = "Days since launch"

        u.render_plot(series_data, style, show=show, imgur=imgur)

    def compare_titles(
        self,
        title_ids: list,
        time_span: Optional[Tuple[Any, Any]] = None,
        launch_aligned: bool = False,
        style: Optional[PlotStyle] = None,
        show: bool = True,
        imgur: bool = False,
    ):
        style = style or PlotStyle()

        series_data = []
        missing = []

        for title_id in title_ids:
            resolved_id = self._resolve_xbox_id(title_id)
            df = self._fetch_positions(resolved_id, time_span, launch_aligned)
            df = u.fill_isolated_nans_with_average(df, "position")
            if "percentage" in df.columns:
                df = u.fill_isolated_nans_with_average(df, "percentage")

            title_name = self._get_title_name(resolved_id)

            if df.empty or df["position"].isna().all():
                missing.append(title_id)
            else:
                series_data.append(
                    (df.index, df["position"], df["percentage"], title_name)
                )

        if missing:
            print(f"Warning: No chart data found for title_ids: {', '.join(missing)}")

        if not series_data:
            raise ValueError("No valid data found for any of the provided title_ids")

        if not style.title:
            style.title = (
                f"Chart Performance Comparison ({self.platform.upper()} CSV Data)"
            )

        if launch_aligned and style.xlabel == "Date":
            style.xlabel = "Days since launch"

        u.render_plot(series_data, style, show=show, imgur=imgur)

    def _fetch_positions(
        self,
        title_id: str,
        time_span: Optional[Tuple[Any, Any]] = None,
        launch_aligned: bool = False,
    ) -> pd.DataFrame:
        resolved_id = self._resolve_xbox_id(title_id)
        release_date = None
        start_date = None
        end_date = None

        if launch_aligned:
            release_date = self._get_release_date(resolved_id)
            if release_date:
                release_date = pd.to_datetime(release_date).tz_localize(None)
            else:
                print(
                    f"Warning: Could not find release date for {resolved_id}. Skipping data fetch."
                )
                return pd.DataFrame(
                    columns=["position", "percentage"],
                    index=pd.Index([], name="days_since_launch"),
                )

        if time_span:
            if launch_aligned and release_date:
                start_date = release_date + pd.Timedelta(days=time_span[0])
                end_date = release_date + pd.Timedelta(days=time_span[1])
            elif not launch_aligned:
                start_date = pd.to_datetime(time_span[0])
                end_date = pd.to_datetime(time_span[1])

        csv_files = sorted(self.charts_dir.glob("*.csv"))

        if not csv_files:
            return pd.DataFrame(
                columns=["position", "percentage"], index=pd.to_datetime([])
            )

        positions = []
        percentages = []
        dates = []

        for csv_file in csv_files:
            try:
                date_val = pd.to_datetime(csv_file.stem)  # YYYY-MM-DD
            except ValueError:
                continue

            if start_date and date_val < start_date:
                continue
            if end_date and date_val > end_date:
                continue

            try:
                df = pd.read_csv(csv_file, comment="#")
                df.columns = [c.strip() for c in df.columns]

                match = df[df["title_id"].astype(str).str.strip() == str(resolved_id)]

                if not match.empty:
                    positions.append(int(match.iloc[0]["rank"]))
                    percentages.append(match.iloc[0].get("percentage", pd.NA))
                    dates.append(date_val)

                    if resolved_id not in self._title_cache:
                        self._title_cache[resolved_id] = match.iloc[0]["title"]
                else:
                    positions.append(pd.NA)
                    percentages.append(pd.NA)
                    dates.append(date_val)

            except Exception as e:
                print(f"Warning: Error reading {csv_file}: {e}")
                continue

        if not dates:
            if launch_aligned:
                return pd.DataFrame(
                    columns=["position", "percentage"],
                    index=pd.Index([], name="days_since_launch"),
                )
            else:
                return pd.DataFrame(
                    columns=["position", "percentage"], index=pd.to_datetime([])
                )

        result = pd.DataFrame(
            {"position": positions, "percentage": percentages},
            index=pd.to_datetime(dates),
        )

        # Format index based on alignment
        if launch_aligned and release_date:
            result.index = (
                (result.index - release_date) / pd.Timedelta(days=1)
            ).astype(int)
            result.index.name = "days_since_launch"

            result = result.sort_index()
            if time_span:
                result = result.loc[time_span[0] : time_span[1]]
        else:
            result.index.name = "date"

        result = result.astype({"position": "Int64", "percentage": "Float64"})

        return result

    def _get_title_name(self, title_id: str) -> str:
        resolved_id = self._resolve_xbox_id(title_id)
        if resolved_id in self._title_cache:
            return self._title_cache[resolved_id]

        if resolved_id in self.metadata.index:
            row = self.metadata.loc[resolved_id]
            name_val = (
                row.get("title_name")
                if isinstance(row, pd.Series)
                else row.iloc[0].get("title_name")
            )
            if pd.notna(name_val):
                self._title_cache[resolved_id] = str(name_val)
                return str(name_val)

        return f"Title {resolved_id}"

    def get_available_dates(self) -> list:
        csv_files = sorted(self.charts_dir.glob("*.csv"))
        dates = []

        for csv_file in csv_files:
            try:
                date_val = pd.to_datetime(csv_file.stem)
                dates.append(date_val)
            except ValueError:
                continue

        return dates

    def search_titles(self, query: str, limit: int = 10) -> list:
        query_lower = query.lower()
        results = []
        seen_ids = set()

        csv_files = sorted(self.charts_dir.glob("*.csv"), reverse=True)[:30]

        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file, comment="#")
                df.columns = [c.strip() for c in df.columns]

                for _, row in df.iterrows():
                    title_id = str(row["title_id"])
                    title_name = row["title"]

                    if title_id in seen_ids:
                        continue

                    if query_lower in title_name.lower():
                        results.append((title_id, title_name))
                        seen_ids.add(title_id)

                        if len(results) >= limit:
                            return results

            except Exception:
                continue

        return results
