import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Optional, List, Literal


def distribution_plot(
    df: pd.DataFrame,
    title: str = 'Distribution Overview',
    ignore_cols: Optional[List[str]] = None,
    top_n_categories: int = 10,
    n_cols: int = 2,
    show_mean_line: bool = True,
    show_median_line: bool = True,
    categorical_threshold: int = 10,
    figsize: tuple = (1400, None)  # Width fixed, height auto-calculated
) -> go.Figure:
    """
    Create comprehensive EDA visualization for all columns in a DataFrame.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe to analyze
    title : str, default='Distribution Overview'
        Main title for the plot
    ignore_cols : List[str], optional
        Column names to exclude from visualization
    top_n_categories : int, default=10
        Maximum number of categories to show individually (rest grouped as "Other")
    n_cols : int, default=2
        Number of columns in the subplot grid
    show_mean_line : bool, default=True
        Show mean line on numerical plots
    show_median_line : bool, default=True
        Show median line on numerical plots
    categorical_threshold : int, default=10
        Treat numerical columns with fewer unique values as categorical
    figsize : tuple, default=(1400, None)
        Figure size (width, height). Height auto-calculated if None
    
    Returns:
    --------
    plotly.graph_objects.Figure
    """
    
    # Color schemes
    numerical_colors = [
        '#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A',
        '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52'
    ]
    categorical_colors = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
        '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5'
    ]
    other_color = '#4a4a4a'  # Neutral gray for "Other" category
    
    # Prepare columns
    if ignore_cols is None:
        ignore_cols = []
    
    cols_to_plot = [col for col in df.columns if col not in ignore_cols]
    
    # Remove columns with all nulls
    cols_to_plot = [col for col in cols_to_plot if df[col].notna().sum() > 0]
    
    if len(cols_to_plot) == 0:
        raise ValueError("No valid columns to plot after filtering")
    
    # Classify columns
    column_types = {}
    for col in cols_to_plot:
        col_data = df[col].dropna()
        
        # Check if datetime
        if pd.api.types.is_datetime64_any_dtype(col_data):
            column_types[col] = 'categorical'
        # Check if explicitly categorical or object
        elif pd.api.types.is_categorical_dtype(col_data) or pd.api.types.is_object_dtype(col_data):
            column_types[col] = 'categorical'
        # Check if numeric
        elif pd.api.types.is_numeric_dtype(col_data):
            n_unique = col_data.nunique()
            # Treat as categorical if low cardinality
            if n_unique < categorical_threshold:
                column_types[col] = 'categorical'
            else:
                column_types[col] = 'numerical'
        else:
            column_types[col] = 'categorical'
    
    # Calculate grid dimensions
    n_plots = len(cols_to_plot)
    n_rows = int(np.ceil(n_plots / n_cols))
    
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
    height = figsize[1] if figsize[1] is not None else n_rows * per_row_h
    
    # Create subplots
    fig = make_subplots(
        rows=n_rows,
        cols=n_cols,
        subplot_titles=[col for col in cols_to_plot],
        vertical_spacing=v_spacing,
        horizontal_spacing=h_spacing
    )
    
    # Track max values for each subplot to adjust y-axis
    subplot_max_values = {}
    
    # Store stats for annotations
    stats_annotations = []
    
    # Plot each column
    for idx, col in enumerate(cols_to_plot):
        row = idx // n_cols + 1
        col_pos = idx % n_cols + 1
        color_idx = idx % len(numerical_colors)
        
        col_data = df[col].dropna()
        
        if column_types[col] == 'numerical':
            # Numerical: Histogram
            fig.add_trace(
                go.Histogram(
                    x=col_data,
                    name=col,
                    marker_color=numerical_colors[color_idx],
                    showlegend=False,
                    autobinx=True
                ),
                row=row,
                col=col_pos
            )
            
            mean_val = col_data.mean()
            median_val = col_data.median()
            
            # Determine the correct axis references
            if idx == 0:
                xref = 'x'
                yref = 'y'
                xref_domain = 'x domain'
                yref_domain = 'y domain'
            else:
                xref = f'x{idx + 1}'
                yref = f'y{idx + 1}'
                xref_domain = f'x{idx + 1} domain'
                yref_domain = f'y{idx + 1} domain'
            
            # Add mean line
            if show_mean_line:
                fig.add_shape(
                    type='line',
                    x0=mean_val,
                    x1=mean_val,
                    y0=0,
                    y1=1,
                    yref=yref_domain,
                    xref=xref,
                    line=dict(color='#FFD700', width=2.5, dash='dash')
                )
            
            # Add median line
            if show_median_line:
                fig.add_shape(
                    type='line',
                    x0=median_val,
                    x1=median_val,
                    y0=0,
                    y1=1,
                    yref=yref_domain,
                    xref=xref,
                    line=dict(color='#FF6B6B', width=2.5, dash='dot')
                )
            
            # Create annotation text for this subplot
            annotation_lines = []
            if show_mean_line:
                annotation_lines.append(f'<span style="color:#FFD700;">━━</span> Mean: {mean_val:.2f}')
            if show_median_line:
                annotation_lines.append(f'<span style="color:#FF6B6B;">⋯⋯</span> Median: {median_val:.2f}')
            
            if annotation_lines:
                stats_annotations.append({
                    'text': '<br>'.join(annotation_lines),
                    'xref': xref_domain,
                    'yref': yref_domain,
                    'x': 0.98,  # Top right of subplot
                    'y': 0.98,
                    'xanchor': 'right',
                    'yanchor': 'top',
                    'showarrow': False,
                    'font': dict(size=10, color='#fafafa'),
                    'bgcolor': 'rgba(0,0,0,0.6)',
                    'bordercolor': '#2d2d2d',
                    'borderwidth': 1,
                    'borderpad': 4
                })
        
        else:
            # Categorical: Bar chart with percentages
            value_counts = col_data.value_counts()
            total = len(col_data)
            percentages = (value_counts / total * 100).round(2)
            
            # Handle top N categories
            if len(value_counts) > top_n_categories:
                top_categories = value_counts.head(top_n_categories)
                other_count = value_counts.iloc[top_n_categories:].sum()
                other_pct = (other_count / total * 100).round(2)
                
                categories = list(top_categories.index) + ['Other']
                values = list(top_categories.values) + [other_count]
                pcts = list(percentages.head(top_n_categories)) + [other_pct]
                colors = [categorical_colors[i % len(categorical_colors)] 
                         for i in range(top_n_categories)] + [other_color]
            else:
                categories = list(value_counts.index)
                values = list(value_counts.values)
                pcts = list(percentages)
                colors = [categorical_colors[i % len(categorical_colors)] 
                         for i in range(len(categories))]
            
            # Sort by frequency (descending)
            sorted_data = sorted(zip(categories, values, pcts, colors), 
                               key=lambda x: x[1], reverse=True)
            categories, values, pcts, colors = zip(*sorted_data)
            
            # Store max value for y-axis adjustment
            subplot_max_values[(row, col_pos)] = max(values)
            
            # Create hover text with percentages
            hover_text = [f"{cat}<br>Count: {val}<br>Percentage: {pct}%" 
                         for cat, val, pct in zip(categories, values, pcts)]
            
            fig.add_trace(
                go.Bar(
                    x=list(categories),
                    y=list(values),
                    name=col,
                    marker_color=list(colors),
                    showlegend=False,
                    text=[f"{pct}%" for pct in pcts],
                    textposition='outside',
                    textfont=dict(size=10),
                    hovertext=hover_text,
                    hoverinfo='text',
                    cliponaxis=False
                ),
                row=row,
                col=col_pos
            )
    
    # Update layout for dark mode
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
        uniformtext_minsize=8,
        uniformtext_mode='hide',
    )

    fig.update_layout(
    annotations=list(fig.layout.annotations) + stats_annotations
)
    
    # Update axes
    fig.update_xaxes(
        showgrid=True, 
        gridwidth=0.5, 
        gridcolor='#2d2d2d',
        tickangle=-45,
        tickfont=dict(size=10)
    )
    
    fig.update_yaxes(
        showgrid=True, 
        gridwidth=0.5, 
        gridcolor='#2d2d2d'
    )
    
    # Adjust y-axis range for categorical plots to prevent text cutoff
    for (row, col_pos), max_val in subplot_max_values.items():
        fig.update_yaxes(
            range=[0, max_val * 1.15],
            row=row,
            col=col_pos
        )
    
    return fig



def outlier_plot(
    df: pd.DataFrame,
    ignore_list: Optional[List[str]] = None,
    whis: float = 1.5,
    orientation: Literal['horizontal', 'vertical'] = 'horizontal',
    title: Optional[str] = "Box Plot Overview"
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
        'vertical'   – subplots arranged **side-by-side** (one row);
                       boxes are drawn vertically (value on y-axis).
        'horizontal' – subplots **stacked** (one column per row);
                       boxes are drawn horizontally (value on x-axis).
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
    if orientation == 'vertical':
        # Side-by-side subplots, one row — boxes are vertical (y = value)
        rows, cols_n = 1, n
        h_spacing = max(0.01, min(0.04, 0.5 / n))
        v_spacing = 0.12
        plot_height = 480
    else:
        # Stacked subplots, one column per row — boxes are horizontal (x = value)
        rows, cols_n = n, 1
        h_spacing = 0.04
        v_spacing = max(0.03, min(0.12, 0.6 / n))
        plot_height = n * 280

    fig = make_subplots(
        rows=rows, cols=cols_n,
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

        r = 1           if orientation == 'vertical' else idx + 1
        c = idx + 1     if orientation == 'vertical' else 1

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

        if orientation == 'vertical':
            # One row, n columns → centre each annotation under its subplot
            axis_key = 'xaxis' if idx == 0 else f'xaxis{idx + 1}'
            domain = fig.layout[axis_key].domain
            x_center = (domain[0] + domain[1]) / 2
            annotations.append(dict(
                text=f"Outliers: {n_out} ({pct:.1f}%)",
                xref='paper', yref='paper',
                x=x_center, y=-0.04,
                xanchor='center', yanchor='top',
                showarrow=False,
                font=dict(size=11, color='#FFD700'),
                bgcolor='rgba(0,0,0,0.5)',
                bordercolor='#FFD700', borderwidth=1, borderpad=4,
            ))
        else:
            # n rows, one column → place each annotation to the right of its row
            axis_key = 'yaxis' if idx == 0 else f'yaxis{idx + 1}'
            domain = fig.layout[axis_key].domain
            y_center = (domain[0] + domain[1]) / 2
            annotations.append(dict(
                text=f"Outliers: {n_out} ({pct:.1f}%)",
                xref='paper', yref='paper',
                x=1.01, y=y_center,
                xanchor='left', yanchor='middle',
                showarrow=False,
                font=dict(size=11, color='#FFD700'),
                bgcolor='rgba(0,0,0,0.5)',
                bordercolor='#FFD700', borderwidth=1, borderpad=4,
            ))

    # ── Layout ────────────────────────────────────────────────────────────────
    margin = (
        dict(l=50, r=50,  t=80, b=100)   # extra bottom for below-subplot labels
        if orientation == 'vertical' else
        dict(l=50, r=180, t=80, b=50)    # extra right for side annotations
    )

    fig.update_layout(
        title=dict(
            text=title or "Outlier Analysis",
            font=dict(size=18, color='white'),
            x=0.5, xanchor='center',
        ),
        template='plotly_dark',
        autosize=True,          # always fill the available container width
        height=plot_height,
        showlegend=False,
        paper_bgcolor='#0e1117',
        plot_bgcolor='#1a1a1a',
        font=dict(color='white'),
        annotations=annotations,
        margin=margin,
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








