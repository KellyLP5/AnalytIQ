'''
Created on Nov 13, 2026

@author: kmoth
'''
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
# python -m streamlit run C:\Users\kmoth\eclipse-practice\AnalytIQ\main.py   windows + R then run 
import re
from difflib import SequenceMatcher


def normalize_column_name(name):
    """Standardize column names for comparison."""
    name = str(name).lower().strip()
    name = re.sub(r"[^a-z0-9 ]", " ", name)
    words = name.split()

    # Ignore generic naming words
    words = [word for word in words if word != "name"]

    return " ".join(words)


def compare_column_values(left_series, right_series):
    """Estimate how many values overlap between two columns."""

    left_values = set(
        left_series.dropna().astype(str).str.strip().str.lower()
    )

    right_values = set(
        right_series.dropna().astype(str).str.strip().str.lower()
    )

    if not left_values or not right_values:
        return 0

    overlap = len(left_values.intersection(right_values))

    return overlap / min(len(left_values), len(right_values))


def suggest_column_matches(left_df, right_df):
    """Find potentially matching columns in two datasets."""

    suggestions = []

    for left_col in left_df.columns:
        for right_col in right_df.columns:

            left_name = normalize_column_name(left_col)
            right_name = normalize_column_name(right_col)

            name_score = SequenceMatcher(
                None,
                left_name,
                right_name
            ).ratio()

            value_score = compare_column_values(
                left_df[left_col],
                right_df[right_col]
            )

            score = max(name_score, value_score)

            if name_score >= 0.65 or value_score >= 0.50:

                suggestions.append({
                    "left": left_col,
                    "right": right_col,
                    "score": score
                })

    suggestions.sort(
        key=lambda x: x["score"],
        reverse=True
    )
#AnalytIQ - Intelligent Data Analyst

st.set_page_config(
    page_title="AnalytIQ",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
if "combined_df" not in st.session_state:
    st.session_state["combined_df"] = None

if "combined_name" not in st.session_state:
    st.session_state["combined_name"] = None

# Application Title
st.title("AnalytIQ")
st.subheader("Intelligent Research & Statistical Analysis")

st.write(
    "Upload a dataset and let AnalytIQ help you "
    "explore, combine, analyze, and visualize your data."
)

# -----------------------------------------
# 1. Dataset Upload
# -----------------------------------------

st.header("1. Dataset Upload")

uploaded_files = st.file_uploader(
    "Upload one or more Excel or CSV datasets",
    type=["csv", "xlsx"],
    accept_multiple_files=True
)

datasets = {}

if uploaded_files:
    for i, uploaded_file in enumerate(uploaded_files):
        try:
            if uploaded_file.name.lower().endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            dataset_name = f"{uploaded_file.name} ({i + 1})"
            datasets[dataset_name] = df

        except Exception as e:
            st.error(
                f"Could not read {uploaded_file.name}: {e}"
            )

# -----------------------------------------
# 2. Individual Dataset Analysis
# -----------------------------------------

if datasets:

    st.success(
        f"{len(datasets)} dataset(s) successfully uploaded!"
    )

    st.header("2. Individual Dataset Analysis")

    selected_dataset = st.selectbox(
        "Choose a dataset to analyze",
        list(datasets.keys())
    )

    df = datasets[selected_dataset]

    st.subheader(f"Preview: {selected_dataset}")
    st.dataframe(df.head(10), use_container_width=True)

    # Dataset Overview
    st.subheader("Dataset Overview")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Observations", df.shape[0])

    with col2:
        st.metric("Variables", df.shape[1])

    with col3:
        st.metric(
            "Missing Values",
            int(df.isna().sum().sum())
        )

    # Descriptive Statistics
    st.header("3. Descriptive Statistics")

    st.dataframe(
        df.describe(include="all").T,
        use_container_width=True
    )

    # Missing Values
    st.header("4. Data Quality")

    missing = df.isna().sum().reset_index()
    missing.columns = ["Variable", "Missing Values"]

    st.dataframe(missing, use_container_width=True)

    # -----------------------------------------
    # 3. Combine Datasets
    # -----------------------------------------

    st.header("5. Combine Datasets")

    dataset_names = list(datasets.keys())

    if len(dataset_names) >= 2:

        combine_method = st.radio(
            "Choose how to combine your datasets",
            ["Merge Datasets", "Append Datasets"],
            horizontal=True
        )

        if combine_method == "Merge Datasets":

            st.write(
                "Merge joins two datasets using matching variables "
                "such as state, year, or ID."
            )

            col1, col2 = st.columns(2)

            with col1:
                left_name = st.selectbox(
                    "First dataset",
                    dataset_names,
                    key="left_dataset"
                )

            with col2:
                right_options = [
                    name for name in dataset_names
                    if name != left_name
                ]

                right_name = st.selectbox(
                    "Second dataset",
                    right_options,
                    key="right_dataset"
                )

            left_df = datasets[left_name]
            right_df = datasets[right_name]
            left_df.columns = left_df.columns.str.strip().str.lower()
            right_df.columns = right_df.columns.str.strip().str.lower()
            
            st.write("First dataset columns:", left_df.columns.tolist())
            st.write("Second dataset columns:", right_df.columns.tolist())

            common_columns = [
                col for col in left_df.columns
                if col in right_df.columns
            ]

            if common_columns:

                st.write("Select the matching variables.")

                col1, col2 = st.columns(2)

                with col1:
                    left_key = st.selectbox(
                        "Matching variable in first dataset",
                        left_df.columns.tolist(),
                        index=left_df.columns.tolist().index(
                            common_columns[0]
                        )
                    )

                with col2:
                    right_key = st.selectbox(
                        "Matching variable in second dataset",
                        right_df.columns.tolist(),
                        index=right_df.columns.tolist().index(
                            common_columns[0]
                        )
                    )

                merge_type = st.selectbox(
                    "Choose merge type",
                    ["inner", "left", "right", "outer"]
                )

                if st.button("Merge Datasets"):

                    try:
                        combined = pd.merge(
                            left_df,
                            right_df,
                            left_on=left_key,
                            right_on=right_key,
                            how=merge_type
                        )

                        st.session_state["combined_df"] = combined
                        st.session_state["combined_name"] = (
                            "Merged Dataset"
                        )

                        st.success(
                            "Datasets merged successfully!"
                        )

                    except Exception as e:
                        st.error(
                            f"Unable to merge datasets: {e}"
                        )

            else:
                st.warning(
                    "No matching column names were found. "
                    "Check your datasets before merging."
                )

        else:

            st.write(
                "Append stacks datasets vertically. "
                "Columns with different names are retained."
            )

            if st.button("Append Datasets"):

                try:
                    combined = pd.concat(
                        list(datasets.values()),
                        ignore_index=True,
                        sort=False
                    )

                    st.session_state["combined_df"] = combined
                    st.session_state["combined_name"] = (
                        "Appended Dataset"
                    )

                    st.success(
                        "Datasets appended successfully!"
                    )

                except Exception as e:
                    st.error(
                        f"Unable to append datasets: {e}"
                    )

    else:
        st.info(
            "Upload at least two datasets to combine them."
        )

else:
    st.info("Upload a dataset to begin your analysis.")

# -----------------------------------------
# 4. Display Combined Dataset
# -----------------------------------------

if st.session_state["combined_df"] is not None:

    combined_df = st.session_state["combined_df"]

    st.header("6. Combined Dataset")

    col1, col2, col3 = st.columns(3)

    col1.metric("Rows", combined_df.shape[0])
    col2.metric("Columns", combined_df.shape[1])

    col3.metric(
        "Missing Values",
        int(combined_df.isnull().sum().sum())
    )

    st.dataframe(
        combined_df.head(10),
        use_container_width=True
    )

    st.subheader("Download Combined Dataset")

    csv = combined_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="analytIQ_combined_dataset.csv",
        mime="text/csv"
    )

# -----------------------------------------
# 5. Data Visualization
# -----------------------------------------

st.header("7. Data Visualization")

visualization_options = {}

for name, dataset in datasets.items():
    visualization_options[name] = dataset

if st.session_state["combined_df"] is not None:

    visualization_options["Combined Dataset"] = (
        st.session_state["combined_df"]
    )

if visualization_options:

    visualization_dataset = st.selectbox(
        "Choose a dataset to visualize",
        list(visualization_options.keys()),
        key="visualization_dataset"
    )

    viz_df = visualization_options[visualization_dataset]

    numeric_columns = viz_df.select_dtypes(
        include=np.number
    ).columns.tolist()

    if numeric_columns:

        chart_type = st.selectbox(
            "Choose a visualization",
            ["Histogram", "Scatterplot", "Boxplot"]
        )

        if chart_type == "Histogram":

            selected_variable = st.selectbox(
                "Choose a variable",
                numeric_columns,
                key="histogram_variable"
            )

            fig = px.histogram(
                viz_df,
                x=selected_variable,
                title=f"Distribution of {selected_variable}",
                marginal="box"
            )

        elif chart_type == "Scatterplot":

            if len(numeric_columns) >= 2:

                col1, col2 = st.columns(2)

                x_variable = col1.selectbox(
                    "Choose X variable",
                    numeric_columns,
                    key="scatter_x"
                )

                y_variable = col2.selectbox(
                    "Choose Y variable",
                    numeric_columns,
                    index=1,
                    key="scatter_y"
                )

                fig = px.scatter(
                    viz_df,
                    x=x_variable,
                    y=y_variable,
                    title=f"{y_variable} vs. {x_variable}"
                )

            else:
                fig = None

                st.warning(
                    "Scatterplots require at least two numeric columns."
                )

        else:

            selected_variable = st.selectbox(
                "Choose a variable",
                numeric_columns,
                key="boxplot_variable"
            )

            fig = px.box(
                viz_df,
                y=selected_variable,
                title=f"Boxplot of {selected_variable}"
            )

        if fig is not None:

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    else:
        st.info(
            "No numeric columns available for visualization."
        )

else:
    st.info("Upload a dataset to create visualizations.")
    