import streamlit as st
import pandas as pd
import plotly.express as px
from utils.database import Database
from utils.styling import apply_custom_styling
from attached_assets.data_processor import calculate_age
import logging

logger = logging.getLogger(__name__)
apply_custom_styling()

def age_management_page():
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.warning("অনুগ্রহ করে প্রথমে লগইন করুন")
        return

    st.title("🎂 বয়স ম্যানেজমেন্ট এবং বিশ্লেষণ")
    st.markdown("এখানে আপনি বিদ্যমান রেকর্ডগুলির বয়স পুনরায় গণনা এবং আপডেট করতে পারেন এবং বয়স বিতরণ দেখতে পারেন।")

    db = Database()

    # --- Age Recalculation Section ---
    st.subheader("বয়স পুনরায় গণনা করুন")
    st.info("এই বৈশিষ্ট্যটি বিদ্যমান সমস্ত রেকর্ডের জন্য জন্ম তারিখের উপর ভিত্তি করে বয়স পুনরায় গণনা করবে এবং আপডেট করবে।")

    if st.button("🔄 সমস্ত বয়স আপডেট করুন", type="primary", use_container_width=True):
        try:
            with st.spinner("বয়স আপডেট করা হচ্ছে... এটি কিছু সময় নিতে পারে।"):
                records_to_update = db.get_all_records_with_dob()
                updated_count = 0
                
                # Start a transaction for bulk updates
                # db.conn.autocommit is already False from __init__, so no need to set it again
                # However, ensure a fresh transaction context is used if needed.
                # The key is to commit/rollback before any Streamlit state changes/reruns.

                for record in records_to_update:
                    record_id = record['id']
                    dob_str = record['জন্ম_তারিখ']
                    new_age = calculate_age(dob_str)
                    
                    if new_age is not None:
                        db.update_record_age(record_id, new_age)
                        updated_count += 1
                
                db.commit_changes() # Commit all updates at once
                
                # Move st.success and st.rerun outside the transaction scope
                st.success(f"✅ সফলভাবে {updated_count} টি রেকর্ডের বয়স আপডেট করা হয়েছে!")
                st.rerun() # Rerun to refresh the page and stats
        except Exception as e:
            db.rollback_changes() # Rollback on error
            logger.error(f"Error updating all ages: {e}")
            st.error(f"বয়স আপডেট করার সময় একটি সমস্যা হয়েছে: {str(e)}")

    st.markdown("---")

    # --- Age Distribution Analysis ---
    st.subheader("বয়স অনুযায়ী বিতরণ")

    # Fetch age distribution from dashboard stats
    dashboard_stats = db.get_dashboard_stats()
    age_distribution_data = dashboard_stats.get('age_distribution', [])

    if age_distribution_data:
        df_age = pd.DataFrame(age_distribution_data)
        
        # Sort age groups for better visualization
        # Handle 'Unknown' or other non-numeric labels for sorting
        df_age['age_group_sort_key'] = df_age['age_group'].apply(lambda x: int(x.split('-')[0]) if x != 'Unknown' else -1)
        df_age = df_age.sort_values('age_group_sort_key')


        fig_age = px.bar(
            df_age,
            x='age_group',
            y='count',
            title="বয়স গ্রুপ অনুযায়ী রেকর্ড বিতরণ",
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
        st.info("বয়স বিশ্লেষণের জন্য কোন ডাটা পাওয়া যায়নি। অনুগ্রহ করে প্রথমে রেকর্ড আপলোড করুন বা বয়স আপডেট করুন।")

if __name__ == "__main__":
    age_management_page()
