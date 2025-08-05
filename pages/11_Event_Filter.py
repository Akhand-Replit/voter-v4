import streamlit as st
import pandas as pd
from utils.database import Database
from utils.styling import apply_custom_styling
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Apply custom styling to the page
apply_custom_styling()

def event_filter_page():
    """
    Streamlit page to filter and display records based on a selected event.
    It provides a dropdown to select an event and shows all associated records
    in a clean, readable table upon filtering.
    """
    # Check if the user is authenticated before showing the page content
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.warning("অনুগ্রহ করে প্রথমে লগইন করুন")
        return

    st.title("🗓️ ইভেন্ট অনুযায়ী ফিল্টার")
    st.markdown("এখানে আপনি একটি নির্দিষ্ট ইভেন্টের জন্য নির্ধারিত সমস্ত রেকর্ড দেখতে পারেন।")

    db = Database()

    # --- Event Selection Dropdown ---
    try:
        # Fetch all available events from the database
        all_events = db.get_all_events()
        if not all_events:
            st.info("কোন ইভেন্ট পাওয়া যায়নি। অনুগ্রহ করে প্রথমে 'ইভেন্ট ম্যানেজমেন্ট' পেজ থেকে একটি ইভেন্ট তৈরি করুন।")
            return

        # Create a mapping from event name to event ID for easy lookup
        event_map = {event['name']: event['id'] for event in all_events}
        
        # Display a selectbox for the user to choose an event
        selected_event_name = st.selectbox(
            "একটি ইভেন্ট নির্বাচন করুন",
            options=event_map.keys(),
            help="তালিকা থেকে একটি ইভেন্ট নির্বাচন করে ফিল্টার করুন।"
        )

        # --- Filter Button ---
        if st.button("🔍 ফিল্টার করুন", type="primary", use_container_width=True):
            if selected_event_name:
                selected_event_id = event_map[selected_event_name]

                with st.spinner(f"'{selected_event_name}' ইভেন্টের জন্য রেকর্ড আনা হচ্ছে..."):
                    # Fetch records associated with the selected event from the database
                    records = db.get_records_for_event(selected_event_id)

                    if records:
                        st.success(f"'{selected_event_name}' ইভেন্টের জন্য {len(records)} টি রেকর্ড পাওয়া গেছে।")
                        
                        # Convert the list of records to a pandas DataFrame for display
                        df = pd.DataFrame(records)
                        
                        # Define which columns to display and in what order
                        display_columns = [
                            'ক্রমিক_নং', 'নাম', 'ভোটার_নং', 'পিতার_নাম', 'মাতার_নাম', 
                            'পেশা', 'ঠিকানা', 'জন্ম_তারিখ', 'phone_number', 
                            'facebook_link', 'relationship_status', 'gender', 'batch_name' # Added gender
                        ]
                        
                        # Ensure only existing columns are selected to prevent errors
                        df_display = df[[col for col in display_columns if col in df.columns]]

                        # Display the data in a table
                        st.dataframe(
                            df_display,
                            hide_index=True,
                            use_container_width=True
                        )
                    else:
                        st.info(f"'{selected_event_name}' ইভেন্টের জন্য কোনো রেকর্ড নির্ধারিত করা হয়নি।")

    except Exception as e:
        logger.error(f"Error fetching or displaying event data: {e}")
        st.error("ইভেন্টের ডেটা আনতে একটি অপ্রত্যাশিত সমস্যা হয়েছে।")

if __name__ == "__main__":
    event_filter_page()
