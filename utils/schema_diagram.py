from __future__ import annotations
import plotly.graph_objects as go
import pandas as pd
from typing import Optional, Literal, Callable
import math
import networkx as nx



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


def _edge_label_angle(
    x0: float, y0: float,
    x1: float, y1: float,
    fig_w: int, fig_h: int,
    x_range: float, y_range: float,
) -> float:
    """
    Compute the Plotly ``textangle`` (clockwise degrees from horizontal) that
    makes a label visually parallel to the edge from ``(x0, y0)`` to
    ``(x1, y1)``.

    Two coordinate-system subtleties are accounted for:

    * **Aspect-ratio correction** — networkx positions sit in roughly
      [-1, 1] × [-1, 1] data space, but the rendered canvas is
      ``fig_w × fig_h`` pixels.  Scaling each axis by its pixels-per-unit
      ratio converts the data-space delta to an approximate screen-space
      delta, so the computed angle matches what the user actually sees.

    * **Y-axis flip** — Plotly displays data with y increasing *upward*,
      but Plotly's ``textangle`` lives in screen space where y increases
      *downward*.  Negating ``dy`` before calling ``atan2`` corrects for
      this flip, ensuring positive angles are clockwise as Plotly expects.

    The result is normalised to ``[-90, 90]`` so text is never upside-down.
    """
    scale_x = (fig_w - 40) / max(x_range, 1e-9)
    scale_y = (fig_h - 80) / max(y_range, 1e-9)
    dx_screen =  (x1 - x0) * scale_x
    dy_screen = -(y1 - y0) * scale_y   # negate: data y-up → screen y-down
    angle = math.degrees(math.atan2(dy_screen, dx_screen))
    # Clamp to [-90, 90]: keep text readable, never upside-down
    if angle > 90:
        angle -= 180
    elif angle < -90:
        angle += 180
    return angle


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
    rotate_edge_labels: bool = False,
    rotated_label_spacing: float = 1.6,
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
    rotate_edge_labels : bool
        Only has effect when ``edge_labels='always'``.
        When ``True``, each FK label is rotated to match the visual angle
        of its connection line, making it immediately clear which label
        belongs to which edge.  Multiple FK labels on the same edge are
        stacked perpendicular to the edge — mirroring the horizontal-mode
        stacking behaviour — so labels never collide with each other.
        See also ``rotated_label_spacing``.
        When ``False`` (default), all labels remain horizontal.
    rotated_label_spacing : float
        Only has effect when ``rotate_edge_labels=True``.
        Controls the gap between stacked FK labels on the same edge.
        The gap equals ``edge_label_font_size × rotated_label_spacing``
        converted to data-coordinate units, so the visual spacing scales
        consistently regardless of figure size or font size.
        Default 1.6.  Increase (e.g. 2.5) for looser stacking,
        decrease (e.g. 1.0) for tighter stacking.
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
    _fig_w   = width or 900
    node_r   = _estimate_node_radius(pos, node_size, _fig_w, height)
    # Pre-compute data ranges used by _edge_label_angle() for aspect-ratio
    # correction — extracted here once so the label loop stays concise.
    _all_xs  = [p[0] for p in pos.values()]
    _all_ys  = [p[1] for p in pos.values()]
    _x_range = (max(_all_xs) - min(_all_xs)) or 1.0
    _y_range = (max(_all_ys) - min(_all_ys)) or 1.0

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
    lbl_x, lbl_y, lbl_angles, hover_texts, always_texts = [], [], [], [], []
    edge_perp_dirs: list[tuple[float, float]] = []  # unit perp vector per edge
    edge_fk_lists:  list[list[str]]          = []  # raw FK label list per edge
    for u, v, data in G.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]

        lx = x0 + (x1 - x0) * 0.35
        ly = y0 + (y1 - y0) * 0.35

        perp_x, perp_y = 0.0, 0.0                  # safe default for zero-length edges
        elen = math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)
        if elen > 1e-9:
            perp_x = -(y1 - y0) / elen
            perp_y =  (x1 - x0) / elen
            lx += perp_x * node_r * 0.9
            ly += perp_y * node_r * 0.9

        lbl_x.append(lx)
        lbl_y.append(ly)
        edge_perp_dirs.append((perp_x, perp_y))
        edge_fk_lists.append(data["fk_labels"])
        lbl_angles.append(
            _edge_label_angle(
                x0, y0, x1, y1,
                _fig_w, height, _x_range, _y_range,
            )
        )

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
        if rotate_edge_labels:
            # go.Scatter mode="text" has no per-point textangle support.
            # We use an invisible Scatter to carry hover tooltips, then add
            # one layout annotation per label — each annotation gets its own
            # textangle so it visually aligns with its edge line.
            label_trace = go.Scatter(
                x=lbl_x, y=lbl_y,
                mode="markers",
                marker=dict(size=10, color="rgba(0,0,0,0)"),
                hovertemplate=[f"{h}<extra></extra>" for h in hover_texts],
                hoverlabel=dict(bgcolor="#1e1e2e", font_size=edge_label_font_size),
            )
            # Convert one font-size line-height to data-coordinate units, then
            # scale by the user-tunable multiplier.  This keeps the gap visually
            # consistent regardless of figure size or font size.
            line_spacing = (
                (edge_label_font_size * rotated_label_spacing)
                / (height - 80)
                * _y_range
            )

            for base_lx, base_ly, fk_labels, angle, (perp_x, perp_y) in zip(
                lbl_x, lbl_y, edge_fk_lists, lbl_angles, edge_perp_dirs
            ):
                n_labels = len(fk_labels)
                for i, label_text in enumerate(fk_labels):
                    # Centre the stack around the base position.  Each label is
                    # offset along the perpendicular-to-edge direction so that,
                    # after textangle rotation, the labels read as a tidy vertical
                    # stack — matching the horizontal-mode stacking behaviour.
                    offset = (i - (n_labels - 1) / 2) * line_spacing
                    annotations.append(dict(
                        x=base_lx + perp_x * offset,
                        y=base_ly + perp_y * offset,
                        xref="x", yref="y",
                        text=label_text,
                        showarrow=False,
                        textangle=angle,
                        font=dict(size=edge_label_font_size, color=edge_label_color),
                        align="center",
                    ))
        else:
            # Default: horizontal text via a single Scatter trace (original)
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