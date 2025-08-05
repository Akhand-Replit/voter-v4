import streamlit as st
from utils.database import Database
from utils.styling import apply_custom_styling
import logging

logger = logging.getLogger(__name__)
apply_custom_styling()

def events_page():
    """
    Streamlit page for managing events.
    Allows adding, viewing, and deleting events.
    """
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.warning("অনুগ্রহ করে প্রথমে লগইন করুন")
        return

    st.title("🗓️ ইভেন্ট ম্যানেজমেন্ট")

    db = Database()

    # --- Add New Event Section ---
    st.subheader("➕ নতুন ইভেন্ট যোগ করুন")
    with st.form("new_event_form", clear_on_submit=True):
        event_name = st.text_input("ইভেন্টের নাম", placeholder="যেমন: বার্ষিক সম্মেলন ২০২২")
        submitted = st.form_submit_button("ইভেন্ট যোগ করুন")

        if submitted and event_name:
            try:
                db.add_event(event_name)
                st.success(f"✅ ইভেন্ট '{event_name}' সফলভাবে যোগ করা হয়েছে।")
            except Exception as e:
                logger.error(f"Error adding event: {e}")
                st.error("এই নামের ইভেন্ট ইতিমধ্যে বিদ্যমান।")

    st.markdown("---")

    # --- Existing Events Section ---
    st.subheader("📋 বিদ্যমান ইভেন্ট তালিকা")
    
    try:
        all_events = db.get_all_events()

        if not all_events:
            st.info("এখনও কোনো ইভেন্ট যোগ করা হয়নি।")
            return

        # Display events in a list with delete buttons
        for event in all_events:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"- **{event['name']}** (যোগ করা হয়েছে: {event['created_at'].strftime('%Y-%m-%d')})")
            
            with col2:
                # Use a unique key for each delete button
                if st.button("🗑️ মুছুন", key=f"delete_{event['id']}", type="secondary"):
                    try:
                        db.delete_event(event['id'])
                        st.success(f"🗑️ ইভেন্ট '{event['name']}' মুছে ফেলা হয়েছে।")
                        st.rerun() # Rerun to update the list
                    except Exception as e:
                        logger.error(f"Error deleting event {event['id']}: {e}")
                        st.error("ইভেন্টটি মুছতে সমস্যা হয়েছে।")

    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        st.error("ইভেন্ট তালিকা আনতে একটি সমস্যা হয়েছে।")


if __name__ == "__main__":
    events_page()
