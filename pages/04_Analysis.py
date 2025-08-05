import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.database import Database
from utils.styling import apply_custom_styling
import logging

logger = logging.getLogger(__name__)
apply_custom_styling()

def analysis_page():
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.warning("অনুগ্রহ করে প্রথমে লগইন করুন")
        return

    st.title("📊 ডাটা বিশ্লেষণ")

    db = Database()

    try:
        # Get all batches
        batches = db.get_all_batches()

        if not batches:
            st.info("বিশ্লেষণের জন্য কোন ডাটা পাওয়া যায়নি")
            return

        # Batch selection
        selected_batch = st.selectbox(
            "ব্যাচ নির্বাচন করুন",
            options=['সব ব্যাচ'] + [batch['name'] for batch in batches],
            format_func=lambda x: x
        )

        # Get selected batch ID
        selected_batch_id = None
        if selected_batch != 'সব ব্যাচ':
            selected_batch_id = next(batch['id'] for batch in batches if batch['name'] == selected_batch)

        # Total records metrics
        total_metrics_col1, total_metrics_col2 = st.columns(2)

        with total_metrics_col1:
            # Overall statistics
            if selected_batch == 'সব ব্যাচ':
                total_records = sum(len(db.get_batch_records(batch['id'])) for batch in batches)
                st.metric("মোট রেকর্ড (সব ব্যাচ)", total_records)
            else:
                batch_records = db.get_batch_records(selected_batch_id)
                st.metric(f"মোট রেকর্ড ({selected_batch})", len(batch_records))

        # --- Gender Distribution Analysis ---
        st.subheader("লিঙ্গ অনুযায়ী বিতরণ")
        gender_stats = db.get_gender_stats(selected_batch_id)

        if gender_stats:
            df_gender = pd.DataFrame(gender_stats)
            fig_gender = px.pie(
                df_gender,
                values='count',
                names='gender',
                title=f"লিঙ্গ অনুযায়ী বিতরণ ({selected_batch})",
                hole=0.3,
                color_discrete_map={
                    'Male': '#1f77b4',    # Blue
                    'Female': '#ff7f0e',  # Orange
                    'Other': '#2ca02c'    # Green
                }
            )
            fig_gender.update_layout(
                font=dict(family="Noto Sans Bengali"),
                height=500,
                showlegend=True
            )
            st.plotly_chart(fig_gender, use_container_width=True)
            
            # Display detailed gender table
            st.markdown("##### বিস্তারিত লিঙ্গ পরিসংখ্যান")
            st.dataframe(
                df_gender.rename(columns={'gender': 'লিঙ্গ', 'count': 'সংখ্যা'}),
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("লিঙ্গ বিশ্লেষণের জন্য কোন ডাটা পাওয়া যায়নি।")

        # --- Age Distribution Analysis ---
        st.subheader("বয়স অনুযায়ী বিতরণ")
        # Fetch age distribution from dashboard stats (which now includes it)
        dashboard_stats = db.get_dashboard_stats()
        age_distribution_data = dashboard_stats.get('age_distribution', [])

        if age_distribution_data:
            df_age = pd.DataFrame(age_distribution_data)
            # Sort age groups for better visualization
            df_age['age_group_sort_key'] = df_age['age_group'].apply(lambda x: int(x.split('-')[0]) if x != 'Unknown' else -1)
            df_age = df_age.sort_values('age_group_sort_key')

            fig_age = px.bar(
                df_age,
                x='age_group',
                y='count',
                title=f"বয়স অনুযায়ী বিতরণ ({selected_batch})",
                labels={'age_group': 'বয়স গ্রুপ', 'count': 'সংখ্যা'}
            )
            fig_age.update_layout(
                font=dict(family="Noto Sans Bengali"),
                height=500
            )
            st.plotly_chart(fig_age, use_container_width=True)

            st.markdown("##### বিস্তারিত বয়স পরিসংখ্যান")
            st.dataframe(
                df_age[['age_group', 'count']].rename(columns={'age_group': 'বয়স গ্রুপ', 'count': 'সংখ্যা'}),
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("বয়স বিশ্লেষণের জন্য কোন ডাটা পাওয়া যায়নি।")


        # --- Occupation Distribution Analysis ---
        st.subheader("পেশা অনুযায়ী বিতরণ")
        if selected_batch == 'সব ব্যাচ':
            occupation_stats = db.get_occupation_stats()
        else:
            occupation_stats = db.get_batch_occupation_stats(selected_batch_id)

        if occupation_stats:
            # Convert to DataFrame for visualization
            df_occupation = pd.DataFrame(occupation_stats)

            # Create donut chart
            fig_occupation = px.pie(
                df_occupation,
                values='count',
                names='পেশা',
                title=f"পেশা অনুযায়ী বিতরণ ({selected_batch})",
                hole=0.3
            )
            fig_occupation.update_layout(
                font=dict(family="Noto Sans Bengali"),
                height=500,
                showlegend=True
            )
            st.plotly_chart(fig_occupation, use_container_width=True)

            # Display detailed table
            st.markdown("##### বিস্তারিত পেশা পরিসংখ্যান")
            df_display = df_occupation.copy()
            df_display.columns = ['পেশা', 'সংখ্যা']
            df_display = df_display.sort_values('সংখ্যা', ascending=False)
            st.dataframe(
                df_display,
                hide_index=True,
                use_container_width=True
            )

        else:
            st.info("পেশা বিশ্লেষণের জন্য কোন ডাটা পাওয়া যায়নি")

        # --- Batch-wise Record Distribution (if 'সব ব্যাচ' selected) ---
        if selected_batch == 'সব ব্যাচ':
            st.subheader("ব্যাচ অনুযায়ী রেকর্ড বিতরণ")
            batch_stats = []
            for batch in batches:
                records = db.get_batch_records(batch['id'])
                batch_stats.append({
                    'ব্যাচ': batch['name'],
                    'রেকর্ড': len(records)
                })

            batch_df = pd.DataFrame(batch_stats)
            fig_bar = px.bar(
                batch_df,
                x='ব্যাচ',
                y='রেকর্ড',
                title="ব্যাচ অনুযায়ী মোট রেকর্ড"
            )
            fig_bar.update_layout(
                font=dict(family="Noto Sans Bengali"),
                height=400
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        st.error(f"বিশ্লেষণে সমস্যা হয়েছে: {str(e)}")

if __name__ == "__main__":
    analysis_page()
