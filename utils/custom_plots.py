from __future__ import annotations
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Optional, List, Literal
import math
import scipy.stats as stats


def distribution_plot(
    df: pd.DataFrame,
    title: str = 'Distribution Overview',
    ignore_cols: Optional[List[str]] = None,
    top_n_categories: int = 10,
    n_cols: int = 2,
    show_mean_line: bool = True,
    show_median_line: bool = True,
    categorical_threshold: int = 10,
    figsize: tuple = (1400, None),
) -> go.Figure:
    """
    Create comprehensive EDA visualization for all columns in a DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe to analyze.
    title : str
        Main title for the plot.
    ignore_cols : list[str], optional
        Column names to exclude from visualization.
    top_n_categories : int
        Maximum number of categories to show individually (rest → "Other").
    n_cols : int
        Number of columns in the subplot grid.
    show_mean_line : bool
        Overlay mean line on numerical histograms.
    show_median_line : bool
        Overlay median line on numerical histograms.
    categorical_threshold : int
        Numeric columns with fewer unique values than this are treated as categorical.
    figsize : tuple
        (width, height). Height is auto-calculated when None.

    Returns
    -------
    plotly.graph_objects.Figure
    """

    # ── Colour palettes ────────────────────────────────────────────────────────
    NUMERICAL_COLORS = [
        '#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A',
        '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52',
    ]
    CATEGORICAL_COLORS = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
        '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5',
    ]
    OTHER_COLOR = '#4a4a4a'

    # ── Column selection ───────────────────────────────────────────────────────
    ignore_cols = ignore_cols or []
    cols_to_plot = [
        col for col in df.columns
        if col not in ignore_cols and df[col].notna().any()
    ]

    if not cols_to_plot:
        raise ValueError("No valid columns to plot after filtering.")

    # ── Column type classification ─────────────────────────────────────────────
    def _classify(col: str) -> str:
        s = df[col].dropna()
        if pd.api.types.is_datetime64_any_dtype(s):
            return 'categorical'
        if pd.api.types.is_categorical_dtype(s) or pd.api.types.is_object_dtype(s):
            return 'categorical'
        if pd.api.types.is_numeric_dtype(s):
            return 'categorical' if s.nunique() < categorical_threshold else 'numerical'
        return 'categorical'

    column_types = {col: _classify(col) for col in cols_to_plot}

    # ── Grid geometry ──────────────────────────────────────────────────────────
    n_plots = len(cols_to_plot)
    n_rows = math.ceil(n_plots / n_cols)

    spacing_map = {
        2: (0.10, 0.12),
        3: (0.07, 0.11),
        4: (0.05, 0.10),
    }
    h_spacing, v_spacing = spacing_map.get(n_cols, (0.03, 0.08))

    per_row_h = 380 if n_rows <= 3 else (320 if n_rows <= 6 else 270)
    height = figsize[1] if figsize[1] is not None else n_rows * per_row_h

    # ── Subplots ───────────────────────────────────────────────────────────────
    fig = make_subplots(
        rows=n_rows,
        cols=n_cols,
        subplot_titles=cols_to_plot,
        vertical_spacing=v_spacing,
        horizontal_spacing=h_spacing,
    )

    categorical_ymax: dict[tuple[int, int], float] = {}
    stats_annotations: list[dict] = []

    # ── Per-column traces ──────────────────────────────────────────────────────
    for idx, col in enumerate(cols_to_plot):
        row     = idx // n_cols + 1
        col_pos = idx  % n_cols + 1
        col_data = df[col].dropna()

        # Axis reference strings (Plotly uses 'x'/'y' for the first subplot,
        # 'x2'/'y2' for the second, etc.)
        axis_suffix = '' if idx == 0 else str(idx + 1)
        xref        = f'x{axis_suffix}'
        yref        = f'y{axis_suffix}'
        xref_domain = f'x{axis_suffix} domain'
        yref_domain = f'y{axis_suffix} domain'

        if column_types[col] == 'numerical':
            fig.add_trace(
                go.Histogram(
                    x=col_data,
                    name=col,
                    marker_color=NUMERICAL_COLORS[idx % len(NUMERICAL_COLORS)],
                    showlegend=False,
                    autobinx=True,
                ),
                row=row, col=col_pos,
            )

            mean_val   = col_data.mean()
            median_val = col_data.median()

            if show_mean_line:
                fig.add_shape(
                    type='line',
                    x0=mean_val, x1=mean_val, y0=0, y1=1,
                    xref=xref, yref=yref_domain,
                    line=dict(color='#FFD700', width=2.5, dash='dash'),
                )
            if show_median_line:
                fig.add_shape(
                    type='line',
                    x0=median_val, x1=median_val, y0=0, y1=1,
                    xref=xref, yref=yref_domain,
                    line=dict(color='#FF6B6B', width=2.5, dash='dot'),
                )

            annotation_lines = []
            if show_mean_line:
                annotation_lines.append(f'<span style="color:#FFD700;">━━</span> Mean: {mean_val:.2f}')
            if show_median_line:
                annotation_lines.append(f'<span style="color:#FF6B6B;">⋯⋯</span> Median: {median_val:.2f}')

            if annotation_lines:
                stats_annotations.append(dict(
                    text='<br>'.join(annotation_lines),
                    xref=xref_domain, yref=yref_domain,
                    x=0.98, y=0.98,
                    xanchor='right', yanchor='top',
                    showarrow=False,
                    font=dict(size=10, color='#fafafa'),
                    bgcolor='rgba(0,0,0,0.6)',
                    bordercolor='#2d2d2d',
                    borderwidth=1,
                    borderpad=4,
                ))

        else:  # categorical
            value_counts = col_data.value_counts()
            total        = len(col_data)

            if len(value_counts) > top_n_categories:
                top  = value_counts.head(top_n_categories)
                rest = value_counts.iloc[top_n_categories:].sum()
                categories = [*top.index,  'Other']
                counts     = [*top.values, rest]
                colors     = [
                    CATEGORICAL_COLORS[i % len(CATEGORICAL_COLORS)]
                    for i in range(top_n_categories)
                ] + [OTHER_COLOR]
            else:
                categories = list(value_counts.index)
                counts     = list(value_counts.values)
                colors     = [
                    CATEGORICAL_COLORS[i % len(CATEGORICAL_COLORS)]
                    for i in range(len(categories))
                ]

            pcts = [round(c / total * 100, 2) for c in counts]

            # Sort descending by count
            order      = sorted(range(len(counts)), key=lambda i: counts[i], reverse=True)
            categories = [categories[i] for i in order]
            counts     = [counts[i]     for i in order]
            pcts       = [pcts[i]       for i in order]
            colors     = [colors[i]     for i in order]

            # ── FIX: give the tallest bar enough room so its outside label
            #    is never clipped.  1.25× headroom (vs the old 1.15×) combined
            #    with disabling uniformtext_mode='hide' (see layout below)
            #    guarantees the label always renders.
            categorical_ymax[(row, col_pos)] = max(counts) * 1.25

            fig.add_trace(
                go.Bar(
                    x=categories,
                    y=counts,
                    name=col,
                    marker_color=colors,
                    showlegend=False,
                    text=[f'{p}%' for p in pcts],
                    textposition='outside',
                    textfont=dict(size=10),
                    hovertext=[
                        f'{cat}<br>Count: {n}<br>Percentage: {p}%'
                        for cat, n, p in zip(categories, counts, pcts)
                    ],
                    hoverinfo='text',
                    cliponaxis=False,
                ),
                row=row, col=col_pos,
            )

    # ── Layout ─────────────────────────────────────────────────────────────────
    fig.update_layout(
        template='plotly_dark',
        height=height,
        width=figsize[0],
        autosize=False,
        title_text=title,
        title_font_size=24,
        title_x=0.5,
        showlegend=False,
        plot_bgcolor='#0e1117',
        paper_bgcolor='#0e1117',
        font=dict(color='#fafafa', size=12),
        # ── FIX: 'hide' was silently suppressing the label on the tallest bar
        #    because Plotly couldn't fit it at the uniform minimum size within
        #    the (too-tight) headroom.  'show' forces all labels to render.
        uniformtext_minsize=8,
        uniformtext_mode='show',
        annotations=list(fig.layout.annotations) + stats_annotations,
    )

    fig.update_xaxes(
        showgrid=True,
        gridwidth=0.5,
        gridcolor='#2d2d2d',
        tickangle=-45,
        tickfont=dict(size=10),
    )
    fig.update_yaxes(
        showgrid=True,
        gridwidth=0.5,
        gridcolor='#2d2d2d',
    )

    # Apply per-subplot y-axis ceiling for categorical plots
    for (r, c), ymax in categorical_ymax.items():
        fig.update_yaxes(range=[0, ymax], row=r, col=c)

    return fig



def box_plot(
    df: pd.DataFrame,
    ignore_list: Optional[List[str]] = None,
    whis: float = 1.5,
    orientation: Literal['horizontal', 'vertical'] = 'horizontal',
    n_cols: int = 2,
    title: Optional[str] = "Box Plot Overview",
    width: int = 1400
) -> go.Figure:
    """
    Create box plots for numerical columns with outlier detection.
    Each column gets its own subplot with an independent scale.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    ignore_list : list of str, optional
        Columns to exclude from plotting.
    whis : float, default 1.5
        IQR multiplier for whisker / outlier fence calculation.
    orientation : {'vertical', 'horizontal'}, default 'horizontal'
        'vertical'   – boxes are drawn vertically (value on y-axis).
        'horizontal' – boxes are drawn horizontally (value on x-axis).
    n_cols : int, default 2
        Number of columns in the subplot grid. Rows are calculated
        automatically as ceil(n_numerical_cols / n_cols).
    title : str, optional
        Main figure title.

    Returns
    -------
    plotly.graph_objects.Figure
    """
    if ignore_list is None:
        ignore_list = []

    numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    numerical_cols = [col for col in numerical_cols if col not in ignore_list]
    if not numerical_cols:
        raise ValueError("No numerical columns found after applying ignore_list")

    n = len(numerical_cols)
    colors = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A',
              '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52']

    # ── Layout dimensions ─────────────────────────────────────────────────────
    n_rows = int(np.ceil(n / n_cols))
    cols_n = n_cols

    # Dynamic spacing — tightens as the grid grows to maximise plot area
    if n_cols <= 2:
        h_spacing = 0.10
        v_spacing = 0.12
    elif n_cols == 3:
        h_spacing = 0.07
        v_spacing = 0.11
    elif n_cols == 4:
        h_spacing = 0.05
        v_spacing = 0.10
    else:  # 5+ columns
        h_spacing = 0.03
        v_spacing = 0.08

    # Dynamic per-row height: progressively compact for larger grids
    per_row_h = 380 if n_rows <= 3 else (320 if n_rows <= 6 else 270)
    plot_height = n_rows * per_row_h

    fig = make_subplots(
        rows=n_rows, cols=cols_n,
        subplot_titles=numerical_cols,
        horizontal_spacing=h_spacing,
        vertical_spacing=v_spacing,
    )

    # ── Add box traces & compute outlier stats ────────────────────────────────
    outlier_stats = []
    for idx, col in enumerate(numerical_cols):
        data = df[col].dropna()
        q1, q3 = data.quantile(0.25), data.quantile(0.75)
        iqr = q3 - q1

        # Whiskers extend to the last actual data point inside the IQR fence
        lo_fence = q1 - whis * iqr
        hi_fence = q3 + whis * iqr
        lo_whisker = data[data >= lo_fence].min()
        hi_whisker = data[data <= hi_fence].max()

        outliers = data[(data < lo_whisker) | (data > hi_whisker)]
        outlier_stats.append((len(outliers), len(outliers) / len(data) * 100))

        r = idx // n_cols + 1
        c = idx % n_cols + 1

        # Vertical boxes use y; horizontal boxes use x
        box_data = dict(y=data) if orientation == 'vertical' else dict(x=data)
        fig.add_trace(go.Box(
            **box_data,
            name='',
            marker_color=colors[idx % len(colors)],
            boxmean=False,
            showlegend=False,
            marker=dict(
                size=5,
                outliercolor='rgba(220,220,220,0.7)',
                line=dict(outliercolor='rgba(220,220,220,0.7)', outlierwidth=1),
            ),
            line=dict(width=2),
        ), row=r, col=c)

    # ── Build outlier-stat annotations ────────────────────────────────────────
    annotations = list(fig.layout.annotations)
    for idx in range(n):
        n_out, pct = outlier_stats[idx]
        axis_idx = '' if idx == 0 else str(idx + 1)
        x_axis_key = f'xaxis{axis_idx}'
        y_axis_key = f'yaxis{axis_idx}'
        x_domain = fig.layout[x_axis_key].domain
        y_domain = fig.layout[y_axis_key].domain

        if orientation == 'vertical':
            # Boxes are vertical → annotate below each subplot using its own domains
            x_center = (x_domain[0] + x_domain[1]) / 2
            y_bottom = y_domain[0] - 0.02
            annotations.append(dict(
                text=f"Outliers: {n_out} ({pct:.1f}%)",
                xref='paper', yref='paper',
                x=x_center, y=y_bottom,
                xanchor='center', yanchor='top',
                showarrow=False,
                font=dict(size=11, color='#FFD700'),
                bgcolor='rgba(0,0,0,0.5)',
                bordercolor='#FFD700', borderwidth=1, borderpad=4,
            ))
        else:
            # Boxes are horizontal → annotate INSIDE the subplot, top-right corner
            x_right  = x_domain[1] - 0.005   # just inside the right edge
            y_top    = y_domain[1]            # top of the subplot domain
            annotations.append(dict(
                text=f"Outliers: {n_out} ({pct:.1f}%)",
                xref='paper', yref='paper',
                x=x_right, y=y_top,
                xanchor='right', yanchor='top',   # anchor pulls it inward
                showarrow=False,
                font=dict(size=11, color='#FFD700'),
                bgcolor='rgba(0,0,0,0.5)',
                bordercolor='#FFD700', borderwidth=1, borderpad=4,
            ))

    # ── Layout ────────────────────────────────────────────────────────────────

    fig.update_layout(
        title=dict(
            text=title or "Outlier Analysis",
            font=dict(size=18, color='white'),
            x=0.5, xanchor='center',
        ),
        template='plotly_dark',
        width=width,
        height=plot_height,
        showlegend=False,
        paper_bgcolor='#0e1117',
        plot_bgcolor='#1a1a1a',
        font=dict(color='white'),
        annotations=annotations,
    )

    # ── Axis tick-label visibility ────────────────────────────────────────────
    if orientation == 'vertical':
        # Boxes are vertical (y = value range) → x labels are meaningless
        fig.update_xaxes(showticklabels=False, showgrid=True,
                         gridwidth=0.5, gridcolor='rgba(128,128,128,0.2)')
        fig.update_yaxes(showticklabels=True,  showgrid=True,
                         gridwidth=0.5, gridcolor='rgba(128,128,128,0.2)')
    else:
        # Boxes are horizontal (x = value range) → y labels are meaningless
        fig.update_xaxes(showticklabels=True,  showgrid=True,
                         gridwidth=0.5, gridcolor='rgba(128,128,128,0.2)')
        fig.update_yaxes(showticklabels=False, showgrid=True,
                         gridwidth=0.5, gridcolor='rgba(128,128,128,0.2)')

    return fig


PALETTE = [
    "#636EFA", "#EF553B", "#00CC96", "#AB63FA",
    "#FFA15A", "#19D3F3", "#FF6692",
]

_DARK_BG   = "#0e1117"
_PLOT_BG   = "#1a1a1a"
_GRID_CLR  = "rgba(128,128,128,0.2)"
_FONT_CLR  = "white"


def cross_tab_heatmap(
    df: pd.DataFrame,
    col1: str,
    col2: str,
    ignore_cols: list = [],
    normalize: bool = True,
    title: str = "",
) -> go.Figure:
    """
    Crosstab heatmap: does the distribution of col2 shift across levels of col1?

    Each row is one category of col1.  When normalize=True the values are row
    percentages (each row sums to 100 %) so the colour encodes composition
    rather than raw counts — useful when categories have very different sizes.

    Parameters
    ----------
    df : pd.DataFrame
    col1 : str
        Row dimension (y-axis).
    col2 : str
        Column dimension (x-axis).
    ignore_cols : list
        Columns to skip — not used in the crosstab itself but kept for API
        consistency with the rest of the library.
    normalize : bool, default True
        Row-normalise the crosstab to percentages.
    title : str
        Figure title.  Defaults to "col1 × col2".

    Returns
    -------
    go.Figure
    """
    working = df.drop(columns=[c for c in ignore_cols if c in df.columns])

    ct = pd.crosstab(working[col1], working[col2])

    if normalize:
        z      = ct.div(ct.sum(axis=1), axis=0) * 100
        fmt    = ".1f"
        cbar_title = "Row %"
    else:
        z      = ct.astype(float)
        fmt    = ".0f"
        cbar_title = "Count"

    y_labels = [str(v) for v in z.index.tolist()]
    x_labels = [str(v) for v in z.columns.tolist()]
    z_vals   = z.values

    # Build annotation text matrix
    text_matrix = [
        [f"{z_vals[r, c]:{fmt}}" + ("%" if normalize else "")
         for c in range(len(x_labels))]
        for r in range(len(y_labels))
    ]

    fig = go.Figure(go.Heatmap(
        z=z_vals,
        x=x_labels,
        y=y_labels,
        text=text_matrix,
        texttemplate="%{text}",
        textfont=dict(size=11, color="white", family="Arial"),
        colorscale="Viridis",
        colorbar=dict(
            title=dict(text=cbar_title, font=dict(size=12, color=_FONT_CLR, family="Arial")),
            tickfont=dict(color=_FONT_CLR, family="Arial"),
            thickness=14,
            outlinewidth=0,
        ),
        hovertemplate=(
            f"<b>{col1}</b>: %{{y}}<br>"
            f"<b>{col2}</b>: %{{x}}<br>"
            f"<b>{'Row %' if normalize else 'Count'}</b>: %{{z:{fmt}}}"
            + ("%" if normalize else "") + "<extra></extra>"
        ),
    ))

    plot_title = title if title else f"{col1}  ×  {col2}"
    subtitle   = "Row-normalised (each row sums to 100 %)" if normalize else "Raw counts"

    fig.update_layout(
        title=dict(
            text=f"<b>{plot_title}</b><br><sup>{subtitle}</sup>",
            font=dict(size=18, color=_FONT_CLR, family="Arial"),
            x=0.5, xanchor="center",
        ),
        template="plotly_dark",
        width=1400,
        height=max(420, len(y_labels) * 52 + 160),
        paper_bgcolor=_DARK_BG,
        plot_bgcolor=_PLOT_BG,
        font=dict(color=_FONT_CLR, family="Arial"),
        xaxis=dict(
            title=dict(text=col2, font=dict(size=13)),
            tickfont=dict(size=11),
            side="bottom",
        ),
        yaxis=dict(
            title=dict(text=col1, font=dict(size=13)),
            tickfont=dict(size=11),
            autorange="reversed",   # top-to-bottom reading order
        ),
        margin=dict(l=140, r=80, t=100, b=100),
    )

    return fig


def correlation_heatmap(
    df: pd.DataFrame,
    ignore_cols: list = [],
    cols: Optional[List[str]] = None,
    method: Literal['pearson', 'spearman', 'kendall'] = 'pearson',
    threshold: float = 0.0,
    title: str = "",
) -> go.Figure:
    """
    Annotated correlation heatmap — primary tool for Feature Correlation section.

    Diagonal and cells whose |r| < threshold are masked (shown as empty) so
    the chart stays readable even with many columns.  Colour diverges around 0:
    deep blue = strong positive, deep red = strong negative, grey ≈ zero.

    Parameters
    ----------
    df : pd.DataFrame
    ignore_cols : list
        Columns to exclude.
    cols : list of str, optional
        Restrict to these numerical columns.  If None, uses all numeric cols
        minus ignore_cols.
    method : {'pearson', 'spearman', 'kendall'}, default 'pearson'
    threshold : float, default 0.0
        Cells with |r| below this value are blanked out.
    title : str

    Returns
    -------
    go.Figure
    """
    working = df.drop(columns=[c for c in ignore_cols if c in df.columns])

    if cols is not None:
        working = working[cols]

    num = working.select_dtypes(include=[np.number])
    if num.shape[1] < 2:
        raise ValueError("Need at least two numerical columns for a correlation heatmap.")

    corr = num.corr(method=method)
    labels = corr.columns.tolist()
    n = len(labels)
    z = corr.values.copy()

    # --- Build masked versions for display & annotation ---
    z_display = z.copy().astype(float)
    text_matrix = []

    for r in range(n):
        row_text = []
        for c in range(n):
            if r == c:
                # blank out diagonal
                z_display[r, c] = np.nan
                row_text.append("")
            elif abs(z[r, c]) < threshold:
                z_display[r, c] = np.nan
                row_text.append("")
            else:
                row_text.append(f"{z[r, c]:.2f}")
        text_matrix.append(row_text)

    # Diverging RdBu — reversed so blue=positive, red=negative (conventional)
    colorscale = [
        [0.0,  "#B2182B"],
        [0.1,  "#D6604D"],
        [0.2,  "#F4A582"],
        [0.35, "#FDDBC7"],
        [0.5,  "#F7F7F7"],
        [0.65, "#D1E5F0"],
        [0.8,  "#92C5DE"],
        [0.9,  "#4393C3"],
        [1.0,  "#2166AC"],
    ]

    fig = go.Figure(go.Heatmap(
        z=z_display,
        x=labels,
        y=labels,
        text=text_matrix,
        texttemplate="%{text}",
        textfont=dict(size=10, color="white", family="Arial"),
        colorscale=colorscale,
        zmid=0,
        zmin=-1,
        zmax=1,
        colorbar=dict(
            title=dict(text=method.capitalize(), font=dict(size=12, color=_FONT_CLR, family="Arial")),
            tickfont=dict(color=_FONT_CLR, family="Arial"),
            tickvals=[-1, -0.5, 0, 0.5, 1],
            ticktext=["-1", "-0.5", "0", "0.5", "1"],
            thickness=14,
            outlinewidth=0,
        ),
        hovertemplate="<b>%{y}</b> × <b>%{x}</b><br>r = %{z:.3f}<extra></extra>",
    ))

    # --- Threshold note ---
    thr_note = f"  |r| < {threshold} masked" if threshold > 0 else ""
    method_note = f"{method.capitalize()} correlation{thr_note}"
    plot_title  = title if title else "Feature Correlation Matrix"

    cell_px = max(38, min(70, 900 // n))
    size    = n * cell_px + 200

    fig.update_layout(
        title=dict(
            text=f"<b>{plot_title}</b><br><sup>{method_note}</sup>",
            font=dict(size=18, color=_FONT_CLR, family="Arial"),
            x=0.5, xanchor="center",
        ),
        template="plotly_dark",
        width=max(700, size),
        height=max(600, size),
        paper_bgcolor=_DARK_BG,
        plot_bgcolor=_PLOT_BG,
        font=dict(color=_FONT_CLR, family="Arial"),
        xaxis=dict(
            tickfont=dict(size=11),
            tickangle=-40,
            side="bottom",
        ),
        yaxis=dict(
            tickfont=dict(size=11),
            autorange="reversed",
        ),
        margin=dict(l=150, r=80, t=110, b=150),
    )

    return fig


def scatter_plot(
    df: pd.DataFrame,
    x: str,
    y: str,
    ignore_cols: list = [],
    color_by: Optional[str] = None,
    trendline: bool = True,
    title: str = "",
    width: int = 1400,
) -> go.Figure:
    """
    Scatter plot with an optional OLS trendline.

    When color_by is supplied the points are split by category and each group
    gets its own colour from the library palette.  A trendline is fitted per
    group (not a global pooled line), which makes it easy to spot whether the
    x–y relationship holds equally across all categories or diverges.

    Parameters
    ----------
    df : pd.DataFrame
    x : str
        Numerical column for the x-axis.
    y : str
        Numerical column for the y-axis.
    ignore_cols : list
        Columns to skip (API consistency).
    color_by : str, optional
        Categorical column to colour-split the scatter.
    trendline : bool, default True
        Overlay an OLS trendline.  One line per group when color_by is set.
    title : str

    Returns
    -------
    go.Figure
    """
    working = df.drop(columns=[c for c in ignore_cols if c in df.columns])
    working = working[[col for col in [x, y, color_by] if col]].dropna()

    plot_title = title if title else f"{y}  vs  {x}"

    fig = go.Figure()

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _add_trendline(xd, yd, color, name_prefix=""):
        """Fit OLS and add a smooth line trace. Annotate with r²."""
        if len(xd) < 3:
            return
        slope, intercept, r_val, p_val, _ = stats.linregress(xd, yd)
        x_sorted = np.linspace(xd.min(), xd.max(), 200)
        y_hat    = slope * x_sorted + intercept
        label    = f"{name_prefix} trend (r²={r_val**2:.2f})" if name_prefix else f"OLS (r²={r_val**2:.2f})"
        fig.add_trace(go.Scatter(
            x=x_sorted,
            y=y_hat,
            mode="lines",
            name=label,
            line=dict(color=color, width=2, dash="dash"),
            opacity=0.8,
            showlegend=True,
            hoverinfo="skip",
        ))

    # ── No colour split ───────────────────────────────────────────────────────
    if color_by is None:
        xd = working[x].values
        yd = working[y].values

        fig.add_trace(go.Scatter(
            x=xd, y=yd,
            mode="markers",
            name="",
            marker=dict(
                color=PALETTE[0],
                size=6,
                opacity=0.65,
                line=dict(width=0.4, color="rgba(255,255,255,0.3)"),
            ),
            showlegend=False,
            hovertemplate=f"<b>{x}</b>: %{{x}}<br><b>{y}</b>: %{{y}}<extra></extra>",
        ))

        if trendline:
            _add_trendline(xd, yd, color=PALETTE[2])

    # ── Colour split ──────────────────────────────────────────────────────────
    else:
        categories = sorted(working[color_by].unique())
        for i, cat in enumerate(categories):
            mask = working[color_by] == cat
            sub  = working[mask]
            col  = PALETTE[i % len(PALETTE)]

            fig.add_trace(go.Scatter(
                x=sub[x].values,
                y=sub[y].values,
                mode="markers",
                name=str(cat),
                marker=dict(
                    color=col,
                    size=6,
                    opacity=0.65,
                    line=dict(width=0.4, color="rgba(255,255,255,0.3)"),
                ),
                legendgroup=str(cat),
                hovertemplate=(
                    f"<b>{color_by}</b>: {cat}<br>"
                    f"<b>{x}</b>: %{{x}}<br>"
                    f"<b>{y}</b>: %{{y}}<extra></extra>"
                ),
            ))

            if trendline:
                _add_trendline(sub[x].values, sub[y].values, color=col, name_prefix=str(cat))

    fig.update_layout(
        title=dict(
            text=f"<b>{plot_title}</b>",
            font=dict(size=18, color=_FONT_CLR, family="Arial"),
            x=0.5, xanchor="center",
        ),
        template="plotly_dark",
        width=width,
        height=620,
        paper_bgcolor=_DARK_BG,
        plot_bgcolor=_PLOT_BG,
        font=dict(color=_FONT_CLR, family="Arial"),
        xaxis=dict(
            title=dict(text=x, font=dict(size=13, family="Arial")),
            tickfont=dict(size=11),
            showgrid=True,
            gridwidth=0.5,
            gridcolor=_GRID_CLR,
            zeroline=False,
        ),
        yaxis=dict(
            title=dict(text=y, font=dict(size=13, family="Arial")),
            tickfont=dict(size=11),
            showgrid=True,
            gridwidth=0.5,
            gridcolor=_GRID_CLR,
            zeroline=False,
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0.4)",
            bordercolor="rgba(255,255,255,0.15)",
            borderwidth=1,
            font=dict(size=11, color=_FONT_CLR),
        ),
        margin=dict(l=80, r=60, t=90, b=80),
    )

    return fig


PALETTE = [
    "#636EFA", "#EF553B", "#00CC96", "#AB63FA",
    "#FFA15A", "#19D3F3", "#FF6692",
]

_DARK_BG  = "#0e1117"
_PLOT_BG  = "#1a1a1a"
_GRID_CLR = "rgba(128,128,128,0.2)"
_FONT_CLR = "white"

_RDBU = [
    [0.0,  "#B2182B"],
    [0.1,  "#D6604D"],
    [0.2,  "#F4A582"],
    [0.35, "#FDDBC7"],
    [0.5,  "#F7F7F7"],
    [0.65, "#D1E5F0"],
    [0.8,  "#92C5DE"],
    [0.9,  "#4393C3"],
    [1.0,  "#2166AC"],
]


def _normalize_size(s: pd.Series, lo: float = 5, hi: float = 50) -> np.ndarray:
    """Min-max scale a Series to [lo, hi]."""
    mn, mx = s.min(), s.max()
    if mx == mn:
        return np.full(len(s), (lo + hi) / 2)
    return lo + (s.values - mn) / (mx - mn) * (hi - lo)


def bubble_plot(
    df: pd.DataFrame,
    x: str,
    y: str,
    size: str,
    ignore_cols: list = [],
    color_by: Optional[str] = None,
    title: str = "",
    opacity: float = 0.7,
    width: int = 1400,
) -> go.Figure:
    """
    Three-variable bubble chart: x position × y position × bubble area.

    Bubble area encodes the `size` column (normalised to [5, 50] px so
    extreme values don't eat the chart).  `color_by` accepts either a
    categorical column (discrete palette + legend) or a numerical column
    (RdBu colorbar).

    Parameters
    ----------
    df : pd.DataFrame
    x : str
        Numerical column for the horizontal axis.
    y : str
        Numerical column for the vertical axis.
    size : str
        Numerical column controlling bubble area.
    ignore_cols : list
        Columns to exclude (API consistency).
    color_by : str, optional
        Categorical → discrete palette with legend.
        Numerical  → continuous RdBu colorbar.
        None       → all bubbles in "#00CC96".
    title : str
        Figure title.  Defaults to "y  vs  x  (size = size)".
    opacity : float, default 0.7
        Marker opacity.
    width : int, default 1400

    Returns
    -------
    go.Figure
    """
    # ── Prep ──────────────────────────────────────────────────────────────────
    required = [c for c in [x, y, size, color_by] if c]
    working  = df.drop(columns=[c for c in ignore_cols if c in df.columns])
    working  = working[required].dropna()

    if working.empty:
        raise ValueError("No rows remain after dropping nulls for the selected columns.")

    bubble_sizes = _normalize_size(working[size])
    plot_title   = title if title else f"{y}  vs  {x}  (size = {size})"

    # ── Detect color_by type ──────────────────────────────────────────────────
    is_categorical = (
        color_by is not None
        and (
            working[color_by].dtype == object
            or str(working[color_by].dtype) == "category"
            or working[color_by].nunique() <= 12  # low-cardinality numerics treated as categorical
        )
    )
    is_numerical = color_by is not None and not is_categorical

    fig = go.Figure()

    # ── Size legend annotation ─────────────────────────────────────────────────
    # We'll add representative bubble sizes as a manual annotation block
    # rather than polluting the trace legend.
    raw   = working[size]
    pcts  = [0.25, 0.75, 1.0]            # represent small / medium / large
    refs  = [raw.quantile(p) for p in pcts]
    ref_sizes = [
        float(_normalize_size(pd.Series([v] + [raw.min(), raw.max()]), 5, 50)[0])
        for v in refs
    ]

    # ── Case A: categorical color_by ─────────────────────────────────────────
    if is_categorical:
        categories = sorted(working[color_by].unique(), key=str)
        for i, cat in enumerate(categories):
            mask = working[color_by] == cat
            sub  = working[mask]
            col  = PALETTE[i % len(PALETTE)]
            sub_sizes = bubble_sizes[mask.values]

            hover = (
                f"<b>{color_by}</b>: {cat}<br>"
                f"<b>{x}</b>: %{{x}}<br>"
                f"<b>{y}</b>: %{{y}}<br>"
                f"<b>{size}</b>: %{{customdata:.3g}}<extra></extra>"
            )
            fig.add_trace(go.Scatter(
                x=sub[x].values,
                y=sub[y].values,
                mode="markers",
                name=str(cat),
                customdata=sub[size].values,
                marker=dict(
                    size=sub_sizes,
                    color=col,
                    opacity=opacity,
                    line=dict(width=0.8, color="rgba(255,255,255,0.25)"),
                ),
                legendgroup=str(cat),
                hovertemplate=hover,
            ))

    # ── Case B: numerical color_by ────────────────────────────────────────────
    elif is_numerical:
        hover = (
            f"<b>{x}</b>: %{{x}}<br>"
            f"<b>{y}</b>: %{{y}}<br>"
            f"<b>{size}</b>: %{{customdata[0]:.3g}}<br>"
            f"<b>{color_by}</b>: %{{customdata[1]:.3g}}<extra></extra>"
        )
        fig.add_trace(go.Scatter(
            x=working[x].values,
            y=working[y].values,
            mode="markers",
            name="",
            customdata=np.stack([working[size].values, working[color_by].values], axis=1),
            marker=dict(
                size=bubble_sizes,
                color=working[color_by].values,
                colorscale=_RDBU,
                colorbar=dict(
                    title=dict(
                        text=color_by,
                        font=dict(size=12, color=_FONT_CLR, family="Arial"),
                    ),
                    tickfont=dict(color=_FONT_CLR, family="Arial"),
                    thickness=14,
                    outlinewidth=0,
                ),
                opacity=opacity,
                line=dict(width=0.8, color="rgba(255,255,255,0.25)"),
                showscale=True,
            ),
            showlegend=False,
            hovertemplate=hover,
        ))

    # ── Case C: no color_by ───────────────────────────────────────────────────
    else:
        hover = (
            f"<b>{x}</b>: %{{x}}<br>"
            f"<b>{y}</b>: %{{y}}<br>"
            f"<b>{size}</b>: %{{customdata:.3g}}<extra></extra>"
        )
        fig.add_trace(go.Scatter(
            x=working[x].values,
            y=working[y].values,
            mode="markers",
            name="",
            customdata=working[size].values,
            marker=dict(
                size=bubble_sizes,
                color="#00CC96",
                opacity=opacity,
                line=dict(width=0.8, color="rgba(255,255,255,0.25)"),
            ),
            showlegend=False,
            hovertemplate=hover,
        ))

    # ── Size reference annotation (top-right, inside plot) ───────────────────
    # Three ghost bubbles with labels: Q25 / Q75 / Max of the size column.
    # Rendered as separate traces with no axis influence (visible in legend area).
    size_labels = ["Q25", "Q75", "Max"]
    size_note_lines = [
        f"● {size_labels[i]}  {refs[i]:.3g}"
        for i in range(3)
    ]
    size_block = (
        f"<b>Bubble size → {size}</b><br>"
        + "<br>".join(size_note_lines)
    )

    annotations = [dict(
        text=size_block,
        xref="paper", yref="paper",
        x=0.99, y=0.99,
        xanchor="right", yanchor="top",
        showarrow=False,
        font=dict(size=11, color="#AAAAAA", family="Arial"),
        bgcolor="rgba(0,0,0,0.45)",
        bordercolor="rgba(255,255,255,0.12)",
        borderwidth=1,
        borderpad=6,
        align="left",
    )]

    # ── Layout ────────────────────────────────────────────────────────────────
    fig.update_layout(
        title=dict(
            text=f"<b>{plot_title}</b>",
            font=dict(size=18, color=_FONT_CLR, family="Arial"),
            x=0.5, xanchor="center",
        ),
        template="plotly_dark",
        width=width,
        height=640,
        paper_bgcolor=_DARK_BG,
        plot_bgcolor=_PLOT_BG,
        font=dict(color=_FONT_CLR, family="Arial"),
        xaxis=dict(
            title=dict(text=x, font=dict(size=13, family="Arial")),
            tickfont=dict(size=11),
            showgrid=True,
            gridwidth=0.5,
            gridcolor=_GRID_CLR,
            zeroline=False,
        ),
        yaxis=dict(
            title=dict(text=y, font=dict(size=13, family="Arial")),
            tickfont=dict(size=11),
            showgrid=True,
            gridwidth=0.5,
            gridcolor=_GRID_CLR,
            zeroline=False,
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0.4)",
            bordercolor="rgba(255,255,255,0.12)",
            borderwidth=1,
            font=dict(size=11, color=_FONT_CLR),
            title=dict(
                text=color_by if is_categorical else "",
                font=dict(size=12, color=_FONT_CLR),
            ),
        ),
        annotations=annotations,
        margin=dict(l=80, r=80, t=90, b=80),
    )

    return fig