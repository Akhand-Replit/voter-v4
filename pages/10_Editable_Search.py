import streamlit as st
import pandas as pd
from utils.database import Database
from utils.styling import apply_custom_styling
import logging
from attached_assets.data_processor import calculate_age # Import calculate_age

logger = logging.getLogger(__name__)
apply_custom_styling()

def editable_search_page():
    """
    A search page where the results are displayed in editable cards,
    allowing direct modification of record data and event assignments.
    """
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.warning("অনুগ্রহ করে প্রথমে লগইন করুন")
        return

    st.title("✏️ তথ্য খুঁজুন এবং সম্পাদনা করুন")
    st.markdown("এখানে আপনি তথ্য অনুসন্ধান করতে এবং সরাসরি ফলাফল সম্পাদনা করতে পারেন।")

    db = Database()

    # --- Search UI ---
    with st.container(border=True):
        st.subheader("অনুসন্ধান ফিল্টার")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("নাম")
            fathers_name = st.text_input("পিতার নাম")
            phone_number = st.text_input("ফোন নম্বর")
        with col2:
            voter_no = st.text_input("ভোটার নং")
            address = st.text_input("ঠিকানা")
            si_number = st.text_input("ক্রমিক নং")
            gender_filter = st.selectbox("লিঙ্গ", options=['সব', 'Male', 'Female', 'Other']) # Gender search filter

    if st.button("🔍 অনুসন্ধান করুন", type="primary", use_container_width=True):
        search_criteria = {
            'নাম': name,
            'পিতার_নাম': fathers_name,
            'phone_number': phone_number,
            'ভোটার_নং': voter_no,
            'ঠিকানা': address,
            'ক্রমিক_নং': si_number,
            'gender': gender_filter # Include gender in search criteria
        }
        # Remove empty criteria to search only with provided values, but keep 'gender' if 'সব' is selected
        search_criteria = {k: v for k, v in search_criteria.items() if v or (k == 'gender' and v == 'সব')}

        if not search_criteria or (len(search_criteria) == 1 and 'gender' in search_criteria and search_criteria['gender'] == 'সব'):
            st.warning("অনুসন্ধানের জন্য অন্তত একটি ফিল্টার পূরণ করুন।")
            return

        try:
            with st.spinner("অনুসন্ধান করা হচ্ছে..."):
                results = db.search_records_advanced(search_criteria)
            
            st.session_state.search_results = results
            if not results:
                st.info("আপনার অনুসন্ধানের সাথে মেলে এমন কোনো ফলাফল পাওয়া যায়নি।")

        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            st.error(f"অনুসন্ধানে সমস্যা হয়েছে: {str(e)}")

    # --- Display Search Results ---
    if 'search_results' in st.session_state and st.session_state.search_results:
        st.markdown("---")
        st.subheader(f"অনুসন্ধানের ফলাফল ({len(st.session_state.search_results)} টি)")

        all_events = db.get_all_events()
        event_map = {event['name']: event['id'] for event in all_events}

        for record in st.session_state.search_results:
            with st.expander(f"**{record['নাম']}** (ক্রমিক নং: {record['ক্রমিক_নং']})"):
                
                # Create a unique key for each form to isolate its state
                form_key = f"form_{record['id']}"
                with st.form(key=form_key):
                    st.markdown(f"#### রেকর্ড আইডি: {record['id']}")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        # Editable fields
                        edited_name = st.text_input("নাম", value=record.get('নাম', ''), key=f"name_{record['id']}")
                        edited_father = st.text_input("পিতার নাম", value=record.get('পিতার_নাম', ''), key=f"father_{record['id']}")
                        edited_mother = st.text_input("মাতার নাম", value=record.get('মাতার_নাম', ''), key=f"mother_{record['id']}")
                        edited_voter_no = st.text_input("ভোটার নং", value=record.get('ভোটার_নং', ''), key=f"voter_{record['id']}")
                        
                        phone_val = record.get('phone_number') or ''
                        edited_phone = st.text_input("ফোন নম্বর", value=phone_val.replace('tel:', ''), key=f"phone_{record['id']}")
                        
                        whatsapp_val = record.get('whatsapp_number') or ''
                        edited_whatsapp = st.text_input("Whatsapp Number", value=whatsapp_val.replace('https://wa.me/', ''), key=f"whatsapp_{record['id']}")
                        
                        edited_fb = st.text_input("ফেসবুক লিঙ্ক", value=record.get('facebook_link', ''), key=f"fb_{record['id']}")
                        edited_tiktok = st.text_input("Tiktok Link", value=record.get('tiktok_link', ''), key=f"tiktok_{record['id']}")


                    with c2:
                        edited_si = st.text_input("ক্রমিক নং", value=record.get('ক্রমিক_নং', ''), key=f"si_{record['id']}")
                        edited_occupation = st.text_input("পেশা", value=record.get('পেশা', ''), key=f"occupation_{record['id']}")
                        edited_occupation_details = st.text_area("Occupation Details", value=record.get('occupation_details', ''), key=f"occupation_details_{record['id']}")
                        edited_dob = st.text_input("জন্ম তারিখ", value=record.get('জন্ম_তারিখ', ''), key=f"dob_{record['id']}")
                        edited_address = st.text_area("ঠিকানা", value=record.get('ঠিকানা', ''), key=f"address_{record['id']}")
                        edited_photo = st.text_input("ছবির লিঙ্ক", value=record.get('photo_link', ''), key=f"photo_{record['id']}")
                        edited_youtube = st.text_input("Youtube Link", value=record.get('youtube_link', ''), key=f"youtube_{record['id']}")
                        edited_insta = st.text_input("Insta Link", value=record.get('insta_link', ''), key=f"insta_{record['id']}")
                    
                    # Age display (not editable directly)
                    st.markdown(f"**বয়স:** {record.get('age', 'N/A')}")

                    # Gender selection in editable form
                    current_gender = record.get('gender', '')
                    gender_options = ['Male', 'Female', 'Other', '']
                    if current_gender not in gender_options:
                        gender_options.append(current_gender) # Add current value if it's not in default options
                    
                    edited_gender = st.selectbox(
                        "লিঙ্গ",
                        options=gender_options,
                        index=gender_options.index(current_gender),
                        key=f"gender_{record['id']}"
                    )
                    
                    edited_political_status = st.text_input("Political Status", value=record.get('political_status', ''), key=f"political_status_{record['id']}")
                    edited_description = st.text_area("বিবরণ", value=record.get('description', ''), key=f"desc_{record['id']}")
                    
                    st.markdown("---")
                    
                    # Relationship and Event assignment
                    rel_col, event_col = st.columns(2)
                    with rel_col:
                        edited_relationship = st.selectbox(
                            "সম্পর্কের ধরণ",
                            options=['Regular', 'Friend', 'Enemy', 'Connected'],
                            index=['Regular', 'Friend', 'Enemy', 'Connected'].index(record.get('relationship_status', 'Regular')),
                            key=f"rel_{record['id']}"
                        )
                    with event_col:
                        assigned_events = db.get_events_for_record(record['id'])
                        selected_events = st.multiselect(
                            "ইভেন্ট নির্ধারণ করুন",
                            options=event_map.keys(),
                            default=assigned_events,
                            key=f"events_{record['id']}"
                        )

                    # Submit button for the form
                    if st.form_submit_button("💾 পরিবর্তন সংরক্ষণ করুন", type="primary"):
                        try:
                            # 1. Update Record Details
                            updated_data = {
                                'ক্রমিক_নং': edited_si, 'নাম': edited_name, 'ভোটার_নং': edited_voter_no,
                                'পিতার_নাম': edited_father, 'মাতার_নাম': edited_mother, 'পেশা': edited_occupation,
                                'occupation_details': edited_occupation_details,
                                'ঠিকানা': edited_address, 'জন্ম_তারিখ': edited_dob, 'phone_number': edited_phone,
                                'whatsapp_number': edited_whatsapp,
                                'facebook_link': edited_fb, 'tiktok_link': edited_tiktok, 'youtube_link': edited_youtube, 'insta_link': edited_insta,
                                'photo_link': edited_photo, 'description': edited_description,
                                'political_status': edited_political_status,
                                'relationship_status': edited_relationship,
                                'gender': edited_gender # Include gender in updated data
                            }
                            
                            # Recalculate age if 'জন্ম_তারিখ' was changed
                            calculated_age = calculate_age(edited_dob)
                            updated_data['age'] = calculated_age

                            db.update_record(record['id'], updated_data)

                            # 2. Update Event Assignments
                            selected_event_ids = [event_map[name] for name in selected_events]
                            db.assign_events_to_record(record['id'], selected_event_ids)

                            st.success(f"রেকর্ড '{record['নাম']}' সফলভাবে আপডেট করা হয়েছে।")
                            # Clear results to allow a new search
                            st.session_state.search_results = []
                            st.rerun()

                        except Exception as e:
                            logger.error(f"Update failed for record {record['id']}: {e}")
                            st.error("তথ্য আপডেট করার সময় একটি সমস্যা হয়েছে।")

if __name__ == "__main__":
    editable_search_page()
