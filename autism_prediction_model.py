# -*- coding: utf-8 -*-
"""Autism_prediction_model.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1bLxbXcDxaNQIL4fvrm8l77qYL2AVXQN-

**Importing the Libraries**
"""


from IPython import get_ipython
from IPython.display import display
# %% [markdown]
# **Importing the Libraries**
# %%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sklearn as sk
from sklearn.preprocessing import LabelEncoder
from imblearn.over_sampling import SMOTE
from sklearn.model_selection import train_test_split, cross_val_score, RandomizedSearchCV
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier #Imported after xgboost installation
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import pickle


"""**Data Loading & Understanding**"""

df = pd.read_csv("/content/train.csv")

pd.set_option("display.max_columns", None)

df["age"] = df["age"].astype(int)

df.head(2)

df.head(2)

for col in df.columns:
  numerical_features = ["ID","age","result"]
  if col not in numerical_features:
    print(col,df[col].unique())
    print("-"*50)

df = df.drop(columns = ["ID", "age_desc"])

df.head(2)

# Define the mapping name for country names
mappping = {
    "Viet Nam" : "Vietnam",
    "AmericanSamoa":"United States",
    "Hong Kong" : "China"
}
#replace the value in country column
df["contry_of_res"] = df["contry_of_res"].replace(mappping)

df["contry_of_res"].unique()

#target class destribution
df["Class/ASD"].value_counts()

"""**Insights**
1. missing values ion ethinicity and relation
2. age_desc column has one unique value so it is removed as it is not important for prediction
3. fixed country names
4. identified class imbalance in the target coulmn

**3. Exploratory Data Analysis**
"""

df.describe()

"""**Univariate Analysis**

Numerical columns:
- age
- result
"""

#set the desired theme
sns.set_theme(style="whitegrid")

# Histogram for age
sns.histplot(df["age"], kde=True)
plt.title("Age Distribution")


#mean, median
age_mean = df["age"].mean()
age_median = df["age"].median()
print(f"Mean: {age_mean}, Median: {age_median}")


plt.axvline(age_mean, color="red", linestyle="--", label="Mean")
plt.axvline(age_median, color="green", linestyle="-", label="Median")

plt.legend()
plt.show()

# Histogram for age
sns.histplot(df["result"], kde=True)
plt.title("Distribution of result")


#mean, median
result_mean = df["result"].mean()
result_median = df["result"].median()
print(f"Mean: {result_mean}, Median: {result_median}")

#drawing vertical line
plt.axvline(result_mean, color="red", linestyle="--", label="Mean")
plt.axvline(result_median, color="green", linestyle="-", label="Median")

plt.legend()
plt.show()

"""**Box plots for identifying outliers in numerical columns**"""

#box plot
sns.boxplot(x=df["age"])
plt.title("Box plot for age")
plt.xlabel("Age")
plt.show()

#box plot
sns.boxplot(x=df["result"])
plt.title("Box plot for result")
plt.xlabel("result")
plt.show()

# count the outliers using IQR method for age column
Q1 = df["age"].quantile(0.25)
Q3 = df["age"].quantile(0.75)
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR
age_outliers = df[(df["age"] < lower_bound) | (df["age"] > upper_bound)]

len(age_outliers)

# count the outliers using IQR method for result column
Q1 = df["result"].quantile(0.25)
Q3 = df["result"].quantile(0.75)
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR
result_outliers = df[(df["result"] < lower_bound) | (df["result"] > upper_bound)]

len(result_outliers)

"""**Univariate analysis of Categorical columns**"""

df.columns

categorical_columns = ['A1_Score', 'A2_Score', 'A3_Score', 'A4_Score', 'A5_Score', 'A6_Score',
       'A7_Score', 'A8_Score', 'A9_Score', 'A10_Score', 'gender',
       'ethnicity', 'jaundice', 'austim', 'contry_of_res', 'used_app_before','relation']

for col in categorical_columns:
  sns.countplot(x=df[col])
  plt.title(f"count plot for {col}")
  plt.xlabel(col)
  plt.ylabel("Count")
  plt.show()

#countplot for target column (Class/ASD)
sns.countplot(x=df["Class/ASD"])
plt.title("count plot for Class/ASD")
plt.xlabel("Class/ASD")
plt.ylabel("Count")
plt.show()

df["Class/ASD"].value_counts()

"""handling missing values in ethnicity and relation column"""

df["ethnicity"] = df["ethnicity"].replace({"?" : "Others", "others" : "Others"})

df["relation"].unique()

df["relation"] = df["relation"].replace({"?" : "Others", "Relative":"Others", "Parent":"Others", "Health care professional":"Others"})

df["relation"].unique()

#identify columns with "object" data types

object_columns = df.select_dtypes(include=["object"]).columns

print(object_columns)

#intialize a dictionary to store the encoders
encoders = {}

#apply label encoding and store the encoders
for col in object_columns:
  encoder = LabelEncoder()
  df[col] = encoder.fit_transform(df[col])
  encoders[col] = encoder


# save the encoders as a pickle file
with open("encoders.pkl", "wb") as f:
  pickle.dump(encoders, f)

encoders

"""**Bivariate Analysis**"""

#correlation matrix
plt.figure(figsize=(15,15))
sns.heatmap(df.corr(), annot=True, cmap="coolwarm", fmt=".2f")
plt.title("Correlation matrix")
plt.show()

"""**Insights from EDA:**
- There are few outliers in numerical column(age, results)
- There is a class imbalance in the target column
- There is a class imbalance in the categorical features
- We don't have any highly correleted column
- performed label encoding and saved the encoders

**4. Data preprocessing**
"""

#function to replace outliers with the median
def replace_outliers_with_median(df, column):
  Q1 = df[column].quantile(0.25)
  Q3 = df[column].quantile(0.75)
  IQR = Q3 - Q1

  lower_bound = Q1 - 1.5 * IQR
  upper_bound = Q3 + 1.5 * IQR

  median = df[column].median()


  #replace the outlier with the median
  df[column] = df[column].apply(lambda x: median if x < lower_bound or x > upper_bound else x)

  return df

#replace the outliers in the "age" column
df = replace_outliers_with_median(df, "age")

#replace the outliers in the "result" column
df = replace_outliers_with_median(df, "result")

df.shape

"""**Train Test Split**"""

X = df.drop(columns = ["Class/ASD"])
y= df["Class/ASD"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print(X_train.shape, X_test.shape, y_train.shape, y_test.shape)

"""SMOTE(Synthetic Minority Oversampling technique)"""

smote = SMOTE(random_state=42)
X_train_smote, y_train_smote = smote.fit_resample(X_train, y_train)

print(X_train_smote.shape, y_train_smote.shape)

print(y_train_smote.value_counts())

"""5. **Model Training**"""

# dictionary of classifiers
models = {
    "Decision Tree": DecisionTreeClassifier(),
    "Random Forest": RandomForestClassifier(),
    "XGBoost": XGBClassifier()
}
models["XGBoost"]._estimator_type = "classifier"

# dictionary to store cross validation results
cv_scores ={}

# perform 5-fold cross validation for each model

for model_name, model in models.items():
  print(f"Training {model_name} with default parameters...")
  scores = cross_val_score(model, X_train_smote, y_train_smote, cv=5, scoring = "accuracy")
  cv_scores[model_name] = scores
  print(f"{model_name} Cross-Validation Accuracy: {np.mean(scores):.2f}")
  print("-"*50)

cv_scores

"""**6. Model Selection & Hyperparameter Tuning**"""

# Intializing models

decision_tree = DecisionTreeClassifier(random_state =42)
random_forest = RandomForestClassifier(random_state =42)
xgboost_classifier = XGBClassifier(random_state =42)

# Hyperparameter grids for RandomizedSearchCV

param_grid_dt = {
    "criterion": ["gini", "entropy"],
    "max_depth": [None, 10, 20, 30, 50, 70],
    "min_samples_split": [2, 5, 10],
    "min_samples_leaf": [1, 2, 4]
}

params_grid_rf = {
    "n_estimators": [50, 100, 200, 500],
    "max_depth": [None, 10, 20, 30],
    "min_samples_split": [2, 5, 10],
    "min_samples_leaf": [1, 2, 4],
    "bootstrap": [True, False]
}

params_grid_xgb = {
    "n_estimators": [50, 100, 200, 500],
    "max_depth": [3, 5, 7, 10],
    "learning_rate": [0.01, 0.1, 0.2, 0.3],
    "subsample": [0.5, 0.7, 1.0],
    "colsample_bytree": [0.5, 0.7, 1.0]
}

# hyperparameter tuning for 3 tree based models

# the below steps can be automated by using a for loop or by using a pipeline

# perform RandomizedSearchCV for each model
random_search_dt = RandomizedSearchCV(estimator=decision_tree, param_distributions=param_grid_dt, n_iter=10, cv=5, scoring="accuracy", random_state=42)
random_search_rf = RandomizedSearchCV(estimator=random_forest, param_distributions=params_grid_rf, n_iter=10, cv=5, scoring="accuracy", random_state=42)
random_search_xgb = RandomizedSearchCV(estimator=xgboost_classifier, param_distributions=params_grid_xgb, n_iter=10, cv=5, scoring="accuracy", random_state=42)

# fit the models
random_search_dt.fit(X_train_smote, y_train_smote)
random_search_rf.fit(X_train_smote, y_train_smote)
random_search_xgb.fit(X_train_smote, y_train_smote)

# Get the model with best score
best_model = None
best_score = 0

if random_search_dt.best_score_ > best_score:
  best_score = random_search_dt.best_score_
  best_model = random_search_dt.best_estimator_

if random_search_rf.best_score_ > best_score:
  best_score = random_search_rf.best_score_
  best_model = random_search_rf.best_estimator_

if random_search_xgb.best_score_ > best_score:
  best_score = random_search_xgb.best_score_
  best_model = random_search_xgb.best_estimator_

print(f"Best Model: {best_model}")
print(f"Best Cross-Validation Accuracy: {best_score:.2f}")

# save the best model
with open("best_model.pkl", "wb") as f:
  pickle.dump(best_model, f)

"""**7. Evaluation**"""

# evaluate on test data
y_test_pred = best_model.predict(X_test)
print("Accuracy score:\n", accuracy_score(y_test, y_test_pred))
print("Confusion Matrix:\n", confusion_matrix(y_test, y_test_pred))
print("Classification Report:", classification_report(y_test, y_test_pred))
