import pandas as pd
from typing import Optional, Tuple, Any

import plotting.plotting_utils as u
from plotting.plotting_config import PlotStyle
from plotting.csv_plotter import CSVPlotter


class VersusPlotter:
    """
    Compares the tracker data of a PlayStation title directly against an Xbox title.
    """

    def __init__(self, base_dir: str = "charts/"):
        """
        Args:
            base_dir: Path to the root 'charts/' directory.
        """
        self.base_dir = base_dir

    def compare_platforms(
        self,
        ps_title_id: str,
        xbox_title_id: str,
        chart_type: str = "7_days",
        time_span: Optional[Tuple[Any, Any]] = None,
        launch_aligned: bool = False,
        style: Optional[PlotStyle] = None,
        show: bool = True,
        imgur: bool = False,
    ):
        """
        Fetch positions from both platforms for the given IDs and plot them side by side.

        Args:
            ps_title_id: Title ID from the PlayStation tracker.
            xbox_title_id: Title ID from the Xbox tracker.
            chart_type: 'daily' or '7_days'.
            time_span: String dates OR relative ints if launch_aligned is True.
            launch_aligned: Compare performance over days passed since official launch.
            style: Optional PlotStyle.
        """
        style = style or PlotStyle()

        # Initialize isolated plotters for each platform
        ps_csv = CSVPlotter(
            platform="ps", chart_type=chart_type, base_dir=self.base_dir
        )
        xbox_csv = CSVPlotter(
            platform="xbox", chart_type=chart_type, base_dir=self.base_dir
        )

        series_data = []

        # 1. Fetch PlayStation Data
        try:
            ps_df = ps_csv._fetch_positions(ps_title_id, time_span, launch_aligned)
            ps_df = u.fill_isolated_nans_with_average(ps_df, "position")
            if "percentage" in ps_df.columns:
                ps_df = u.fill_isolated_nans_with_average(ps_df, "percentage")

            if not ps_df.empty and not ps_df["position"].isna().all():
                ps_title = ps_csv._get_title_name(ps_title_id)
                series_data.append(
                    (
                        ps_df.index,
                        ps_df["position"],
                        ps_df["percentage"] if "percentage" in ps_df.columns else None,
                        f"{ps_title} (PlayStation)",
                        {"linestyle": "-", "marker": "o"},
                    )
                )
        except Exception as e:
            print(f"Warning: Could not fetch PlayStation data: {e}")

        # 2. Fetch Xbox Data
        try:
            resolved_xbox_id = xbox_csv._resolve_xbox_id(xbox_title_id)
            xbox_df = xbox_csv._fetch_positions(
                resolved_xbox_id, time_span, launch_aligned
            )
            xbox_df = u.fill_isolated_nans_with_average(xbox_df, "position")
            if "percentage" in xbox_df.columns:
                xbox_df = u.fill_isolated_nans_with_average(xbox_df, "percentage")

            if not xbox_df.empty and not xbox_df["position"].isna().all():
                xbox_title = xbox_csv._get_title_name(resolved_xbox_id)
                series_data.append(
                    (
                        xbox_df.index,
                        xbox_df["position"],
                        (
                            xbox_df["percentage"]
                            if "percentage" in xbox_df.columns
                            else None
                        ),
                        f"{xbox_title} (Xbox)",
                        {"linestyle": "--", "marker": "x"},
                    )
                )
        except Exception as e:
            print(f"Warning: Could not fetch Xbox data: {e}")

        # 3. Validation & Rendering
        if not series_data:
            raise ValueError(
                f"No tracker data found for IDs ({ps_title_id}, {xbox_title_id}) in '{chart_type}' charts."
            )

        if not style.title:
            names = " vs ".join([s[3].split(" (")[0] for s in series_data])
            style.title = f"{names} - PS vs Xbox ({chart_type})"

        if launch_aligned and style.xlabel == "Date":
            style.xlabel = "Days since launch"

        u.render_plot(series_data, style, show=show, imgur=imgur)
