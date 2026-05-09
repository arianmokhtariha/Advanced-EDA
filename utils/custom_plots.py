import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Optional, List


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
    
    # Dynamic spacing based on number of columns
    if n_cols <= 2:
        h_spacing = 0.12
        v_spacing = 0.15
    elif n_cols == 3:
        h_spacing = 0.08
        v_spacing = 0.13
    elif n_cols == 4:
        h_spacing = 0.05
        v_spacing = 0.12
    else:  # 5+ columns
        h_spacing = 0.03
        v_spacing = 0.10
    
    # Calculate height - scales with rows
    height = figsize[1] if figsize[1] is not None else n_rows * 400
    
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







