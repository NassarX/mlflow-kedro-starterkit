"""
This is a boilerplate pipeline
generated using Kedro 0.18.8
"""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import  clean_data, feature_engineer, split_data, model_train


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=clean_data,
                inputs="bank_raw_data",
                outputs=["bank_cleaned_data","raw_describe","cleaned_describe"],
                name="clean",
            ),

            node(
                func= feature_engineer,
                inputs="bank_cleaned_data",
                outputs= "bank_data_engineered",
                name="engineering",
            ),

            node(
                func= split_data,
                inputs=["bank_data_engineered","parameters"],
                outputs= ["X_train_data","X_test_data","y_train_data","y_test_data"],
                name="split",
            ),


            node(
                func= model_train,
                inputs=["X_train_data","X_test_data","y_train_data","y_test_data","parameters"],
                outputs= ["test_model","output_plot"],
                name="train",
            ),
        ]
    )
