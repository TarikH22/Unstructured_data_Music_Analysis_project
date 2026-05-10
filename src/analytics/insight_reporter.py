import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def run_all_questions(df):
    results = {}
    print("--- Analytics Insights ---")
    print(f"Total artists analyzed: {len(df)}")
    
    # Q1: Total listeners by source
    q1 = df.groupby('source_collection')['listeners'].sum().to_dict()
    results['Total Listeners by Source'] = q1
    print("\nQ1: Total Listeners by Source")
    print(q1)

    # Q2: Top 3 artists by Playcount
    q2 = df.nlargest(3, 'playcount')[['name', 'playcount']]
    results['Top 3 Artists by Playcount'] = q2.to_dict('records')
    print("\nQ2: Top 3 Artists by Playcount")
    print(q2)

    # Q3: Average listeners by source
    q3 = df.groupby('source_collection')['listeners'].mean().round(2).to_dict()
    results['Avg Listeners by Source'] = q3
    print("\nQ3: Avg Listeners by Source")
    print(q3)

    # Q4: Correlation between playcount and listeners
    q4 = df['listeners'].corr(df['playcount'])
    results['Correlation'] = q4
    print("\nQ4: Correlation between Listeners and Playcount")
    print(f"{q4:.4f}")

    return results

def plot_genre_roi(df, output_path='data/processed/analytics/genre_roi.png'):
    plt.figure(figsize=(10,6))
    if 'listeners' in df.columns:
        sns.barplot(data=df, x='name', y='listeners')
        plt.xticks(rotation=90)
        plt.title('Listeners per Artist')
        plt.tight_layout()
        plt.savefig(output_path)
    plt.close()
