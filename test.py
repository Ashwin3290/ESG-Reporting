import pandas as pd

df=pd.read_csv("data/kpi_data.csv")
print(df.head())
print(df.info())

from collections import Counter

kpi_words = df['KPI Name'].str.split().explode().str.lower()
common_words = Counter(kpi_words).most_common(50)  # Display top 50 most common words
common_words
