from __future__ import annotations
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Optional, List, Literal, Callable
import math
import networkx as nx


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

