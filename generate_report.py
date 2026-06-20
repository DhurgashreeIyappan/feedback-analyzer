"""
Report generation module for customer feedback analysis.

This module generates a markdown summary report from enriched feedback data,
including top complaint categories, sentiment breakdown, and representative examples.
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_enriched_data(file_path: str) -> pd.DataFrame:
    """
    Load enriched feedback data from a CSV file.
    
    Args:
        file_path: Path to the CSV file containing enriched feedback data.
        
    Returns:
        DataFrame containing the enriched feedback data.
        
    Raises:
        FileNotFoundError: If the specified file does not exist.
        pd.errors.EmptyDataError: If the file is empty.
    """
    logger.info(f"Loading enriched data from {file_path}")
    df = pd.read_csv(file_path)
    logger.info(f"Loaded {len(df)} rows from {file_path}")
    return df


def get_top_categories(df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    """
    Get the top N categories by volume.
    
    Args:
        df: DataFrame containing enriched feedback data.
        top_n: Number of top categories to return.
        
    Returns:
        DataFrame with category, count, and percentage, sorted by count descending.
    """
    logger.info(f"Calculating top {top_n} categories by volume")
    
    # Count categories
    category_counts = df['category'].value_counts().reset_index()
    category_counts.columns = ['category', 'count']
    
    # Calculate percentage
    total = len(df)
    category_counts['percentage'] = (category_counts['count'] / total * 100).round(1)
    
    # Get top N
    top_categories = category_counts.head(top_n)
    
    logger.info(f"Top {top_n} categories calculated")
    return top_categories


def get_sentiment_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """
    Get the overall sentiment breakdown.
    
    Args:
        df: DataFrame containing enriched feedback data.
        
    Returns:
        DataFrame with sentiment, count, and percentage.
    """
    logger.info("Calculating sentiment breakdown")
    
    # Count sentiments
    sentiment_counts = df['sentiment'].value_counts().reset_index()
    sentiment_counts.columns = ['sentiment', 'count']
    
    # Calculate percentage
    total = len(df)
    sentiment_counts['percentage'] = (sentiment_counts['count'] / total * 100).round(1)
    
    logger.info("Sentiment breakdown calculated")
    return sentiment_counts


def get_representative_examples(df: pd.DataFrame, category: str, n_examples: int = 3) -> List[str]:
    """
    Get representative customer messages for a specific category.
    
    Args:
        df: DataFrame containing enriched feedback data.
        category: The category to get examples for.
        n_examples: Number of examples to return.
        
    Returns:
        List of representative feedback text examples.
    """
    logger.info(f"Getting {n_examples} representative examples for category: {category}")
    
    # Filter by category
    category_df = df[df['category'] == category]
    
    if len(category_df) == 0:
        logger.warning(f"No examples found for category: {category}")
        return []
    
    # Get sample feedback texts
    examples = category_df['feedback_text'].head(n_examples).tolist()
    
    logger.info(f"Retrieved {len(examples)} examples for category: {category}")
    return examples


def generate_business_recommendation(top_category: str, negative_percentage: float) -> str:
    """
    Generate a business recommendation based on analysis results.
    
    Args:
        top_category: The most common complaint category.
        negative_percentage: Percentage of negative feedback.
        
    Returns:
        Business recommendation string.
    """
    logger.info("Generating business recommendation")
    
    if negative_percentage > 50:
        return f"Urgent action required: {negative_percentage:.1f}% of feedback is negative. Prioritize addressing {top_category} issues immediately to improve customer satisfaction."
    elif negative_percentage > 30:
        return f"Significant concern: {negative_percentage:.1f}% of feedback is negative. Focus on improving {top_category} processes and implement customer feedback loops."
    elif top_category == "App Bug":
        return "Invest in QA and automated testing to reduce app-related issues and improve overall user experience."
    elif top_category == "Delivery":
        return "Review delivery logistics and partner with reliable delivery services to ensure timely and accurate order fulfillment."
    elif top_category == "Billing":
        return "Audit billing systems and improve transparency in pricing to reduce billing-related complaints."
    elif top_category == "Staff/Support":
        return "Enhance staff training programs and implement quality assurance for customer support interactions."
    else:
        return f"Continue monitoring {top_category} feedback and implement targeted improvements based on specific customer issues."


def generate_markdown_report(
    top_categories: pd.DataFrame,
    sentiment_breakdown: pd.DataFrame,
    representative_examples: Dict[str, List[str]],
    total_feedback: int
) -> str:
    """
    Generate a markdown report from the analysis results.
    
    Args:
        top_categories: DataFrame with top categories and statistics.
        sentiment_breakdown: DataFrame with sentiment statistics.
        representative_examples: Dictionary mapping categories to example lists.
        total_feedback: Total number of feedback analyzed.
        
    Returns:
        Markdown formatted report string.
    """
    logger.info("Generating markdown report")
    
    # Calculate executive summary metrics
    most_common_category = top_categories.iloc[0]['category']
    most_common_count = top_categories.iloc[0]['count']
    
    # Get negative sentiment percentage
    negative_row = sentiment_breakdown[sentiment_breakdown['sentiment'] == 'Negative']
    negative_percentage = negative_row.iloc[0]['percentage'] if len(negative_row) > 0 else 0.0
    
    # Generate business recommendation
    recommendation = generate_business_recommendation(most_common_category, negative_percentage)
    
    report_lines = [
        "# Customer Feedback Analysis Report",
        "",
        "## Executive Summary",
        "",
        f"- **Total Feedback Analyzed:** {total_feedback}",
        f"- **Most Common Complaint Category:** {most_common_category} ({most_common_count} entries, {top_categories.iloc[0]['percentage']}%)",
        f"- **Negative Feedback Percentage:** {negative_percentage}%",
        f"- **Business Recommendation:** {recommendation}",
        "",
        "## Top 5 Complaint Categories by Volume",
        "",
        "| Category | Count | Percentage |",
        "|----------|-------|------------|",
    ]
    
    # Add top categories table
    for _, row in top_categories.iterrows():
        report_lines.append(f"| {row['category']} | {row['count']} | {row['percentage']}% |")
    
    report_lines.extend([
        "",
        "## Overall Sentiment Breakdown",
        "",
        "| Sentiment | Count | Percentage |",
        "|-----------|-------|------------|",
    ])
    
    # Add sentiment breakdown table
    for _, row in sentiment_breakdown.iterrows():
        report_lines.append(f"| {row['sentiment']} | {row['count']} | {row['percentage']}% |")
    
    # Add representative examples for each top category
    report_lines.append("")
    report_lines.append("## Representative Examples")
    report_lines.append("")
    
    for category in top_categories['category']:
        examples = representative_examples.get(category, [])
        report_lines.append(f"### {category}")
        report_lines.append("")
        
        if examples:
            for i, example in enumerate(examples, 1):
                report_lines.append(f"{i}. \"{example}\"")
        else:
            report_lines.append("No examples available.")
        
        report_lines.append("")
    
    report = "\n".join(report_lines)
    logger.info("Markdown report generated")
    
    return report


def save_report(report: str, output_path: str) -> None:
    """
    Save the markdown report to a file.
    
    Args:
        report: Markdown report string.
        output_path: Path where the report will be saved.
        
    Raises:
        OSError: If the output directory cannot be created or file cannot be written.
    """
    logger.info(f"Saving report to {output_path}")
    
    # Create output directory if it doesn't exist
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"Successfully saved report to {output_path}")


def main() -> None:
    """
    Main function to orchestrate the report generation process.
    
    This function:
    1. Loads enriched feedback data from outputs/cleaned_enriched_feedback.csv
    2. Calculates top categories and sentiment breakdown
    3. Gets representative examples for each top category
    4. Generates and saves the markdown report to outputs/summary_report.md
    """
    # File paths
    input_file = 'outputs/cleaned_enriched_feedback.csv'
    output_file = 'outputs/summary_report.md'
    
    try:
        # Load enriched data
        df = load_enriched_data(input_file)
        
        # Get top 5 categories
        top_categories = get_top_categories(df, top_n=5)
        
        # Get sentiment breakdown
        sentiment_breakdown = get_sentiment_breakdown(df)
        
        # Get representative examples for each top category
        representative_examples = {}
        for category in top_categories['category']:
            examples = get_representative_examples(df, category, n_examples=3)
            representative_examples[category] = examples
        
        # Generate markdown report
        report = generate_markdown_report(top_categories, sentiment_breakdown, representative_examples, len(df))
        
        # Save report
        save_report(report, output_file)
        
        # Print summary
        print("\n" + "="*50)
        print("Report Generation Summary")
        print("="*50)
        print(f"Total feedback analyzed: {len(df)}")
        print(f"Top category: {top_categories.iloc[0]['category']} ({top_categories.iloc[0]['count']} entries)")
        print(f"Report saved to: {output_file}")
        print("="*50 + "\n")
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during report generation: {e}")
        raise


if __name__ == "__main__":
    main()
