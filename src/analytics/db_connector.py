import pymysql
import pandas as pd

def get_connection(host='localhost', user='root', password='password', db='music_db'):
    return pymysql.connect(host=host, user=user, password=password, database=db)

def populate_financials(df, connection):
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS artist_stats (
            name VARCHAR(255) PRIMARY KEY,
            listeners FLOAT,
            playcount FLOAT
        )
    """)
    for _, row in df.iterrows():
        cursor.execute("INSERT IGNORE INTO artist_stats (name, listeners, playcount) VALUES (%s, %s, %s)",
                       (row['name'], row.get('listeners', 0), row.get('playcount', 0)))
    connection.commit()

def query_financials(connection):
    return pd.read_sql("SELECT * FROM artist_stats", connection)
