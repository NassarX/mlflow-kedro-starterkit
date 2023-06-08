"""
This is a boilerplate pipeline
generated using Kedro 0.18.8
"""

import logging
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd
from .utils import *


from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import OneHotEncoder , LabelEncoder
import shap 
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, classification_report
from sklearn.ensemble import RandomForestClassifier
import sklearn
import mlflow

def clean_data(
    data: pd.DataFrame,
) -> Tuple[pd.DataFrame, Dict, Dict]:
    """Does dome data cleaning.
    Args:
        data: Data containing features and target.
    Returns:
        data: Cleaned data
    """
    #remove some outliers
    df_transformed = data.copy()

    describe_to_dict = df_transformed.describe().to_dict()

    for cols in ["age"]:
        Q1 = df_transformed[cols].quantile(0.25)
        Q3 = df_transformed[cols].quantile(0.75)
        IQR = Q3 - Q1     

    filter = (df_transformed[cols] >= Q1 - 1.5 * IQR) & (df_transformed[cols] <= Q3 + 1.5 *IQR)
    df_transformed = df_transformed.loc[filter]
    
    #we can do some basic cleaning by impuation of all null values
    df_transformed.fillna(-9999,inplace=True)

    describe_to_dict_verified = df_transformed.describe().to_dict()

    return df_transformed, describe_to_dict, describe_to_dict_verified 


def feature_engineer( data: pd.DataFrame) -> pd.DataFrame:
    
    le = LabelEncoder()

    df = campaign_(data)
    df = age_(df)
    df = balance_(df)
    df["y"] = df["y"].map({"no":0, "yes":1})
    
    #new profiling feature
    # In this step we should start to think on feature store
    df["mean_balance_bin_age"] = df.groupby("bin_age")["balance"].transform("mean")
    df["std_balance_bin_age"] = df.groupby("bin_age")["balance"].transform("std")
    df["z_score_bin_age"] = (df["mean_balance_bin_age"] - df["balance"])/(df["std_balance_bin_age"])
    #df['day_of_week'] = le.fit_transform(df['day_of_week'])
    df['month'] = le.fit_transform(df['month'])
    
    

    #fit_transform() will return encoded values 
    #df['day_of_week'] = le.fit_transform(df['day_of_week'])
    df['month'] = le.fit_transform(df['month'])
    
    
    numerical_features = df.select_dtypes(exclude=['object','string','category']).columns.tolist()
    categorical_features = df.select_dtypes(include=['object','string','category']).columns.tolist()
    #Exercise create an assert for numerical and categorical features
    
    OH_encoder = OneHotEncoder(handle_unknown='ignore', sparse=False)
    OH_cols= pd.DataFrame(OH_encoder.fit_transform(df[categorical_features]))

    # Adding column names to the encoded data set.
    OH_cols.columns = OH_encoder.get_feature_names_out(categorical_features)

    # One-hot encoding removed index; put it back
    OH_cols.index = df.index

    # Remove categorical columns (will replace with one-hot encoding)
    num_df = df.drop(categorical_features, axis=1)

    # Add one-hot encoded columns to numerical features
    df_final = pd.concat([num_df, OH_cols], axis=1)


    log = logging.getLogger(__name__)
    log.info(f"The final dataframe has {len(df_final.columns)} columns.")

    return df_final




def split_data(
    data: pd.DataFrame, parameters: Dict[str, Any]
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Splits data into features and target training and test sets.

    Args:
        data: Data containing features and target.
        parameters: Parameters defined in parameters.yml.
    Returns:
        Split data.
    """

    assert [col for col in data.columns if data[col].isnull().any()] == []
    y = data[parameters["target_column"]]
    X = data.drop(columns=parameters["target_column"], axis=1)
    X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, test_size=parameters["test_fraction"], random_state=parameters["random_state"])
    #X_train = data_train.drop(columns=parameters["target_column"])
    #X_test = data_test.drop(columns=parameters["target_column"])
    #y_train = data_train[parameters["target_column"]]
    #y_test = data_test[parameters["target_column"]]
    return X_train, X_test, y_train, y_test



def model_train(X_train: pd.DataFrame, X_test: pd.DataFrame, y_train: pd.DataFrame, y_test: pd.DataFrame, parameters: Dict[str, Any]):
    
    mlflow.set_tag("mlflow.runName", parameters["run_name"])
    #mlflow.autolog(log_model_signatures=True, log_input_examples=True)

    model = RandomForestClassifier(n_estimators=parameters["n_estimators"], max_depth=parameters["max_depth"], max_features=parameters["max_features"])
    model.fit(X_train, y_train)
    # Create object that can calculate shap values
    explainer = shap.TreeExplainer(model)

    # calculate shap values. This is what we will plot.
    #shap_values = explainer.shap_values(X_test)
    
    #shap.summary_plot(shap_values[1], X_test,show=False)

    preds = model.predict(X_test)
    pred_labels = np.rint(preds)
    accuracy = sklearn.metrics.accuracy_score(y_test, pred_labels)

    log = logging.getLogger(__name__)
    log.info("Model accuracy on test set: %0.2f%%", accuracy * 100)

    return model,plt