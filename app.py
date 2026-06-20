"""
Streamlit Dashboard for QuickCart Customer Feedback Analytics.

This dashboard provides interactive visualization and analysis of customer feedback data,
including sentiment analysis, complaint categories, and search functionality.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="QuickCart Customer Feedback Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .kpi-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .kpi-label {
        font-size: 1rem;
        color: #666;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


def load_data(file_path: str) -> pd.DataFrame:
    """
    Load enriched feedback data from CSV file.
    
    Args:
        file_path: Path to the CSV file.
        
    Returns:
        DataFrame containing the feedback data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    try:
        df = pd.read_csv(file_path)
        return df
    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
        st.info("Please run the data processing pipeline first to generate the enriched feedback data.")
        return None
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None


def calculate_kpis(df: pd.DataFrame) -> dict:
    """
    Calculate key performance indicators from the feedback data.
    
    Args:
        df: DataFrame containing feedback data.
        
    Returns:
        Dictionary containing KPI values.
    """
    kpis = {}
    
    # Total feedback count
    kpis['total_feedback'] = len(df)
    
    # Sentiment counts
    if 'sentiment' in df.columns:
        kpis['negative_feedback'] = len(df[df['sentiment'] == 'Negative'])
        kpis['positive_feedback'] = len(df[df['sentiment'] == 'Positive'])
    else:
        kpis['negative_feedback'] = 0
        kpis['positive_feedback'] = 0
    
    # Most common complaint category
    if 'category' in df.columns:
        category_counts = df['category'].value_counts()
        kpis['most_common_category'] = category_counts.index[0] if len(category_counts) > 0 else 'N/A'
    else:
        kpis['most_common_category'] = 'N/A'
    
    return kpis


def display_kpi_cards(kpis: dict) -> None:
    """
    Display KPI cards in a grid layout.
    
    Args:
        kpis: Dictionary containing KPI values.
    """
    st.subheader("Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-value">{}</div>
            <div class="kpi-label">Total Feedback</div>
        </div>
        """.format(kpis['total_feedback']), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-value">{}</div>
            <div class="kpi-label">Negative Feedback</div>
        </div>
        """.format(kpis['negative_feedback']), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-value">{}</div>
            <div class="kpi-label">Positive Feedback</div>
        </div>
        """.format(kpis['positive_feedback']), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-value">{}</div>
            <div class="kpi-label">Most Common Category</div>
        </div>
        """.format(kpis['most_common_category']), unsafe_allow_html=True)
    
    st.markdown("---")


def display_sentiment_analysis(df: pd.DataFrame) -> None:
    """
    Display sentiment analysis with pie chart and statistics table.
    
    Args:
        df: DataFrame containing feedback data.
    """
    st.subheader("Sentiment Analysis")
    
    if 'sentiment' not in df.columns:
        st.warning("Sentiment data not available")
        return
    
    # Calculate sentiment distribution
    sentiment_counts = df['sentiment'].value_counts()
    sentiment_percentages = (sentiment_counts / len(df) * 100).round(1)
    
    # Create pie chart
    col1, col2 = st.columns([1, 1])
    
    with col1:
        fig_pie = px.pie(
            values=sentiment_counts.values,
            names=sentiment_counts.index,
            title='Sentiment Distribution',
            color_discrete_map={
                'Positive': '#2ecc71',
                'Neutral': '#f39c12',
                'Negative': '#e74c3c'
            }
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Create statistics table
        sentiment_df = pd.DataFrame({
            'Sentiment': sentiment_counts.index,
            'Count': sentiment_counts.values,
            'Percentage': sentiment_percentages.values
        })
        st.dataframe(sentiment_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")


def display_category_analysis(df: pd.DataFrame) -> None:
    """
    Display complaint category analysis with bar chart and statistics table.
    
    Args:
        df: DataFrame containing feedback data.
    """
    st.subheader("Complaint Categories")
    
    if 'category' not in df.columns:
        st.warning("Category data not available")
        return
    
    # Calculate category distribution
    category_counts = df['category'].value_counts().sort_values(ascending=True)
    category_percentages = (category_counts / len(df) * 100).round(1)
    
    # Create bar chart
    col1, col2 = st.columns([1, 1])
    
    with col1:
        fig_bar = px.bar(
            x=category_counts.values,
            y=category_counts.index,
            orientation='h',
            title='Category Distribution',
            color=category_counts.values,
            color_continuous_scale='Blues'
        )
        fig_bar.update_layout(
            xaxis_title='Count',
            yaxis_title='Category',
            showlegend=False
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        # Create statistics table
        category_df = pd.DataFrame({
            'Category': category_counts.index,
            'Count': category_counts.values,
            'Percentage': category_percentages.values
        }).sort_values('Count', ascending=False)
        st.dataframe(category_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")


def display_example_complaints(df: pd.DataFrame) -> None:
    """
    Display representative complaints for selected category.
    
    Args:
        df: DataFrame containing feedback data.
    """
    st.subheader("Example Complaints by Category")
    
    if 'category' not in df.columns or 'feedback_text' not in df.columns:
        st.warning("Category or feedback data not available")
        return
    
    # Get unique categories
    categories = df['category'].unique()
    selected_category = st.selectbox("Select Category", categories)
    
    if selected_category:
        # Filter by selected category
        category_feedback = df[df['category'] == selected_category]['feedback_text'].head(5)
        
        if len(category_feedback) > 0:
            st.write(f"**{len(category_feedback)} representative complaints for {selected_category}:**")
            for i, feedback in enumerate(category_feedback, 1):
                st.markdown(f"{i}. \"{feedback}\"")
        else:
            st.info(f"No feedback available for {selected_category}")
    
    st.markdown("---")


def display_search_functionality(df: pd.DataFrame) -> None:
    """
    Display search functionality for feedback text.
    
    Args:
        df: DataFrame containing feedback data.
    """
    st.subheader("Search Feedback")
    
    if 'feedback_text' not in df.columns:
        st.warning("Feedback text data not available")
        return
    
    search_term = st.text_input("Enter search term:", placeholder="e.g., delivery, billing, app crash")
    
    if search_term:
        # Search in feedback text (case-insensitive)
        search_results = df[df['feedback_text'].str.contains(search_term, case=False, na=False)]
        
        if len(search_results) > 0:
            st.success(f"Found {len(search_results)} matching feedback entries")
            
            # Display results with key columns
            display_columns = ['feedback_text', 'sentiment', 'category', 'summary']
            available_columns = [col for col in display_columns if col in df.columns]
            
            st.dataframe(
                search_results[available_columns].head(20),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning(f"No feedback found containing '{search_term}'")
    
    st.markdown("---")


def display_raw_data(df: pd.DataFrame) -> None:
    """
    Display raw data table with download functionality.
    
    Args:
        df: DataFrame containing feedback data.
    """
    st.subheader("Raw Data Viewer")
    
    # Display dataframe
    st.dataframe(df, use_container_width=True)
    
    # Download button
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name='feedback_data.csv',
        mime='text/csv'
    )


def main():
    """
    Main function to run the Streamlit dashboard.
    """
    # Display title
    st.markdown('<h1 class="main-header">📊 QuickCart Customer Feedback Analytics</h1>', 
                unsafe_allow_html=True)
    
    # Load data
    data_file = 'outputs/cleaned_enriched_feedback.csv'
    df = load_data(data_file)
    
    if df is None:
        st.stop()
    
    # Calculate and display KPIs
    kpis = calculate_kpis(df)
    display_kpi_cards(kpis)
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Sentiment Analysis", 
        "Complaint Categories", 
        "Example Complaints", 
        "Search", 
        "Raw Data"
    ])
    
    with tab1:
        display_sentiment_analysis(df)
    
    with tab2:
        display_category_analysis(df)
    
    with tab3:
        display_example_complaints(df)
    
    with tab4:
        display_search_functionality(df)
    
    with tab5:
        display_raw_data(df)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>QuickCart Customer Feedback Analytics Dashboard</p>
        <p>Data refreshes on page reload</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
