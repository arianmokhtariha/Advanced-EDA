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



def outlier_plot(
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




# ── SQL queries for schema_diagram() (pg_catalog — PostgreSQL only, zero ambiguity) ────────────────


_FK_QUERY = """
SELECT
    child_cl.relname  AS child_table,
    child_at.attname  AS fk_column,
    parent_cl.relname AS parent_table,
    parent_at.attname AS pk_column
FROM pg_catalog.pg_constraint  con
JOIN pg_catalog.pg_class       child_cl  ON child_cl.oid  = con.conrelid
JOIN pg_catalog.pg_namespace   child_ns  ON child_ns.oid  = child_cl.relnamespace
JOIN pg_catalog.pg_class       parent_cl ON parent_cl.oid = con.confrelid
CROSS JOIN LATERAL unnest(con.conkey, con.confkey) AS cols(child_col, parent_col)
JOIN pg_catalog.pg_attribute   child_at
    ON child_at.attrelid = con.conrelid  AND child_at.attnum = cols.child_col
JOIN pg_catalog.pg_attribute   parent_at
    ON parent_at.attrelid = con.confrelid AND parent_at.attnum = cols.parent_col
WHERE con.contype   = 'f'
  AND child_ns.nspname = '{schema}';
"""

_TABLES_QUERY = """
SELECT c.relname AS table_name
FROM pg_catalog.pg_class     c
JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = '{schema}'
  AND c.relkind = 'r';
"""

#   Why pg_catalog instead of information_schema:
#   information_schema identifies constraints by name, but PostgreSQL only
#   requires constraint names to be unique WITHIN a table — not across the
#   schema.  When two tables define the same constraint name (e.g. both
#   `appearances` and `game_events` call their FK `fk_player_id`),
#   information_schema views cannot distinguish them and any join on
#   constraint_name cross-products the rows, producing phantom duplicates.
#
#   pg_catalog uses OIDs (object identifiers) which are globally unique
#   integers assigned by PostgreSQL itself — no name collision is possible.
#   unnest(conkey, confkey) unpacks the FK and PK column-number arrays in
#   parallel, so composite keys pair correctly without ordinal tricks.
#   Result: exactly one row per FK column, always, regardless of naming.

_COLUMNS_QUERY = """
SELECT
    c.relname                                        AS table_name,
    a.attname                                        AS column_name,
    pg_catalog.format_type(a.atttypid, a.atttypmod)  AS data_type
FROM pg_catalog.pg_attribute  a
JOIN pg_catalog.pg_class      c ON c.oid = a.attrelid
JOIN pg_catalog.pg_namespace  n ON n.oid = c.relnamespace
WHERE n.nspname  = '{schema}'
  AND c.relkind  = 'r'
  AND a.attnum   > 0
  AND NOT a.attisdropped
ORDER BY c.relname, a.attnum;
"""

#   Same reasoning as _FK_QUERY: pg_catalog OIDs guarantee uniqueness per
#   column (attnum is the 1-based ordinal position within its table), so
#   the ORDER BY c.relname, a.attnum always returns columns in the original
#   CREATE TABLE order — independent of any name the user may have given.



# ── Internal helpers for schema_diagram() ──────────────────────────────────────────────────────────

def _get_pos(G: nx.DiGraph, layout: str, seed: int, spring_k: float) -> dict:
    if layout == "spring":
        return nx.spring_layout(G, seed=seed, k=spring_k)
    elif layout == "kamada_kawai":
        return nx.kamada_kawai_layout(G)
    elif layout == "shell":
        shells = sorted(G.nodes(), key=lambda n: G.in_degree(n))
        mid = math.ceil(len(shells) / 2)
        return nx.shell_layout(G, nlist=[shells[:mid], shells[mid:]])
    elif layout == "circular":
        return nx.circular_layout(G)
    else:
        raise ValueError(
            f"Unknown layout '{layout}'. "
            "Choose: spring, kamada_kawai, shell, circular"
        )


def _separate_nodes(pos: dict, min_dist: float = 0.28, iterations: int = 100) -> dict:
    """Push nodes apart when the layout places two of them too close together."""
    pos = {k: list(v) for k, v in pos.items()}
    nodes = list(pos.keys())
    for _ in range(iterations):
        changed = False
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                u, v = nodes[i], nodes[j]
                dx = pos[u][0] - pos[v][0]
                dy = pos[u][1] - pos[v][1]
                dist = math.sqrt(dx ** 2 + dy ** 2)
                if dist < min_dist:
                    push = (min_dist - dist) / 2 + 1e-6
                    ux, uy = (dx / dist, dy / dist) if dist > 1e-9 else (1.0, 0.0)
                    pos[u][0] += ux * push
                    pos[u][1] += uy * push
                    pos[v][0] -= ux * push
                    pos[v][1] -= uy * push
                    changed = True
        if not changed:
            break
    return {k: tuple(v) for k, v in pos.items()}


def _perimeter_point(x0, y0, x1, y1, r):
    """
    Return the point on the perimeter of node at (x1,y1) facing (x0,y0).
    Stops edges and arrowheads at the node boundary, not inside it.
    """
    dx, dy = x1 - x0, y1 - y0
    dist = math.sqrt(dx ** 2 + dy ** 2)
    if dist < 1e-9:
        return x1, y1
    ratio = max(0.0, (dist - r) / dist)
    return x0 + dx * ratio, y0 + dy * ratio


def _estimate_node_radius(pos: dict, node_size: int,
                           fig_width: int, fig_height: int) -> float:
    """Convert node_size (px diameter) to data-coordinate units."""
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    x_span = (max(xs) - min(xs)) or 1.0
    y_span = (max(ys) - min(ys)) or 1.0
    eff_w  = (fig_width  - 40) * 0.70
    eff_h  = (fig_height - 80) * 0.70
    r_x = (node_size / 2) / (eff_w / x_span)
    r_y = (node_size / 2) / (eff_h / y_span)
    return (r_x + r_y) / 2


# ── Main function ─────────────────────────────────────────────────────────────

def schema_diagram(
    run_query_fn: Callable[[str], pd.DataFrame],
    *,
    # — Data
    schema: str = "public",
    # — Graph layout
    layout: Literal["spring", "kamada_kawai", "shell", "circular"] = "kamada_kawai",
    seed: int = 42,
    spring_k: float = 2.5,
    # — Nodes
    node_size: int = 28,
    node_colorscale: str = "Blues",
    node_border_color: str = "#6366F1",
    node_font_size: int = 13,
    # — Edges
    edge_color: str = "#6366F1",
    edge_width: float = 1.8,
    arrow_size: float = 1.2,
    # — Edge labels
    edge_labels: Literal["hover", "always", "none"] = "hover",
    edge_label_font_size: int = 10,
    edge_label_color: str = "#94A3B8",
    # — Figure
    title: str = "Database Schema – Table Relationships",
    height: int = 650,
    width: Optional[int] = 1400,
    template: str = "plotly_dark",
    paper_bgcolor: str = "#0e1117",
) -> go.Figure:
    """
    Auto-generate an interactive FK relationship diagram from a live PostgreSQL DB.

    Parameters
    ----------
    run_query_fn : callable
        Your existing run_query() from db_utils.  Accepts a SQL string,
        returns a pandas DataFrame.
    schema : str
        Postgres schema to inspect (default: 'public').
    layout : str
        Node layout algorithm:
        'kamada_kawai' (default) | 'spring' | 'shell' | 'circular'
    seed : int
        Random seed for the spring layout.
    spring_k : float
        Spring layout repulsion — increase to spread nodes further apart.
    node_size : int
        Marker diameter for table nodes (pixels).
    node_colorscale : str
        Plotly colorscale for node fill colour.
    node_border_color : str
        Hex colour for the node border ring.
    node_font_size : int
        Font size of the table-name labels.
    edge_color : str
        Hex colour for edges and arrowheads.
    edge_width : float
        Stroke width of edge lines.
    arrow_size : float
        Scale factor for arrowheads.
    edge_labels : str
        'hover'  — FK column names appear on mouse-over (default, cleaner)
        'always' — FK column names rendered directly on the diagram
        'none'   — no FK labels at all
    edge_label_font_size : int
        Font size for edge labels (both hover tooltip and always-on).
        Default 10. Increase for larger text, e.g. 12 or 14.
    edge_label_color : str
        Colour for always-on edge label text.
    title : str
        Figure title.
    height : int
        Figure height in pixels.
    width : int or None
        Figure width in pixels.  None = full container width.
    template : str
        Plotly template ('plotly_dark', 'plotly', 'ggplot2', …).
    paper_bgcolor : str
        Figure background colour.

    Returns
    -------
    plotly.graph_objects.Figure
    """

    # ── 1. Fetch live schema ──────────────────────────────────────────────────
    df_fk     = run_query_fn(_FK_QUERY.format(schema=schema))
    df_tables = run_query_fn(_TABLES_QUERY.format(schema=schema))
    df_cols   = run_query_fn(_COLUMNS_QUERY.format(schema=schema))

    if df_fk is None or df_tables is None or df_cols is None:
        raise RuntimeError("Could not fetch schema — check your DB connection.")

    # Build table → [column (type), …] map for node hover tooltips
    table_cols: dict[str, list[str]] = {}
    for _, row in df_cols.iterrows():
        table_cols.setdefault(row["table_name"], []).append(
            f"{row['column_name']}  ({row['data_type']})"
        )

    # ── 2. Build graph ────────────────────────────────────────────────────────
    G = nx.DiGraph()
    G.add_nodes_from(df_tables["table_name"])

    # Collapse parallel FK edges: one graph edge per (child, parent) pair,
    # storing all FK→PK column pairs in a list so nothing is lost.
    edge_fks: dict[tuple, list[str]] = {}
    for _, row in df_fk.iterrows():
        key   = (row["child_table"], row["parent_table"])
        label = f"{row['fk_column']} → {row['pk_column']}"
        edge_fks.setdefault(key, []).append(label)

    for (child, parent), labels in edge_fks.items():
        G.add_edge(child, parent, fk_labels=labels)

    # ── 3. Layout + separate overlapping nodes ────────────────────────────────
    pos    = _get_pos(G, layout, seed, spring_k)
    pos    = _separate_nodes(pos)
    _fig_w = width or 900
    node_r = _estimate_node_radius(pos, node_size, _fig_w, height)

    # ── 4. Edge lines (perimeter-to-perimeter) ────────────────────────────────
    edge_x, edge_y = [], []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        sx, sy = _perimeter_point(x1, y1, x0, y0, node_r)
        tx, ty = _perimeter_point(x0, y0, x1, y1, node_r)
        edge_x += [sx, tx, None]
        edge_y += [sy, ty, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        mode="lines",
        line=dict(width=edge_width, color=edge_color),
        hoverinfo="none",
    )

    # ── 5. Arrowhead stubs ────────────────────────────────────────────────────
    # Short annotation covering only the last 20 % of each edge so the
    # arrowhead sits cleanly at the node perimeter, not inside the node.
    annotations = []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        sx, sy = _perimeter_point(x1, y1, x0, y0, node_r)
        tx, ty = _perimeter_point(x0, y0, x1, y1, node_r)
        stub_ax = sx + (tx - sx) * 0.80
        stub_ay = sy + (ty - sy) * 0.80
        annotations.append(dict(
            x=tx, y=ty,
            ax=stub_ax, ay=stub_ay,
            xref="x", yref="y",
            axref="x", ayref="y",
            showarrow=True,
            arrowhead=2,
            arrowsize=arrow_size,
            arrowwidth=edge_width,
            arrowcolor=edge_color,
            text="",
            opacity=0.9,
        ))

    # ── 6. Edge labels ────────────────────────────────────────────────────────
    # Placed at 35 % from source + perpendicular nudge to separate labels on
    # edges that converge on the same hub node.
    lbl_x, lbl_y, hover_texts, always_texts = [], [], [], []
    for u, v, data in G.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]

        lx = x0 + (x1 - x0) * 0.35
        ly = y0 + (y1 - y0) * 0.35

        elen = math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)
        if elen > 1e-9:
            perp_x = -(y1 - y0) / elen
            perp_y =  (x1 - x0) / elen
            lx += perp_x * node_r * 0.9
            ly += perp_y * node_r * 0.9

        lbl_x.append(lx)
        lbl_y.append(ly)

        fk_str = "<br>".join(data["fk_labels"])
        hover_texts.append(
            f"<b>{u}</b> → <b>{v}</b><br>"
            f"<span style='color:{edge_label_color}'>{fk_str}</span>"
        )
        always_texts.append("<br>".join(data["fk_labels"]))

    if edge_labels == "hover":
        label_trace = go.Scatter(
            x=lbl_x, y=lbl_y,
            mode="markers",
            marker=dict(size=10, color="rgba(0,0,0,0)"),
            hovertemplate=[f"{h}<extra></extra>" for h in hover_texts],
            hoverlabel=dict(bgcolor="#1e1e2e", font_size=edge_label_font_size),
        )
    elif edge_labels == "always":
        label_trace = go.Scatter(
            x=lbl_x, y=lbl_y,
            mode="text",
            text=always_texts,
            textfont=dict(size=edge_label_font_size, color=edge_label_color),
            hovertemplate=[f"{h}<extra></extra>" for h in hover_texts],
            hoverlabel=dict(bgcolor="#1e1e2e", font_size=edge_label_font_size),
        )
    else:
        label_trace = go.Scatter(
            x=lbl_x, y=lbl_y,
            mode="markers",
            marker=dict(size=1, color="rgba(0,0,0,0)"),
            hoverinfo="none",
        )

    # ── 7. Node trace ─────────────────────────────────────────────────────────
    node_names  = list(G.nodes())
    node_x      = [pos[n][0] for n in node_names]
    node_y      = [pos[n][1] for n in node_names]
    in_degrees  = [G.in_degree(n)  for n in node_names]
    out_degrees = [G.out_degree(n) for n in node_names]

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        text=node_names,
        textposition="top center",
        textfont=dict(size=node_font_size, color="white"),
        hovertemplate=[
            (
                f"<b>{n}</b><br>"
                f"Referenced by {i} table(s)<br>"
                f"References {o} table(s)<br>"
                f"──────────────────<br>"
                + "<br>".join(table_cols.get(n, ["(no columns found)"]))
                + "<extra></extra>"
            )
            for n, i, o in zip(node_names, in_degrees, out_degrees)
        ],
        hoverlabel=dict(bgcolor="#1e1e2e", font_size=12),
        marker=dict(
            size=node_size,
            color=in_degrees,
            colorscale=node_colorscale,
            showscale=True,
            colorbar=dict(
                title=dict(text="Referenced by (n tables)", font=dict(color="white")),
                thickness=12,
                tickfont=dict(color="white"),
                bgcolor="rgba(0,0,0,0)",
                outlinewidth=0,
            ),
            line=dict(width=2, color=node_border_color),
        ),
    )

    # ── 8. Assemble figure ────────────────────────────────────────────────────
    fig = go.Figure(
        data=[edge_trace, label_trace, node_trace],
        layout=go.Layout(
            title=dict(text=title, font=dict(size=18, color="white"), x=0.5),
            template=template,
            paper_bgcolor=paper_bgcolor,
            plot_bgcolor=paper_bgcolor,
            showlegend=False,
            hovermode="closest",
            annotations=annotations,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=height,
            width=width,
            margin=dict(l=20, r=20, t=60, b=20),
        ),
    )

    return fig