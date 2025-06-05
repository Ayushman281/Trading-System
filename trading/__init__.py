"""
Algorithmic trading module initialization.
"""
import os
from .data_generator import generate_sample_data

# Check if sample data exists, if not generate it
data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
sample_data_path = os.path.join(data_dir, "stock_data.csv")

if not os.path.exists(sample_data_path):
    generate_sample_data()
