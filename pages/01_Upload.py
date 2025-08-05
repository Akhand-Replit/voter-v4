import streamlit as st
import os
from attached_assets.data_processor import process_text_file
from utils.database import Database
from utils.styling import apply_custom_styling
import logging

logger = logging.getLogger(__name__)
apply_custom_styling()

def upload_page():
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.warning("অনুগ্রহ করে প্রথমে লগইন করুন")
        return

    st.title("📤 ফাইল আপলোড")

    db = Database()

    # Batch name input
    batch_name = st.text_input("ব্যাচের নাম", placeholder="ব্যাচের নাম লিখুন")

    # Gender selection for uploaded files
    selected_gender = st.selectbox(
        "লিঙ্গ নির্বাচন করুন (যদি ফাইলে উল্লেখ না থাকে)",
        options=['', 'Male', 'Female', 'Other'], # Empty string for 'not specified'
        format_func=lambda x: x if x else "নির্বাচন করুন"
    )

    # File upload
    uploaded_files = st.file_uploader(
        "টেক্সট ফাইল আপলোড করুন",
        type=['txt'],
        accept_multiple_files=True
    )

    if uploaded_files and batch_name:
        if st.button("আপলোড করুন", type="primary"):
            total_records_processed = 0
            total_records_added_to_db = 0

            try:
                with st.spinner("প্রক্রিয়াকরণ চলছে..."):
                    # Check if batch already exists
                    existing_batch = db.get_batch_by_name(batch_name)
                    if existing_batch:
                        batch_id = existing_batch['id']
                        st.info(f"'{batch_name}' ব্যাচে ফাইল যোগ করা হচ্ছে...")
                    else:
                        # Create new batch
                        batch_id = db.add_batch(batch_name)
                        st.success(f"নতুন ব্যাচ '{batch_name}' তৈরি করা হয়েছে")

                    # Start a single transaction for all files in this upload session
                    # db.conn.autocommit is already False from __init__

                    for uploaded_file in uploaded_files:
                        try:
                            content = uploaded_file.read().decode('utf-8')
                            records = process_text_file(content, default_gender=selected_gender if selected_gender else None)
                            total_records_processed += len(records)

                            for record in records:
                                db.add_record(batch_id, uploaded_file.name, record)
                                total_records_added_to_db += 1
                            
                            logger.info(f"Records from file '{uploaded_file.name}' prepared for insertion.")

                        except Exception as file_e:
                            # Log the error for this specific file but don't rollback the whole transaction yet
                            logger.error(f"Failed to process and add records for file {uploaded_file.name}: {file_e}")
                            st.error(f"ফাইল '{uploaded_file.name}' প্রক্রিয়াকরণ এবং যোগ করতে ব্যর্থ: {file_e}. এই ফাইলের কোনো রেকর্ড যোগ করা হয়নি।")
                            # Continue to next file, the overall transaction will be rolled back later if needed

                # After processing all files, attempt to commit all changes
                if total_records_added_to_db > 0:
                    db.commit_changes() # Explicitly commit here
                    st.success(f"সফলভাবে {len(uploaded_files)} টি ফাইল থেকে {total_records_added_to_db} টি রেকর্ড ডাটাবেসে আপলোড করা হয়েছে!")
                    st.markdown(f"**মোট রেকর্ড:** {db.get_total_records_count()}") # Display total count
                else:
                    st.warning("কোনো রেকর্ড ডাটাবেসে যোগ করা যায়নি। ফাইল ফরম্যাট বা ডাটাবেস স্কিমা পরীক্ষা করুন।")
                    db.rollback_changes() # Rollback if no records were added (e.g., all skipped or failed)

            except Exception as e:
                db.rollback_changes() # Ensure rollback for any top-level errors
                logger.error(f"Upload process failed: {str(e)}")
                st.error(f"আপলোড প্রক্রিয়া ব্যর্থ হয়েছে: {str(e)}")

    # Display existing batches
    st.subheader("বিদ্যমান ব্যাচসমূহ")
    batches = db.get_all_batches()

    if batches:
        for batch in batches:
            with st.expander(f"ব্যাচ: {batch['name']} ({batch['created_at'].strftime('%Y-%m-%d %H:%M')})"):
                records = db.get_batch_records(batch['id'])
                st.write(f"মোট রেকর্ড: {len(records)}")
    else:
        st.info("কোন ব্যাচ পাওয়া যায়নি")

if __name__ == "__main__":
    upload_page()
