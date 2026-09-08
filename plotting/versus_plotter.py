import pandas as pd
from typing import Optional, Tuple, Any
import copy

import plotting.plotting_utils as u
from plotting.plotting_config import PlotStyle
from plotting.csv_plotter import CSVPlotter


class VersusPlotter:
    """
    Compares tracker data of PlayStation titles directly against Xbox titles.
    Supports single or multiple title comparisons across platforms.
    """

    def __init__(self, base_dir: str = "charts/"):
        """
        Args:
            base_dir: Path to the root 'charts/' directory.
        """
        self.base_dir = base_dir

    def compare_platforms(
        self,
        ps_title_ids: str | list,
        xbox_title_ids: str | list,
        chart_type: str = "7_days",
        time_span: Optional[Tuple[Any, Any]] = None,
        launch_aligned: bool = False,
        style: Optional[PlotStyle] = None,
        show: bool = True,
        imgur: bool = False,
    ):
        """
        Fetch positions from both platforms for the given list of IDs and plot them on a single chart.

        Args:
            ps_title_ids: A single title ID string or a list of title ID strings from the PlayStation tracker.
            xbox_title_ids: A single title ID string or a list of title ID strings from the Xbox tracker.
            chart_type: 'daily' or '7_days'.
            time_span: String dates OR relative ints if launch_aligned is True.
            launch_aligned: Compare performance over days passed since official launch.
            style: Optional PlotStyle.
        """
        # Clone the style configuration to prevent cross-plot state pollution
        style = copy.copy(style) if style else PlotStyle()

        # Coerce single string inputs into lists for uniform handling
        if isinstance(ps_title_ids, str):
            ps_title_ids = [ps_title_ids]
        if isinstance(xbox_title_ids, str):
            xbox_title_ids = [xbox_title_ids]

        # Initialize isolated plotters for each platform
        ps_csv = CSVPlotter(
            platform="ps", chart_type=chart_type, base_dir=self.base_dir
        )
        xbox_csv = CSVPlotter(
            platform="xbox", chart_type=chart_type, base_dir=self.base_dir
        )

        series_data = []

        # Color and marker palettes to preserve visual identity across multiple lines
        ps_colors = ["#2E67F8", "#00A8FF", "#5B86FF", "#1B4DFF"]
        xbox_colors = ["#107C10", "#00E676", "#3CD070", "#1E5A1E"]

        ps_markers = ["o", "s", "^", "D"]
        xbox_markers = ["x", "+", "1", "*"]

        # 1. Fetch PlayStation Data
        for idx, ps_title_id in enumerate(ps_title_ids):
            try:
                ps_df = ps_csv._fetch_positions(ps_title_id, time_span, launch_aligned)
                ps_df = u.fill_isolated_nans_with_average(ps_df, "position")
                if "percentage" in ps_df.columns:
                    ps_df = u.fill_isolated_nans_with_average(ps_df, "percentage")

                if not ps_df.empty and not (
                    ps_df["position"].isna().all() and ps_df["percentage"].isna().all()
                ):
                    ps_title = ps_csv._get_title_name(ps_title_id)
                    color = ps_colors[idx % len(ps_colors)]
                    marker = ps_markers[idx % len(ps_markers)]
                    series_data.append(
                        (
                            ps_df.index,
                            ps_df["position"],
                            (
                                ps_df["percentage"]
                                if "percentage" in ps_df.columns
                                else None
                            ),
                            f"{ps_title} (PlayStation)",
                            {"linestyle": "-", "marker": marker, "color": color},
                        )
                    )
            except Exception as e:
                print(
                    f"Warning: Could not fetch PlayStation data for ID {ps_title_id}: {e}"
                )

        # 2. Fetch Xbox Data
        for idx, xbox_title_id in enumerate(xbox_title_ids):
            try:
                resolved_xbox_id = xbox_csv._resolve_xbox_id(xbox_title_id)
                xbox_df = xbox_csv._fetch_positions(
                    resolved_xbox_id, time_span, launch_aligned
                )
                xbox_df = u.fill_isolated_nans_with_average(xbox_df, "position")
                if "percentage" in xbox_df.columns:
                    xbox_df = u.fill_isolated_nans_with_average(xbox_df, "percentage")

                if not xbox_df.empty and not (
                    xbox_df["position"].isna().all()
                    and xbox_df["percentage"].isna().all()
                ):
                    xbox_title = xbox_csv._get_title_name(resolved_xbox_id)
                    color = xbox_colors[idx % len(xbox_colors)]
                    marker = xbox_markers[idx % len(xbox_markers)]
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
                            {"linestyle": "-", "marker": marker, "color": color},
                        )
                    )
            except Exception as e:
                print(f"Warning: Could not fetch Xbox data for ID {xbox_title_id}: {e}")

        # 3. Validation & Rendering
        if not series_data:
            raise ValueError(
                f"No tracker data found for the provided platform IDs in '{chart_type}' charts."
            )

        if not style.title:
            metric_label = "Engagement" if style.percentage_only else "Performance"
            style.title = f"Multi-Platform {metric_label} Comparison"

        if launch_aligned and style.xlabel == "Date":
            style.xlabel = "Days since launch"

        u.render_plot(series_data, style, show=show, imgur=imgur)
