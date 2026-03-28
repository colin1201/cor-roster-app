"""
Shared test fixtures for COR Roster App.
"""

import pandas as pd
import pytest


@pytest.fixture
def mt_csv_df():
    """Fake Media Tech volunteer DataFrame matching real sheet format."""
    return pd.DataFrame({
        "Name": [
            "Alan", "Ben", "Christine", "Colin", "Dannel",
            "Darrell", "Edmund", "Gavin", "Jax", "Jessica Tong",
            "Micah", "Mich Lo", "Sherry", "Timmy",
        ],
        "Media Team Lead": [
            "", "Yes", "", "", "",
            "", "", "Yes", "", "",
            "", "Yes", "", "",
        ],
        "Stream Director": [
            "Yes", "Yes", "", "Yes", "Yes",
            "", "", "Yes", "Yes", "Yes",
            "", "Yes", "", "",
        ],
        "Camera 1": [
            "Yes", "", "", "Yes", "Yes",
            "", "", "", "Yes", "Yes",
            "", "", "Yes", "",
        ],
        "Projection": [
            "", "", "Yes", "", "",
            "", "", "", "", "",
            "", "Yes", "", "Yes",
        ],
        "Sound": [
            "", "Yes", "", "", "",
            "", "", "Yes", "", "",
            "Yes", "", "", "",
        ],
    })


@pytest.fixture
def mt_csv_df_with_inactive(mt_csv_df):
    """Media Tech DataFrame including inactive volunteers (zero qualifications)."""
    inactive = pd.DataFrame({
        "Name": ["Rui Jie", "Wei Kiang"],
        "Media Team Lead": ["", ""],
        "Stream Director": ["", ""],
        "Camera 1": ["", ""],
        "Projection": ["", ""],
        "Sound": ["", ""],
    })
    return pd.concat([mt_csv_df, inactive], ignore_index=True)


@pytest.fixture
def welcome_csv_df():
    """Fake Welcome volunteer DataFrame matching real sheet format."""
    return pd.DataFrame({
        "Name": [
            "Cristal Lee", "Joshua Sum", "Jaslyn Wong", "Valerie Chee",
            "Malcolm Lee", "Jessline Lee", "David Sum", "Happy Sum",
            "Samuel Stephens", "Daniel Lim", "Marc Liew",
            "Julia Ang", "Kathleen Chia", "Alvin Chin",
            "Lim Siew Lin", "Michelle Fong", "Ong Yiling",
        ],
        "Welcome Team Lead": [
            "Yes", "Yes", "Yes", "Yes",
            "", "", "", "",
            "", "", "",
            "", "", "",
            "", "", "",
        ],
        "Member": [
            "", "", "", "",
            "Yes", "Yes", "Yes", "Yes",
            "Yes", "Yes", "Yes",
            "Yes", "Yes", "Yes",
            "Yes", "Yes", "Yes",
        ],
        "Gender": [
            "Female", "Male", "Female", "Female",
            "Male", "Female", "Male", "Female",
            "Male", "Male", "Male",
            "Female", "Female", "Male",
            "Female", "Female", "Female",
        ],
        "Couple": [
            "", "", "", "",
            1, 1, 2, 2,
            "", "", "",
            "", "", "",
            "", "", "",
        ],
        "Senior citizen": [
            "", "", "", "",
            "", "", "Yes", "Yes",
            "", "", "",
            "Yes", "Yes", "Yes",
            "", "", "",
        ],
    })
