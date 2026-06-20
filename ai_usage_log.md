# AI Usage Log

This document tracks how AI was used throughout the development of the QuickCart Customer Feedback Analyzer project, including initial implementations, issues encountered, and improvements made.

## Initial AI-Assisted Development

### Data Cleaning Pipeline
- **Used AI to generate initial cleaning logic** in `process_feedback.py`
  - Generated pandas-based data loading and validation functions
  - Implemented text normalization and duplicate removal logic
  - Created timestamp standardization using `pd.to_datetime(errors="coerce")`
  - Added test data pattern removal (e.g., "test test test ignore")

- **Verified duplicate removal manually**
  - Created `check_duplicates.py` to verify duplicate detection logic
  - Manually inspected sample records to ensure duplicate removal worked correctly
  - Confirmed that normalized text matching was identifying true duplicates

### AI Enrichment Pipeline
- **Used AI to build enrichment pipeline** in `enrich_feedback.py`
  - Generated OpenRouter API integration code
  - Implemented sentiment analysis with three categories (Positive, Neutral, Negative)
  - Created category classification with five predefined categories
  - Added summary generation for each feedback entry
  - Implemented JSON response parsing and validation

## Issues Identified and Resolved

### Performance Issue with Row-by-Row Requests
- **Problem**: Initial implementation sent one API request per feedback row
  - For a dataset of ~1,800 records, this would require ~1,800 API calls
  - Processing time would be extremely slow due to API latency
  - Risk of hitting rate limits and incurring excessive costs

- **Solution**: **Refactored to batch processing**
  - Implemented batch processing with `BATCH_SIZE = 20`
  - Single API request now processes 20 feedback items
  - Reduced API calls from ~1,800 to ~90 (95% reduction)
  - Significantly improved processing time and efficiency

### Rate Limit Issue
- **Problem**: OpenRouter free models have a rate limit of 16 requests per minute
  - Initial batch processing didn't account for rate limits
  - Risk of HTTP 429 errors during processing
  - Could cause batch failures and incomplete enrichment

- **Solution**: Implemented comprehensive rate limit handling
  - Added `REQUEST_DELAY = 5` seconds between successful batches
  - Implemented exponential backoff for HTTP 429 errors (10s, 20s, 40s)
  - Added retry logic with `MAX_RETRIES = 3`
  - Added logging for rate limit events: "Rate limit hit. Waiting X seconds before retry"

### AI Output Validation Issues
- **Problem**: Initial AI responses sometimes included invalid categories or sentiments
  - AI occasionally generated categories outside the predefined list
  - Sentiment values sometimes didn't match the three allowed values
  - JSON parsing failed when AI returned markdown code blocks

- **Solution**: Implemented robust validation
  - Created `validate_enrichment()` function to check sentiment and category values
  - Added `validate_batch_response()` for batch response validation
  - Implemented markdown code block removal before JSON parsing
  - Added fallback to "Other" category for ambiguous classifications
  - Implemented retry logic for invalid responses

## Verification and Testing

### Enrichment Results Verification
- **Verified enrichment results against sample records**
  - Manually inspected AI-generated sentiment, category, and summary for sample feedback
  - Confirmed sentiment classification aligned with human interpretation
  - Validated category assignments matched the primary issue in feedback
  - Checked that summaries accurately captured the main point

### Data Quality Validation
- **Test data removal verification**
  - Confirmed test patterns like "test test test ignore" were removed
  - Verified that legitimate feedback containing the word "test" was preserved
  - Validated that empty/null feedback was properly filtered out

- **Duplicate detection verification**
  - Tested duplicate detection with case variations and whitespace differences
  - Confirmed that normalized text matching correctly identified duplicates
  - Verified that the first occurrence was preserved and subsequent duplicates removed

## AI Model Selection and Configuration

### Model Choice
- **Selected**: Cohere/North Mini Code (free tier via OpenRouter)
- **Rationale**: 
  - Free tier available for development and testing
  - Good balance of performance and cost
  - Suitable for text classification and summarization tasks
  - Accessible via OpenRouter API with standard OpenAI client

### Prompt Engineering
- **Initial prompts**: Basic instructions for sentiment and category classification
- **Refined prompts**: Added specific rules and examples
  - Explicitly listed allowed sentiment values
  - Provided category descriptions with examples
  - Added rules for sarcasm detection and context consideration
  - Specified that rating field should be ignored for sentiment
  - Added instruction to use "Other" as fallback category

### Batch Processing Prompts
- **Challenge**: Getting AI to process multiple feedback items in one request
- **Solution**: Structured prompt with clear input/output format
  - Input: JSON array of feedback items with indices
  - Output: JSON array with results maintaining same indices
  - Added explicit instruction to return exactly one result per input item
  - Included rule to maintain index mapping for proper result assignment

## Iterative Improvements

### Test Mode Implementation
- **Added**: `TEST_MODE = True` and `TEST_ROWS = 50` configuration
- **Purpose**: Enable quick testing without processing full dataset
- **Benefit**: Rapid iteration during development and debugging
- **Trade-off**: Requires manual code change for production runs

### Error Handling Enhancement
- **Initial**: Basic try-catch blocks with generic error messages
- **Improved**: Granular error handling with specific error types
  - Separate handling for JSON parsing errors
  - Specific handling for rate limit errors (HTTP 429)
  - Detailed logging for debugging and monitoring
  - Retry logic with exponential backoff

### Logging Enhancement
- **Initial**: Minimal logging with basic progress messages
- **Improved**: Comprehensive logging at multiple levels
  - INFO level for progress tracking
  - WARNING level for validation failures and retries
  - ERROR level for critical failures
  - DEBUG level for detailed API responses
  - Structured log format with timestamps and level indicators

## Lessons Learned

### AI Limitations
1. **Context Understanding**: AI sometimes misses context in short feedback messages
   - Mitigation: Added rules for context consideration in prompts
   - Monitoring: Manual verification of edge cases

2. **Sarcasm Detection**: AI struggles with sarcasm in text-only analysis
   - Mitigation: Explicit instruction to detect sarcasm
   - Limitation: Not 100% accurate, requires human review for critical cases

3. **Category Ambiguity**: Some feedback doesn't fit neatly into predefined categories
   - Mitigation: "Other" category as fallback
   - Future improvement: Consider adding more granular subcategories

### API Considerations
1. **Rate Limits**: Free tier APIs have strict rate limits
   - Solution: Implemented delays and exponential backoff
   - Consideration: Production deployment may require paid tier for higher limits

2. **Response Consistency**: AI responses can vary between calls
   - Mitigation: Validation and retry logic
   - Monitoring: Track validation failure rates

3. **Cost Management**: API usage can become expensive at scale
   - Solution: Batch processing to minimize API calls
   - Future: Consider caching results for identical feedback

### Development Workflow
1. **Incremental Testing**: Test mode essential for rapid iteration
   - Benefit: Quick feedback loop during development
   - Practice: Always test with small subset before full processing

2. **Manual Verification**: AI outputs require human verification
   - Practice: Regular manual inspection of sample results
   - Importance: Ensures AI alignment with business requirements

3. **Error Recovery**: Robust error handling critical for production
   - Lesson: Plan for failures, implement retries and logging
   - Practice: Test error scenarios during development

## Future AI Enhancements

### Model Improvements
1. **Custom Model Training**: Train domain-specific sentiment model
   - Benefit: Better accuracy for QuickCart-specific feedback
   - Requirement: Labeled dataset for training

2. **Ensemble Methods**: Combine multiple AI models for robustness
   - Benefit: Improved accuracy through consensus
   - Trade-off: Increased complexity and cost

3. **Fine-tuning**: Fine-tune base model on customer feedback domain
   - Benefit: Better understanding of domain-specific language
   - Requirement: Access to fine-tuning API and training data

### Feature Enhancements
1. **Topic Modeling**: Add AI-powered topic extraction
   - Benefit: Identify emerging issues beyond predefined categories
   - Implementation: Use clustering or topic modeling algorithms

2. **Entity Recognition**: Extract named entities from feedback
   - Benefit: Identify specific products, locations, or features mentioned
   - Implementation: Use NER models or AI with entity extraction

3. **Sentiment Trends**: Track sentiment changes over time
   - Benefit: Identify improving or degrading customer satisfaction
   - Implementation: Time-series analysis with sentiment data

## Conclusion

AI was instrumental in rapidly developing the QuickCart Customer Feedback Analyzer, enabling sophisticated text analysis and categorization that would have been time-consuming to implement manually. Through iterative refinement and careful validation, we addressed performance issues, rate limiting challenges, and output quality concerns to create a robust production-ready system.

The key to success was balancing AI automation with human verification, implementing comprehensive error handling, and continuously refining prompts based on real-world testing. This approach ensured reliable, accurate results while leveraging AI's capabilities for efficient text analysis at scale.
