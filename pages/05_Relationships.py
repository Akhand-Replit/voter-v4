import streamlit as st
import pandas as pd
from utils.database import Database
from utils.styling import apply_custom_styling
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)
apply_custom_styling()

def get_record_location(db, record):
    """Get batch and file information for a record."""
    try:
        # Batch name is already in the record dictionary as 'batch_name'
        batch_name = record.get('batch_name', 'Unknown Batch')
        
        # File name is also in the record dictionary
        file_name = record.get('file_name', '')

        # Construct location string
        if file_name:
            return f"{batch_name} / {file_name}"
        return batch_name

    except Exception as e:
        logger.error(f"Error getting record location: {e}")
        return "Unknown Location"

def display_relationship_card(record, db):
    """Display a single relationship card with profile image and details"""
    with st.container(border=True):
        # Profile section with image and basic info
        cols = st.columns([1, 3])

        with cols[0]:
            # Profile image - Add robust handling for photo_link
            photo_link = record.get('photo_link')
            if photo_link and photo_link.strip():
                # Use a try-except block to catch potential issues with st.image
                try:
                    st.image(photo_link, width=100)
                except Exception as e:
                    logger.warning(f"Could not load image from {photo_link}: {e}. Displaying placeholder.")
                    st.image("https://placehold.co/100x100/EEE/31343C?text=No+Image", width=100)
            else:
                st.image("https://placehold.co/100x100/EEE/31343C?text=No+Image", width=100)


        with cols[1]:
            st.markdown(f"### {record['নাম']}")
            st.markdown(f"**ক্রমিক নং:** {record['ক্রমিক_নং']}")

        # Location info with both batch name and file name
        st.markdown(f"📍 **স্থান:** {get_record_location(db, record)}")

        st.markdown("---")

        # Main details in two columns for better organization
        col3, col4 = st.columns(2)
        with col3:
            st.markdown(f"**ভোটার নং:** {record['ভোটার_নং']}")
            st.markdown(f"**পিতার নাম:** {record['পিতার_নাম']}")
            st.markdown(f"**মাতার নাম:** {record['মাতার_নাম']}")
            st.markdown(f"**পেশা:** {record['পেশা']}")
            st.markdown(f"**Occupation Details:** {record.get('occupation_details', 'N/A')}")
        with col4:
            st.markdown(f"**জন্ম তারিখ:** {record.get('জন্ম_তারিখ', 'N/A')}")
            st.markdown(f"**ঠিকানা:** {record['ঠিকানা']}")
            st.markdown(f"**লিঙ্গ:** {record.get('gender', 'N/A')}") # Display gender
            st.markdown(f"**বয়স:** {record.get('age', 'N/A')}") # Display age
            st.markdown(f"**Political Status:** {record.get('political_status', 'N/A')}")

        # Additional contact information
        st.markdown(f"**ফোন নাম্বার:** {record.get('phone_number', 'N/A')}")
        if record.get('whatsapp_number'):
            st.markdown(f"**Whatsapp:** [Link]({record.get('whatsapp_number')})")
        if record.get('facebook_link'):
            st.markdown(f"**ফেসবুক:** [Link]({record.get('facebook_link')})")
        if record.get('tiktok_link'):
            st.markdown(f"**Tiktok:** [Link]({record.get('tiktok_link')})")
        if record.get('youtube_link'):
            st.markdown(f"**Youtube:** [Link]({record.get('youtube_link')})")
        if record.get('insta_link'):
            st.markdown(f"**Instagram:** [Link]({record.get('insta_link')})")


        # Description
        st.markdown(f"**বিবরণ:** {record.get('description', 'N/A')}")
        
        # Assigned Events
        events_list = record.get('events', [])
        if events_list:
            st.markdown(f"**নির্ধারিত ইভেন্টস:** {', '.join(events_list)}")
        else:
            st.markdown(f"**নির্ধারিত ইভেন্টস:** N/A")


        # Relationship status
        st.markdown(f"**সম্পর্কের ধরণ:** {record['relationship_status']}")

        # Add action button below the card
        if st.button(
            "🔄 Regular এ ফিরিয়ে নিন", 
            key=f"remove_{record['id']}", 
            type="secondary",
            use_container_width=True
        ):
            db.update_relationship_status(record['id'], 'Regular')
            st.success("✅ Regular হিসেবে আপডেট করা হয়েছে!")
            st.rerun()

def relationships_page():
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.warning("অনুগ্রহ করে প্রথমে লগইন করুন")
        return

    st.title("👥 বন্ধু এবং শত্রু তালিকা")

    db = Database()

    # Get all batches
    batches = db.get_all_batches()

    if not batches:
        st.info("কোন ডাটা পাওয়া যায়নি")
        return

    # Batch selection
    selected_batch = st.selectbox(
        "ব্যাচ নির্বাচন করুন",
        options=['সব ব্যাচ'] + [batch['name'] for batch in batches],
        format_func=lambda x: f"ব্যাচ: {x}"
    )

    # Create tabs for Friend, Enemy and Connected lists
    tab1, tab2, tab3 = st.tabs(["🤝 বন্ধু তালিকা", "⚔️ শত্রু তালিকা", "🔗 সংযুক্ত তালিকা"])

    def display_relationship_section(relationship_type):
        # Get records based on selection
        if selected_batch == 'সব ব্যাচ':
            records = db.get_relationship_records(relationship_type)
        else:
            batch_id = next(batch['id'] for batch in batches if batch['name'] == selected_batch)
            # Filter records in Python after fetching all of them
            all_relationship_records = db.get_relationship_records(relationship_type)
            records = [r for r in all_relationship_records if r['batch_id'] == batch_id]

        if not records:
            st.info(f"এই ক্যাটাগরিতে কোনো রেকর্ড যোগ করা হয়নি।")
            return

        # Show total count
        st.write(f"মোট: {len(records)}")

        # Display each record in a card format
        for record in records:
            display_relationship_card(record, db)

    with tab1:
        display_relationship_section('Friend')

    with tab2:
        display_relationship_section('Enemy')

    with tab3:
        display_relationship_section('Connected')

if __name__ == "__main__":
    relationships_page()
