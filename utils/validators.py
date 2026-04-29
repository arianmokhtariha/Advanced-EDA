"""
Data validation functions to detect quality issues in football dataset.
Each function returns a report of detected anomalies.
"""

import pandas as pd
from typing import Dict, List
import re


# ============================================================================
# DUPLICATE DETECTION
# ============================================================================

def find_exact_duplicates(df: pd.DataFrame, subset: List[str] = None) -> pd.DataFrame:
    """
    Find exact duplicate rows.
    
    Args:
        df: DataFrame to check
        subset: Columns to consider for duplication (None = all columns)
    
    Returns DataFrame of duplicate rows with duplicate_group column.
    """
    duplicated_mask = df.duplicated(subset=subset, keep=False)
    duplicates = df[duplicated_mask].copy()
    
    if len(duplicates) > 0:
        # Assign group IDs to duplicates
        if subset:
            duplicates['duplicate_group'] = duplicates.groupby(subset).ngroup()
        else:
            duplicates['duplicate_group'] = duplicates.groupby(list(df.columns)).ngroup()
    
    return duplicates


def find_near_duplicate_games(games_df: pd.DataFrame) -> pd.DataFrame:
    """
    Find games with same game_id but conflicting data (scores, dates, etc.).
    """
    # Group by game_id and check for variations
    issues = []
    
    for game_id, group in games_df.groupby('game_id'):
        if len(group) > 1:
            # Check if data conflicts
            for col in ['home_club_goals', 'away_club_goals', 'date', 'attendance']:
                if group[col].nunique() > 1:
                    issues.append({
                        'game_id': game_id,
                        'count': len(group),
                        'issue': f'Conflicting {col} values',
                        'values': group[col].unique().tolist()
                    })
                    break
    
    return pd.DataFrame(issues)



# ============================================================================
# MISSING VALUE DETECTION
# ============================================================================

def check_missing_critical_fields(df: pd.DataFrame, critical_fields: List[str], table_name: str) -> pd.DataFrame:
    """
    Find rows with missing values in critical fields.
    
    Returns DataFrame with missing value indicators.
    """
    issues = []
    
    for idx, row in df.iterrows():
        missing_fields = []
        for field in critical_fields:
            value = row[field]
            # Check for various forms of missing
            if pd.isna(value) or value == '' or value == ' ' or str(value).strip() == '':
                missing_fields.append(field)
        
        if missing_fields:
            issue_row = row.to_dict()
            issue_row['missing_fields'] = ', '.join(missing_fields)
            issue_row['index'] = idx
            issues.append(issue_row)
    
    return pd.DataFrame(issues)


def check_placeholder_values(df: pd.DataFrame, text_columns: List[str]) -> pd.DataFrame:
    """
    Detect placeholder values like 'Unknown', 'N/A', 'TBD', etc.
    """
    placeholders = ['unknown', 'n/a', 'na', 'tbd', 'null', 'none', 'missing', '?', '--']
    issues = []
    
    for idx, row in df.iterrows():
        found_placeholders = {}
        for col in text_columns:
            value = str(row[col]).strip().lower()
            if value in placeholders:
                found_placeholders[col] = row[col]
        
        if found_placeholders:
            issue_row = row.to_dict()
            issue_row['placeholder_fields'] = str(found_placeholders)
            issue_row['index'] = idx
            issues.append(issue_row)
    
    return pd.DataFrame(issues)


# ============================================================================
# FORMAT INCONSISTENCIES
# ============================================================================

def check_date_format_consistency(df: pd.DataFrame, date_column: str) -> Dict:
    """
    Detect multiple date formats in a column.
    
    Returns dict with format patterns and example values.
    """
    formats = {
        'ISO (YYYY-MM-DD)': r'^\d{4}-\d{2}-\d{2}$',
        'US (MM/DD/YYYY)': r'^\d{2}/\d{2}/\d{4}$',
        'EU (DD.MM.YYYY)': r'^\d{2}\.\d{2}\.\d{4}$',
        'Mixed separators': r'^\d{2,4}[-/.]\d{2}[-/.]\d{2,4}$',
        'Invalid': r'^(?!\d{4}-\d{2}-\d{2}$)(?!\d{2}/\d{2}/\d{4}$)(?!\d{2}\.\d{2}\.\d{4}$).*'
    }
    
    results = {}
    
    for format_name, pattern in formats.items():
        matches = df[df[date_column].astype(str).str.match(pattern, na=False)]
        if len(matches) > 0:
            results[format_name] = {
                'count': len(matches),
                'examples': matches[date_column].head(5).tolist()
            }
    
    # Unparseable dates
    unparseable = []
    for idx, value in df[date_column].items():
        if pd.notna(value) and value != '':
            try:
                pd.to_datetime(value, errors='raise')
            except:
                unparseable.append({'index': idx, 'value': value})
    
    if unparseable:
        results['unparseable'] = unparseable[:10]  # First 10 examples
    
    return results


def check_numeric_format_violations(df: pd.DataFrame, numeric_columns: List[str]) -> pd.DataFrame:
    """
    Find non-numeric values in columns that should be numeric.
    """
    issues = []
    
    for col in numeric_columns:
        for idx, value in df[col].items():
            if pd.notna(value) and value != '':
                try:
                    float(value)
                except (ValueError, TypeError):
                    issues.append({
                        'index': idx,
                        'column': col,
                        'value': value,
                        'issue': 'Non-numeric value in numeric field'
                    })
    
    return pd.DataFrame(issues)


# ============================================================================
# ENCODING AND CHARACTER ISSUES
# ============================================================================

def check_encoding_issues(df: pd.DataFrame, text_columns: List[str]) -> pd.DataFrame:
    """
    Detect broken UTF-8 sequences and encoding problems.
    """
    issues = []
    
    # Patterns indicating encoding issues
    broken_patterns = [
        r'�',  # Replacement character
        r'Ã©|Ã¨|Ã´|Ã¡',  # Double-encoded UTF-8
        r'\\x[0-9a-fA-F]{2}',  # Hex escape sequences
        r'[\x80-\xFF]',  # Raw bytes in string
    ]
    
    for col in text_columns:
        for idx, value in df[col].items():
            if pd.notna(value):
                value_str = str(value)
                for pattern in broken_patterns:
                    if re.search(pattern, value_str):
                        issues.append({
                            'index': idx,
                            'column': col,
                            'value': value_str,
                            'issue': f'Encoding issue detected (pattern: {pattern})'
                        })
                        break
    
    return pd.DataFrame(issues)


def check_mixed_character_sets(df: pd.DataFrame, text_columns: List[str]) -> pd.DataFrame:
    """
    Detect unexpected character sets (e.g., Cyrillic in Latin text fields).
    """
    issues = []
    
    for col in text_columns:
        for idx, value in df[col].items():
            if pd.notna(value):
                value_str = str(value)
                
                # Check for Cyrillic
                if re.search(r'[А-Яа-я]', value_str):
                    issues.append({
                        'index': idx,
                        'column': col,
                        'value': value_str,
                        'issue': 'Contains Cyrillic characters'
                    })
                
                # Check for mixed scripts
                has_latin = bool(re.search(r'[A-Za-z]', value_str))
                has_cyrillic = bool(re.search(r'[А-Яа-я]', value_str))
                has_arabic = bool(re.search(r'[\u0600-\u06FF]', value_str))
                
                script_count = sum([has_latin, has_cyrillic, has_arabic])
                if script_count > 1:
                    issues.append({
                        'index': idx,
                        'column': col,
                        'value': value_str,
                        'issue': 'Mixed character sets'
                    })
    
    return pd.DataFrame(issues)


# ============================================================================
# WHITESPACE ISSUES
# ============================================================================

def check_whitespace_issues(df: pd.DataFrame, text_columns: List[str]) -> pd.DataFrame:
    """
    Detect leading/trailing whitespace and excessive internal whitespace.
    """
    issues = []
    
    for col in text_columns:
        for idx, value in df[col].items():
            if pd.notna(value) and isinstance(value, str):
                problems = []
                
                if value != value.strip():
                    problems.append('leading/trailing whitespace')
                
                if '  ' in value:  # Multiple consecutive spaces
                    problems.append('excessive internal whitespace')
                
                if '\t' in value or '\n' in value:
                    problems.append('contains tabs/newlines')
                
                if problems:
                    issues.append({
                        'index': idx,
                        'column': col,
                        'value': repr(value),  # repr shows whitespace
                        'issue': ', '.join(problems)
                    })
    
    return pd.DataFrame(issues)


# ============================================================================
# DATA TYPE VIOLATIONS
# ============================================================================

def check_negative_values(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """
    Find negative values in columns that should be non-negative.
    """
    issues = []
    
    for col in columns:
        for idx, value in df[col].items():
            try:
                if pd.notna(value) and float(value) < 0:
                    issues.append({
                        'index': idx,
                        'column': col,
                        'value': value,
                        'issue': 'Negative value in non-negative field'
                    })
            except (ValueError, TypeError):
                pass  # Will be caught by numeric format check
    
    return pd.DataFrame(issues)



# ============================================================================
# OUTLIER DETECTION
# ============================================================================

def detect_outliers_iqr(df: pd.DataFrame, column: str, multiplier: float = 3.0) -> pd.DataFrame:
    """
    Detect outliers using IQR method.
    
    Args:
        multiplier: IQR multiplier (1.5 = standard, 3.0 = extreme outliers)
    """
    if column not in df.columns:
        return pd.DataFrame()
    
    # Convert to numeric, coerce errors
    numeric_series = pd.to_numeric(df[column], errors='coerce')
    
    Q1 = numeric_series.quantile(0.25)
    Q3 = numeric_series.quantile(0.75)
    IQR = Q3 - Q1
    
    lower_bound = Q1 - multiplier * IQR
    upper_bound = Q3 + multiplier * IQR
    
    outliers = df[(numeric_series < lower_bound) | (numeric_series > upper_bound)].copy()
    
    if len(outliers) > 0:
        outliers['outlier_value'] = numeric_series[outliers.index]
        outliers['lower_bound'] = lower_bound
        outliers['upper_bound'] = upper_bound
    
    return outliers

