import pandas as pd

# Load the two CSV files into DataFrames
filtered_updated_df = pd.read_csv("gdelt_5_years_filtered_updated.csv")
keyword_sentiment_df = pd.read_csv("gdelt_5_years_with_keyword_sentiment.csv")

# Merge the two DataFrames on the 'Headline' column
merged_df = keyword_sentiment_df.merge(
    filtered_updated_df[['Headline', 'Date', 'Updated_Date']],
    on='Headline',
    how='left'
)

# Save the updated DataFrame to a new CSV file
merged_df.to_csv("gdelt_5_years_with_keyword_sentiment_updated.csv", index=False)

print("Updated file saved as 'gdelt_5_years_with_keyword_sentiment_updated.csv'")