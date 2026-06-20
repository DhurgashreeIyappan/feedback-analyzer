"""
Data loading and cleaning module for customer feedback analysis.

This module handles loading raw customer feedback data, cleaning it by removing
invalid entries, normalizing text and timestamps, and saving the cleaned data.
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_data(file_path: str) -> pd.DataFrame:
    """
    Load customer feedback data from a CSV file.
    
    Args:
        file_path: Path to the CSV file containing raw feedback data.
        
    Returns:
        DataFrame containing the loaded feedback data.
        
    Raises:
        FileNotFoundError: If the specified file does not exist.
        pd.errors.EmptyDataError: If the file is empty.
    """
    logger.info(f"Loading data from {file_path}")
    df = pd.read_csv(file_path)
    logger.info(f"Loaded {len(df)} rows from {file_path}")
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean customer feedback data by removing invalid entries and normalizing fields.
    
    This function performs the following cleaning operations:
    - Removes rows with null or empty feedback_text
    - Removes obvious test data entries
    - Normalizes feedback_text (strip whitespace, collapse spaces)
    - Normalizes timestamps to datetime format
    - Removes duplicate feedback based on normalized text
    
    Args:
        df: Raw DataFrame containing feedback data.
        
    Returns:
        Cleaned DataFrame with invalid entries removed and fields normalized.
    """
    original_count = len(df)
    logger.info(f"Starting data cleaning with {original_count} rows")
    
    # Create a copy to avoid modifying the original
    df_clean = df.copy()
    
    # Remove rows where feedback_text is null
    df_clean = df_clean[df_clean['feedback_text'].notna()]
    null_removed = original_count - len(df_clean)
    logger.info(f"Removed {null_removed} rows with null feedback_text")
    
    # Remove rows where feedback_text becomes empty after trimming whitespace
    df_clean['feedback_text'] = df_clean['feedback_text'].str.strip()
    df_clean = df_clean[df_clean['feedback_text'] != '']
    empty_removed = original_count - null_removed - len(df_clean)
    logger.info(f"Removed {empty_removed} rows with empty feedback_text after trimming")
    
    # Remove obvious test data
    test_patterns = [
        'test test test ignore',
        'test',
    ]
    
    # Create normalized feedback for duplicate detection and test data removal
    df_clean['normalized_feedback'] = (
        df_clean['feedback_text']
        .str.lower()
        .str.strip()
        .str.replace(r'\s+', ' ', regex=True)
    )
    
    # Remove rows matching test patterns (case-insensitive)
    for pattern in test_patterns:
        pattern_lower = pattern.lower()
        before_removal = len(df_clean)
        df_clean = df_clean[df_clean['normalized_feedback'] != pattern_lower]
        removed = before_removal - len(df_clean)
        if removed > 0:
            logger.info(f"Removed {removed} rows matching test pattern: '{pattern}'")
    
    # Normalize feedback_text: strip whitespace and collapse multiple spaces
    df_clean['feedback_text'] = (
        df_clean['feedback_text']
        .str.strip()
        .str.replace(r'\s+', ' ', regex=True)
    )
    
    # Normalize timestamps: convert to datetime, keep invalid as NaT
    df_clean['timestamp'] = pd.to_datetime(df_clean['timestamp'], errors='coerce')
    logger.info("Normalized timestamps to datetime format")
    
    # Remove genuine duplicate feedback based on normalized_feedback
    before_dedup = len(df_clean)
    df_clean = df_clean.drop_duplicates(subset=['normalized_feedback'], keep='first')
    duplicates_removed = before_dedup - len(df_clean)
    logger.info(f"Removed {duplicates_removed} duplicate feedback entries")
    
    # Drop normalized_feedback column before final output
    df_clean = df_clean.drop(columns=['normalized_feedback'])
    
    final_count = len(df_clean)
    logger.info(f"Data cleaning complete. Final row count: {final_count}")
    
    # Store cleaning statistics as attributes for later access
    df_clean.attrs['original_count'] = original_count
    df_clean.attrs['final_count'] = final_count
    df_clean.attrs['duplicates_removed'] = duplicates_removed
    df_clean.attrs['empty_removed'] = null_removed + empty_removed
    
    return df_clean


def save_cleaned_data(df: pd.DataFrame, output_path: str) -> None:
    """
    Save cleaned DataFrame to a CSV file.
    
    Args:
        df: Cleaned DataFrame to save.
        output_path: Path where the cleaned CSV file will be saved.
        
    Raises:
        OSError: If the output directory cannot be created or file cannot be written.
    """
    logger.info(f"Saving cleaned data to {output_path}")
    
    # Create output directory if it doesn't exist
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Successfully saved {len(df)} rows to {output_path}")


def main() -> None:
    """
    Main function to orchestrate the data loading, cleaning, and saving process.
    
    This function:
    1. Loads raw feedback data from customer_feedback_raw.csv
    2. Cleans the data using the clean_data function
    3. Saves the cleaned data to outputs/cleaned_feedback.csv
    4. Prints cleaning statistics
    """
    # File paths
    input_file = 'customer_feedback_raw.csv'
    output_file = 'outputs/cleaned_feedback.csv'
    
    try:
        # Load data
        df = load_data(input_file)
        original_count = len(df)
        
        # Clean data
        df_clean = clean_data(df)
        
        # Save cleaned data
        save_cleaned_data(df_clean, output_file)
        
        # Print statistics
        print("\n" + "="*50)
        print("Data Cleaning Statistics")
        print("="*50)
        print(f"Original row count: {original_count}")
        print(f"Cleaned row count: {df_clean.attrs['final_count']}")
        print(f"Number of duplicates removed: {df_clean.attrs['duplicates_removed']}")
        print(f"Number of empty/null rows removed: {df_clean.attrs['empty_removed']}")
        print("="*50 + "\n")
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during data processing: {e}")
        raise


if __name__ == "__main__":
    main()
