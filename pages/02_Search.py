import streamlit as st
import pandas as pd
from utils.database import Database
from utils.styling import apply_custom_styling
import logging

logger = logging.getLogger(__name__)
apply_custom_styling()

def display_result_card(result, db):
    """
    Displays a single search result in a well-formatted card.
    Uses st.container with a border for a clean, modern look.
    """
    # Use a container with a border for each card
    with st.container(border=True):
        # Header with name and serial number
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### {result.get('নাম', 'N/A')}")
        with col2:
            st.markdown(f"**ক্রমিক নং:** {result.get('ক্রমিক_নং', 'N/A')}")

        # Location info (Batch and File)
        batch_info = db.get_batch_by_id(result['batch_id'])
        location_str = batch_info['name'] if batch_info else "Unknown Batch"
        if result.get('file_name'):
            location_str += f" / {result['file_name']}"
        st.markdown(f"📍 **স্থান:** {location_str}")

        st.markdown("---")

        # Main details in two columns for better organization
        col3, col4 = st.columns(2)
        with col3:
            st.markdown(f"**ভোটার নং:** {result.get('ভোটার_নং', 'N/A')}")
            st.markdown(f"**পিতার নাম:** {result.get('পিতার_নাম', 'N/A')}")
            st.markdown(f"**মাতার নাম:** {result.get('মাতার_নাম', 'N/A')}")
            st.markdown(f"**পেশা:** {result.get('পেশা', 'N/A')}")
            st.markdown(f"**Occupation Details:** {result.get('occupation_details', 'N/A')}")
        with col4:
            st.markdown(f"**জন্ম তারিখ:** {result.get('জন্ম_তারিখ', 'N/A')}")
            st.markdown(f"**ঠিকানা:** {result.get('ঠিকানা', 'N/A')}")
            st.markdown(f"**লিঙ্গ:** {result.get('gender', 'N/A')}") # Display gender
            st.markdown(f"**বয়স:** {result.get('age', 'N/A')}") # Display age
            st.markdown(f"**Political Status:** {result.get('political_status', 'N/A')}")

        st.markdown("---")

        # Contact and social media
        st.markdown(f"**ফোন নাম্বার:** {result.get('phone_number', 'N/A')}")
        if result.get('whatsapp_number'):
            st.markdown(f"**Whatsapp:** [Link]({result.get('whatsapp_number')})")
        if result.get('facebook_link'):
            st.markdown(f"**ফেসবুক:** [Link]({result.get('facebook_link')})")
        if result.get('tiktok_link'):
            st.markdown(f"**Tiktok:** [Link]({result.get('tiktok_link')})")
        if result.get('youtube_link'):
            st.markdown(f"**Youtube:** [Link]({result.get('youtube_link')})")
        if result.get('insta_link'):
            st.markdown(f"**Instagram:** [Link]({result.get('insta_link')})")

        # Display assigned events
        events_list = result.get('events', [])
        if events_list:
            st.markdown(f"**নির্ধারিত ইভেন্টস:** {', '.join(events_list)}")
        else:
            st.markdown("**নির্ধারিত ইভেন্টস:** N/A")

        # Display relationship status
        st.markdown(f"**সম্পর্কের ধরণ:** {result.get('relationship_status', 'N/A')}")


def search_page():
    """
    The main function for the search page.
    Provides input fields for searching and displays results.
    """
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.warning("অনুগ্রহ করে প্রথমে লগইন করুন")
        return

    st.title("🔍 তথ্য খুঁজুন")

    db = Database()

    # Search fields within a container for better layout
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            si_number = st.text_input("ক্রমিক নং")
            name = st.text_input("নাম")
            mothers_name = st.text_input("মাতার নাম")
            date_of_birth = st.text_input("জন্ম তারিখ")
        with col2:
            voter_no = st.text_input("ভোটার নং")
            fathers_name = st.text_input("পিতার নাম")
            occupation = st.text_input("পেশা")
            address = st.text_input("ঠিকানা")
            gender = st.selectbox("লিঙ্গ", options=['সব', 'Male', 'Female', 'Other']) # Gender search filter
            
    # Search button
    if st.button("অনুসন্ধান করুন", type="primary", use_container_width=True):
        try:
            with st.spinner("অনুসন্ধান করা হচ্ছে..."):
                search_criteria = {
                    'ক্রমিক_নং': si_number,
                    'ভোটার_নং': voter_no,
                    'নাম': name,
                    'পিতার_নাম': fathers_name,
                    'মাতার_নাম': mothers_name,
                    'পেশা': occupation,
                    'ঠিকানা': address,
                    'জন্ম_তারিখ': date_of_birth,
                    'gender': gender # Include gender in search criteria
                }
                # Remove empty criteria to avoid searching on empty strings, but keep 'gender' if 'সব' is selected
                search_criteria = {k: v for k, v in search_criteria.items() if v or k == 'gender'}
                
                if not search_criteria or (len(search_criteria) == 1 and 'gender' in search_criteria and search_criteria['gender'] == 'সব'):
                    st.warning("অনুসন্ধানের জন্য অন্তত একটি ফিল্টার পূরণ করুন।")
                    return

                results = db.search_records_advanced(search_criteria)

                if results:
                    st.success(f"{len(results)}টি ফলাফল পাওয়া গেছে")
                    # Display results in the improved card format
                    for result in results:
                        display_result_card(result, db)
                else:
                    st.info("আপনার অনুসন্ধানের সাথে মেলে এমন কোনো ফলাফল পাওয়া যায়নি।")

        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            st.error(f"অনুসন্ধানে সমস্যা হয়েছে: {str(e)}")

if __name__ == "__main__":
    search_page()
