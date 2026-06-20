"""
AI enrichment module for customer feedback analysis.

This module uses OpenRouter API to analyze customer feedback and generate
sentiment, category, and summary for each feedback entry.
"""

import logging
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from openai import OpenAI
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
BATCH_SIZE = 20
TEST_MODE = False
TEST_ROWS = 50
ALLOWED_SENTIMENTS = ["Positive", "Neutral", "Negative"]
ALLOWED_CATEGORIES = ["Billing", "App Bug", "Delivery", "Staff/Support", "Other"]
MAX_RETRIES = 3
REQUEST_DELAY = 5

# Initialize OpenRouter client
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)


def validate_enrichment(data: Dict) -> Tuple[bool, Optional[str]]:
    """
    Validate the AI enrichment output.
    
    Args:
        data: Dictionary containing sentiment, category, and summary.
        
    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is None.
    """
    required_fields = ["sentiment", "category", "summary"]
    
    # Check required fields
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
    
    # Validate sentiment
    if data["sentiment"] not in ALLOWED_SENTIMENTS:
        return False, f"Invalid sentiment: {data['sentiment']}. Allowed: {ALLOWED_SENTIMENTS}"
    
    # Validate category
    if data["category"] not in ALLOWED_CATEGORIES:
        return False, f"Invalid category: {data['category']}. Allowed: {ALLOWED_CATEGORIES}"
    
    # Validate summary is not empty
    if not data["summary"] or not data["summary"].strip():
        return False, "Summary cannot be empty"
    
    return True, None


def validate_batch_response(results: List[Dict]) -> Tuple[bool, Optional[str]]:
    """
    Validate the batch response from the API.
    
    Args:
        results: List of dictionaries containing enrichment results.
        
    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is None.
    """
    if not isinstance(results, list):
        return False, "Response is not a list"
    
    for result in results:
        if not isinstance(result, dict):
            return False, "Result item is not a dictionary"
        
        if "index" not in result:
            return False, "Result missing 'index' field"
        
        # Validate the enrichment data
        is_valid, error_msg = validate_enrichment(result)
        if not is_valid:
            return False, f"Invalid enrichment at index {result.get('index', 'unknown')}: {error_msg}"
    
    return True, None


def analyze_feedback_batch(feedback_items: List[Dict]) -> Optional[List[Dict]]:
    """
    Analyze a batch of feedback texts using OpenRouter API.
    
    Args:
        feedback_items: List of dictionaries with 'index' and 'feedback' keys.
        
    Returns:
        List of dictionaries with index, sentiment, category, and summary if successful,
        None if analysis fails.
    """
    # Build input JSON
    input_json = json.dumps(feedback_items, indent=2)
    
    prompt = f"""Analyze the following customer feedback items and return ONLY valid JSON array:

Input format:
{input_json}

Output format (return JSON array with one result per feedback):
[
  {{
    "index": 0,
    "sentiment": "Positive|Neutral|Negative",
    "category": "Billing|App Bug|Delivery|Staff/Support|Other",
    "summary": "one sentence summary"
  }},
  ...
]

Rules:
- Ignore rating when determining sentiment
- Use feedback text only
- Detect sarcasm correctly
- Use ONLY the allowed categories: {ALLOWED_CATEGORIES}
- If unsure, use Other
- Maintain the same index from input
- Return exactly one result per input item
- Return ONLY the JSON array, no other text"""
    
    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model="cohere/north-mini-code:free",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.choices[0].message.content.strip()
            logger.debug(f"Raw API response: {content}")
            
            # Parse JSON response
            try:
                # Remove markdown code blocks if present
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                    content = content.strip()
                
                results = json.loads(content)
                
                # Validate the response
                is_valid, error_msg = validate_batch_response(results)
                if not is_valid:
                    logger.warning(f"Invalid AI response: {error_msg}. Response: {results}")
                    if attempt < MAX_RETRIES - 1:
                        logger.info(f"Retrying... (attempt {attempt + 2}/{MAX_RETRIES})")
                        time.sleep(1)
                        continue
                    return None
                
                return results
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}. Content: {content}")
                if attempt < MAX_RETRIES - 1:
                    logger.info(f"Retrying... (attempt {attempt + 2}/{MAX_RETRIES})")
                    time.sleep(1)
                    continue
                return None
                
        except Exception as e:
            # Check for rate limit error (HTTP 429)
            error_str = str(e).lower()
            if '429' in error_str or 'rate limit' in error_str:
                # Exponential backoff for rate limit: 10s, 20s, 40s
                wait_time = 10 * (2 ** attempt)
                logger.warning(f"Rate limit hit. Waiting {wait_time} seconds before retry.")
                time.sleep(wait_time)
                if attempt < MAX_RETRIES - 1:
                    logger.info(f"Retrying... (attempt {attempt + 2}/{MAX_RETRIES})")
                    continue
                else:
                    logger.error("Max retries reached for rate limit. Giving up.")
                    return None
            else:
                logger.error(f"Error calling OpenRouter API: {e}")
                if attempt < MAX_RETRIES - 1:
                    logger.info(f"Retrying... (attempt {attempt + 2}/{MAX_RETRIES})")
                    time.sleep(1)
                    continue
                return None
    
    return None


def enrich_feedback_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enrich feedback data with AI-generated sentiment, category, and summary using batch processing.
    
    Args:
        df: DataFrame containing cleaned feedback data.
        
    Returns:
        DataFrame with added sentiment, category, and summary columns.
    """
    logger.info(f"Starting AI enrichment for {len(df)} rows")
    
    # Create a copy to avoid modifying the original
    df_enriched = df.copy()
    
    # Initialize new columns
    df_enriched['sentiment'] = None
    df_enriched['category'] = None
    df_enriched['summary'] = None
    
    # Limit rows if in test mode
    if TEST_MODE:
        df_enriched = df_enriched.head(TEST_ROWS)
        logger.info(f"TEST_MODE: Processing only first {len(df_enriched)} rows")
    
    total_rows = len(df_enriched)
    success_count = 0
    error_count = 0
    
    # Calculate number of batches
    num_batches = (total_rows + BATCH_SIZE - 1) // BATCH_SIZE
    logger.info(f"Processing {total_rows} rows in {num_batches} batches of size {BATCH_SIZE}")
    
    # Process in batches
    for batch_num in range(num_batches):
        start_idx = batch_num * BATCH_SIZE
        end_idx = min(start_idx + BATCH_SIZE, total_rows)
        
        logger.info(f"Processing batch {batch_num + 1}/{num_batches} (rows {start_idx + 1}-{end_idx})")
        
        # Prepare batch items
        batch_items = []
        for i in range(start_idx, end_idx):
            row = df_enriched.iloc[i]
            batch_items.append({
                "index": i,
                "feedback": row['feedback_text']
            })
        
        # Analyze batch
        results = analyze_feedback_batch(batch_items)
        
        if results:
            for result in results:
                idx = result['index']
                df_enriched.at[idx, 'sentiment'] = result['sentiment']
                df_enriched.at[idx, 'category'] = result['category']
                df_enriched.at[idx, 'summary'] = result['summary']
                success_count += 1
            logger.info(f"Successfully enriched batch {batch_num + 1}/{num_batches}")
            
            # Add delay after successful batch to respect rate limits
            if batch_num < num_batches - 1:  # Don't delay after the last batch
                logger.debug(f"Waiting {REQUEST_DELAY} seconds before next batch")
                time.sleep(REQUEST_DELAY)
        else:
            error_count += (end_idx - start_idx)
            logger.warning(f"Failed to enrich batch {batch_num + 1}/{num_batches}")
    
    logger.info(f"Enrichment complete. Success: {success_count}, Errors: {error_count}")
    
    return df_enriched


def save_enriched_data(df: pd.DataFrame, output_path: str) -> None:
    """
    Save enriched DataFrame to a CSV file.
    
    Args:
        df: Enriched DataFrame to save.
        output_path: Path where the enriched CSV file will be saved.
        
    Raises:
        OSError: If the output directory cannot be created or file cannot be written.
    """
    logger.info(f"Saving enriched data to {output_path}")
    
    # Create output directory if it doesn't exist
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Successfully saved {len(df)} rows to {output_path}")


def main() -> None:
    """
    Main function to orchestrate the AI enrichment process.
    
    This function:
    1. Loads cleaned feedback data from outputs/cleaned_feedback.csv
    2. Enriches the data with AI-generated sentiment, category, and summary
    3. Saves the enriched data to outputs/cleaned_enriched_feedback.csv
    4. Prints enrichment statistics
    """
    # File paths
    input_file = 'outputs/cleaned_feedback.csv'
    output_file = 'outputs/cleaned_enriched_feedback.csv'
    
    # Check for API key
    if not os.getenv("OPENROUTER_API_KEY"):
        logger.error("OPENROUTER_API_KEY environment variable not set")
        raise ValueError("OPENROUTER_API_KEY environment variable not set")
    
    try:
        # Load cleaned data
        logger.info(f"Loading cleaned data from {input_file}")
        df = pd.read_csv(input_file)
        logger.info(f"Loaded {len(df)} rows from {input_file}")
        
        # Enrich data
        df_enriched = enrich_feedback_data(df)
        
        # Save enriched data
        save_enriched_data(df_enriched, output_file)
        
        # Print statistics
        total_rows = len(df_enriched)
        enriched_rows = df_enriched['sentiment'].notna().sum()
        failed_rows = total_rows - enriched_rows
        
        print("\n" + "="*50)
        print("AI Enrichment Statistics")
        print("="*50)
        print(f"Total rows processed: {total_rows}")
        print(f"Successfully enriched: {enriched_rows}")
        print(f"Failed to enrich: {failed_rows}")
        print(f"Success rate: {(enriched_rows/total_rows*100):.1f}%")
        print("="*50 + "\n")
        
        # Print distribution if successful
        if enriched_rows > 0:
            print("\nSentiment Distribution:")
            print(df_enriched['sentiment'].value_counts())
            print("\nCategory Distribution:")
            print(df_enriched['category'].value_counts())
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during data enrichment: {e}")
        raise


if __name__ == "__main__":
    main()
