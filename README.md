# QuickCart Customer Feedback Analyzer

A comprehensive customer feedback analysis system that processes raw customer feedback data, enriches it with AI-powered sentiment analysis and categorization, and provides interactive dashboards and reports for business insights.

## Overview

This project automates the analysis of customer feedback from multiple sources (app store reviews, survey comments, support tickets) to identify key issues, track sentiment trends, and provide actionable business recommendations. The system uses AI to categorize feedback and generate summaries, making it easy to understand customer pain points at scale.

## Architecture

```
customer_feedback_raw.csv
        ↓
    process_feedback.py
    (Data Cleaning & Validation)
        ↓
outputs/cleaned_feedback.csv
        ↓
    enrich_feedback.py
    (AI Enrichment: Sentiment, Category, Summary)
        ↓
outputs/cleaned_enriched_feedback.csv
        ↓
    ├── generate_report.py
    │   (Markdown Report Generation)
    │       ↓
    │   outputs/summary_report.md
    │
    └── app.py
        (Streamlit Dashboard)
            ↓
        Interactive Web Dashboard
```

## Dataset

The system processes customer feedback data with the following structure:

- **id**: Unique identifier for each feedback entry
- **timestamp**: When the feedback was received (various formats)
- **source**: Feedback source (app_store_review, survey_comment, support_ticket)
- **rating**: Customer rating (1-5 stars)
- **feedback_text**: The actual customer feedback message

### Data Sources

- **App Store Reviews**: Customer reviews from mobile app stores
- **Survey Comments**: Feedback from customer surveys
- **Support Tickets**: Issues reported via customer support channels

## Cleaning Logic

The `process_feedback.py` module performs comprehensive data cleaning:

### Data Validation
- Removes rows with null or empty feedback_text
- Removes rows where feedback_text becomes empty after trimming whitespace
- Removes obvious test data patterns (e.g., "test test test ignore", "test")

### Text Normalization
- Strips leading/trailing whitespace
- Collapses multiple spaces into single spaces
- Creates normalized version for duplicate detection (lowercase, trimmed)

### Timestamp Standardization
- Converts various timestamp formats to datetime using `pd.to_datetime(errors="coerce")`
- Preserves invalid timestamps as NaT rather than removing records
- Handles formats like: "02-Feb-24", "02/14/2024", "2024-03-25 16:31:48", "March 18, 2024"

### Duplicate Removal
- Identifies duplicates using normalized feedback text
- Keeps first occurrence, removes subsequent duplicates
- Logs number of duplicates removed

## AI Enrichment Logic

The `enrich_feedback.py` module uses OpenRouter API with the Cohere/North Mini Code model to analyze feedback in batches.

### Sentiment Analysis

Feedback is classified into three sentiment categories:

- **Positive**: Expresses satisfaction, praise, or positive experiences
- **Neutral**: Factual statements, mixed feedback, or mild comments
- **Negative**: Expresses dissatisfaction, complaints, or negative experiences

**Key Rules:**
- Sentiment is determined from feedback text only (rating field is ignored)
- Sarcasm detection is attempted
- Context is considered for accurate classification

### Category Classification

Feedback is categorized into five main categories:

- **Billing**: Issues related to charges, payments, coupons, refunds, pricing
- **App Bug**: Technical issues, crashes, app functionality problems, loading issues
- **Delivery**: Problems with order delivery, missing items, driver issues, late delivery
- **Staff/Support**: Interactions with customer service, agent behavior, support quality
- **Other**: Issues that don't fit into the above categories

**Classification Logic:**
- Uses predefined categories based on common customer feedback themes
- "Other" is used as a fallback for ambiguous or uncategorizable feedback
- Category assignment considers the primary issue mentioned in the feedback

### Summary Generation

Each feedback entry receives a concise one-line summary that captures the customer's main issue or point. This enables quick scanning of feedback without reading the full text.

### Batch Processing

To optimize API usage and respect rate limits:
- Processes feedback in batches of 20 records
- Implements 5-second delays between successful batches
- Uses exponential backoff (10s, 20s, 40s) for rate limit errors (HTTP 429)
- Retries failed requests up to 3 times

## Running Locally

### Prerequisites

- Python 3.11 or higher
- OpenRouter API key (set as `OPENROUTER_API_KEY` environment variable)

### Installation

```bash
pip install -r requirements.txt
```

### Setup Environment Variables

Create a `.env` file in the project root:

```
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

### Run the Pipeline

```bash
# Step 1: Clean the raw data
python process_feedback.py

# Step 2: Enrich with AI analysis
python enrich_feedback.py

# Step 3: Generate markdown report
python generate_report.py

# Step 4: Launch the dashboard
streamlit run app.py
```

### Expected Outputs

After running the pipeline:
- `outputs/cleaned_feedback.csv` - Cleaned and validated data
- `outputs/cleaned_enriched_feedback.csv` - AI-enriched data with sentiment, category, and summary
- `outputs/summary_report.md` - Comprehensive analysis report

### Dashboard Access

After running `streamlit run app.py`, the dashboard will be available at `http://localhost:8501`

## GitHub Actions

The project includes a CI workflow that validates the code and runs the data cleaning pipeline on push/PR to main branch.

### Workflow Steps

1. **Checkout Repository**: Retrieves the latest code
2. **Setup Python**: Configures Python 3.11 environment
3. **Install Dependencies**: Installs all required packages from requirements.txt
4. **Check Python Syntax**: Validates Python syntax for process_feedback.py
5. **Run Data Cleaning Pipeline**: Executes the data cleaning process
6. **Verify Outputs**: Checks that required output files exist
7. **Generate Report**: Creates summary report if enriched data is available

### Workflow Status

The CI workflow ensures that:
- Code syntax is valid before merging
- Data cleaning pipeline runs successfully
- Output files are generated correctly
- Report generation works when enriched data exists

## Trade-offs

### Design Decisions

1. **Timestamp Handling**: Invalid timestamps are kept as NaT rather than removed
   - *Rationale*: Preserves all feedback data for analysis, even with timing issues
   - *Trade-off*: Time-based analysis may have gaps

2. **Batch Size**: Fixed at 20 records per batch
   - *Rationale*: Balances API efficiency with rate limit compliance
   - *Trade-off*: May not be optimal for all dataset sizes

3. **Category Classification**: Uses predefined categories with "Other" fallback
   - *Rationale*: Ensures consistent categorization and simplifies analysis
   - *Trade-off*: May miss nuanced or emerging issue categories

4. **Sentiment from Text Only**: Ignores rating field for sentiment analysis
   - *Rationale*: Text provides more nuanced sentiment information
   - *Trade-off*: May disagree with explicit customer ratings

5. **Test Mode**: Hardcoded test rows limit (50) for development
   - *Rationale*: Enables quick testing without full dataset processing
   - *Trade-off*: Requires manual code change for production runs

### Performance Considerations

- **API Rate Limits**: 5-second delays between batches respect OpenRouter's 16 requests/minute limit
- **Memory Usage**: Entire dataset loaded into memory for processing
- **Processing Time**: AI enrichment is the bottleneck due to API calls and rate limiting

## Future Improvements

### Short-term Enhancements

1. **Configuration Management**
   - Move hardcoded values (BATCH_SIZE, TEST_MODE, etc.) to config file
   - Add command-line arguments for runtime configuration

2. **Error Handling**
   - Add more granular error logging
   - Implement checkpoint/resume functionality for long-running processes
   - Add data validation after each pipeline stage

3. **Testing**
   - Add unit tests for data cleaning functions
   - Add integration tests for the full pipeline
   - Add mock API responses for testing enrichment logic

### Medium-term Enhancements

1. **Advanced Analytics**
   - Time-series analysis of sentiment trends
   - Correlation between rating and sentiment
   - Category trend analysis over time
   - Word frequency analysis and topic modeling

2. **Dashboard Improvements**
   - Add date range filtering
   - Add source-based filtering
   - Add export functionality for filtered data
   - Add comparison views between time periods

3. **Data Quality**
   - Add data quality metrics dashboard
   - Implement automated data quality alerts
   - Add feedback data validation rules

### Long-term Enhancements

1. **Machine Learning**
   - Train custom sentiment model on domain-specific data
   - Implement custom category classification model
   - Add anomaly detection for unusual feedback patterns

2. **Real-time Processing**
   - Stream processing for real-time feedback analysis
   - WebSocket integration for live dashboard updates
   - Alert system for sudden negative sentiment spikes

3. **Integration**
   - API endpoints for programmatic access
   - Integration with customer support ticket systems
   - Automated report generation and email delivery

## Project Structure

```
feedback-analyzer/
│
├── customer_feedback_raw.csv          # Raw input data
├── process_feedback.py                # Data cleaning pipeline
├── enrich_feedback.py                 # AI enrichment pipeline
├── generate_report.py                 # Report generation
├── app.py                             # Streamlit dashboard
├── requirements.txt                    # Python dependencies
├── README.md                          # This file
├── AI_USAGE_LOG.md                    # AI usage documentation
│
├── outputs/                           # Generated outputs
│   ├── cleaned_feedback.csv           # Cleaned data
│   ├── cleaned_enriched_feedback.csv  # AI-enriched data
│   └── summary_report.md              # Analysis report
│
└── .github/
    └── workflows/
        └── ci.yml                      # CI/CD workflow
```

## License

This project is created as a technical assessment for QuickCart customer feedback analysis.

## Contact

For questions or issues related to this project, please refer to the project repository or contact the development team.
