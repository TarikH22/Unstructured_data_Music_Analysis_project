import pandas as pd

def convert_wide_to_long(df, id_vars, value_vars):
    return df.melt(id_vars=id_vars, value_vars=value_vars)

def build_pivot_table(df, index, columns, values, aggfunc='mean'):
    return df.pivot_table(index=index, columns=columns, values=values, aggfunc=aggfunc, margins=True)

def build_crosstab(index, columns):
    return pd.crosstab(index, columns)
