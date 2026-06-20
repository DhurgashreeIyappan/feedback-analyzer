import pandas as pd

df = pd.read_csv("outputs/cleaned_feedback.csv")

print("Rows:", len(df))
print("Duplicate feedbacks:", df["feedback_text"].duplicated().sum())