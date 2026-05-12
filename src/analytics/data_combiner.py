import pandas as pd

def combine_data(df1, df2, on_key='name', how='inner'):
    return pd.merge(df1, df2, on=on_key, how=how)

def concat_data(df1, df2):
    return pd.concat([df1, df2], ignore_index=True)
