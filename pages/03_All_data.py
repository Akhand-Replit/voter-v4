import streamlit as st
import pandas as pd
import numpy as np
from utils.database import Database
from utils.styling import apply_custom_styling
import logging

logger = logging.getLogger(__name__)
apply_custom_styling()

def all_data_page():
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.warning("অনুগ্রহ করে প্রথমে লগইন করুন")
        return

    st.title("📁 সব তথ্য")

    db = Database()
    batches = db.get_all_batches()

    if not batches:
        st.info("কোন ডাটা পাওয়া যায়নি")
        
        # Option to clear entire database even if no batches exist
        st.markdown("---")
        st.subheader("ডেটাবেস ম্যানেজমেন্ট")
        if st.button("🔴 সম্পূর্ণ ডাটাবেস মুছে ফেলুন (সাবধান!)", type="secondary", use_container_width=True):
            if st.session_state.get('confirm_clear_db', False):
                try:
                    # Delete all records first (which will also delete record_events due to CASCADE)
                    with db.conn.cursor() as cur:
                        cur.execute("DELETE FROM records")
                        cur.execute("DELETE FROM batches")
                        cur.execute("DELETE FROM events")
                    db.conn.commit()
                    st.success("✅ সম্পূর্ণ ডাটাবেস সফলভাবে মুছে ফেলা হয়েছে!")
                    st.session_state.pop('confirm_clear_db', None) # Reset confirmation
                    st.rerun()
                except Exception as e:
                    logger.error(f"Error clearing database: {str(e)}")
                    st.error(f"ডাটাবেস মুছে ফেলার সময় সমস্যা হয়েছে: {str(e)}")
            else:
                st.warning("আপনি কি নিশ্চিত যে আপনি সম্পূর্ণ ডাটাবেস মুছে ফেলতে চান? এই ক্রিয়াটি অপরিবর্তনীয়।")
                st.session_state.confirm_clear_db = True
                st.button("হ্যাঁ, আমি নিশ্চিত (সম্পূর্ণ মুছে ফেলুন)", type="danger", key="confirm_clear_db_btn")
        
        return

    # --- Batch and File Selection ---
    selected_batch_name = st.selectbox(
        "ব্যাচ নির্বাচন করুন",
        options=[batch['name'] for batch in batches],
        format_func=lambda x: f"ব্যাচ: {x}",
        key="batch_selector" # Added a unique key for the selectbox
    )
    
    selected_batch_id = next(b['id'] for b in batches if b['name'] == selected_batch_name)
    files = db.get_batch_files(selected_batch_id)

    if not files:
        st.info("এই ব্যাচে কোন ফাইল নেই")
        # Allow creating a dummy file for new records if batch is empty
        if st.button("এই ব্যাচে নতুন রেকর্ড যোগ করার জন্য ফাইল তৈরি করুন"):
            db.add_record(selected_batch_id, "initial_records.txt", {'নাম': 'dummy'})
            db.commit_changes() # Commit the dummy record insertion
            st.rerun()
        
        # Add delete batch option even if no files in batch
        st.markdown("---")
        st.subheader("ব্যাচ ম্যানেজমেন্ট")
        if st.button(f"🗑️ '{selected_batch_name}' ব্যাচ মুছে ফেলুন", type="secondary", use_container_width=True):
            if st.session_state.get(f'confirm_delete_batch_{selected_batch_id}', False):
                try:
                    db.delete_batch(selected_batch_id)
                    st.success(f"✅ ব্যাচ '{selected_batch_name}' সফলভাবে মুছে ফেলা হয়েছে!")
                    st.session_state.pop(f'confirm_delete_batch_{selected_batch_id}', None) # Reset confirmation
                    st.rerun()
                except Exception as e:
                    logger.error(f"Error deleting batch {selected_batch_id}: {str(e)}")
                    st.error(f"ব্যাচ মুছে ফেলার সময় সমস্যা হয়েছে: {str(e)}")
            else:
                st.warning(f"আপনি কি নিশ্চিত যে আপনি '{selected_batch_name}' ব্যাচটি মুছে ফেলতে চান? এই ব্যাচের সমস্ত রেকর্ড মুছে যাবে।")
                st.session_state[f'confirm_delete_batch_{selected_batch_id}'] = True
                st.button("হ্যাঁ, আমি নিশ্চিত (ব্যাচ মুছে ফেলুন)", type="danger", key=f"confirm_delete_batch_btn_{selected_batch_id}")

        # Option to clear entire database if there are batches but no files in selected one
        st.markdown("---")
        st.subheader("সম্পূর্ণ ডাটাবেস ম্যানেজমেন্ট")
        if st.button("🔴 সম্পূর্ণ ডাটাবেস মুছে ফেলুন (সাবধান!)", type="secondary", use_container_width=True):
            if st.session_state.get('confirm_clear_db', False):
                try:
                    # Delete all records first (which will also delete record_events due to CASCADE)
                    with db.conn.cursor() as cur:
                        cur.execute("DELETE FROM records")
                        cur.execute("DELETE FROM batches")
                        cur.execute("DELETE FROM events")
                    db.conn.commit()
                    st.success("✅ সম্পূর্ণ ডাটাবেস সফলভাবে মুছে ফেলা হয়েছে!")
                    st.session_state.pop('confirm_clear_db', None) # Reset confirmation
                    st.rerun()
                except Exception as e:
                    logger.error(f"Error clearing database: {str(e)}")
                    st.error(f"ডাটাবেস মুছে ফেলার সময় সমস্যা হয়েছে: {str(e)}")
            else:
                st.warning("আপনি কি নিশ্চিত যে আপনি সম্পূর্ণ ডাটাবেস মুছে ফেলতে চান? এই ক্রিয়াটি অপরিবর্তনীয়।")
                st.session_state.confirm_clear_db = True
                st.button("হ্যাঁ, আমি নিশ্চিত (সম্পূর্ণ মুছে ফেলুন)", type="danger", key="confirm_clear_db_btn")

        return
        
    selected_file_name = st.selectbox(
        "ফাইল নির্বাচন করুন",
        options=['সব'] + [file['file_name'] for file in files],
        format_func=lambda x: f"ফাইল: {x}" if x != 'সব' else "সব ফাইল দেখুন",
        key="file_selector" # Added a unique key for the selectbox
    )

    # --- Data Display and Editing ---
    if selected_file_name == 'সব':
        records = db.get_batch_records(selected_batch_id)
    else:
        records = db.get_file_records(selected_batch_id, selected_file_name)

    if records:
        df = pd.DataFrame(records)
        st.write(f"মোট রেকর্ড: {len(records)}")

        # IMPORTANT: Update original_df in session state whenever records are loaded or filtered
        # This ensures that the comparison in st.data_editor is always against the currently displayed data
        st.session_state.original_df = df.copy()

        edited_df = st.data_editor(
            df,
            column_config={
                'id': None, 'batch_id': None, 'file_name': None, 'created_at': None, 'batch_name': None,
                'ক্রমিক_নং': st.column_config.TextColumn('ক্রমিক নং', width="small"),
                'নাম': st.column_config.TextColumn('নাম', width="medium"),
                'ভোটার_নং': st.column_config.TextColumn('ভোটার নং', width="medium"),
                'পিতার_নাম': st.column_config.TextColumn('পিতার নাম', width="medium"),
                'মাতার_নাম': st.column_config.TextColumn('মাতার নাম', width="medium"),
                'পেশা': st.column_config.TextColumn('পেশা'),
                'occupation_details': st.column_config.TextColumn('Occupation Details', width="large"),
                'ঠিকানা': st.column_config.TextColumn('ঠিকানা', width="large"),
                'জন্ম_তারিখ': st.column_config.TextColumn('জন্ম তারিখ'),
                'phone_number': st.column_config.TextColumn('ফোন নম্বর'),
                'whatsapp_number': st.column_config.LinkColumn('Whatsapp Number'),
                'facebook_link': st.column_config.LinkColumn('ফেসবুক লিঙ্ক'),
                'tiktok_link': st.column_config.LinkColumn('Tiktok Link'),
                'youtube_link': st.column_config.LinkColumn('Youtube Link'),
                'insta_link': st.column_config.LinkColumn('Insta Link'),
                'photo_link': st.column_config.ImageColumn('ছবি', help="ছবির লিঙ্ক দিন"),
                'description': st.column_config.TextColumn('বিবরণ'),
                'political_status': st.column_config.TextColumn('Political Status'),
                'relationship_status': st.column_config.SelectboxColumn(
                    'সম্পর্কের ধরণ', options=['Regular', 'Friend', 'Enemy', 'Connected'], required=True
                ),
                'gender': st.column_config.SelectboxColumn( # Added gender column config
                    'লিঙ্গ', options=['Male', 'Female', 'Other', ''], required=False # Allow empty string for not specified
                ),
                'events': st.column_config.ListColumn('নির্ধারিত ইভেন্টস', help="এই রেকর্ডের জন্য নির্ধারিত ইভেন্ট (s)", width="medium")
            },
            hide_index=True,
            use_container_width=True,
            key="data_editor"
        )

        # --- Action Buttons ---
        col1, col2, col3 = st.columns([2, 2, 5])

        with col1:
            if st.button("💾 পরিবর্তন সংরক্ষণ", type="primary", use_container_width=True):
                try:
                    # Retrieve the original_df from session state
                    original_df = st.session_state.original_df
                    
                    # Ensure both DataFrames have the same index before comparing
                    # This step is crucial if the index somehow got misaligned
                    original_df = original_df.set_index('id', drop=False)
                    edited_df = edited_df.set_index('id', drop=False)

                    # Identify editable columns
                    editable_cols = [
                        'ক্রমিক_নং', 'নাম', 'ভোটার_নং', 'পিতার_নাম', 'মাতার_নাম', 'পেশা', 
                        'occupation_details', 'ঠিকানা', 'জন্ম_তারিখ', 'phone_number', 
                        'whatsapp_number', 'facebook_link', 'tiktok_link', 'youtube_link', 'insta_link',
                        'photo_link', 'description', 'political_status', 'relationship_status', 'gender' 
                    ]
                    
                    # Compare only the editable columns
                    # Use .align to ensure identical labels for comparison
                    original_subset, edited_subset = original_df[editable_cols].align(edited_df[editable_cols], join='inner', axis=None)
                    changes = edited_subset.compare(original_subset)
                    
                    if not changes.empty:
                        updated_count = 0
                        for idx in changes.index:
                            record_id = int(original_df.loc[idx, 'id']) # Use original_df for record_id
                            updated_data = edited_df.loc[idx].to_dict()
                            db.update_record(record_id, updated_data)
                            updated_count += 1
                        st.success(f"{updated_count} টি রেকর্ডের পরিবর্তন সফলভাবে সংরক্ষিত হয়েছে!")
                        # After saving, re-fetch data or update original_df to reflect saved changes
                        st.session_state.original_df = edited_df.copy() # Update session state with the new state
                        st.rerun() # Rerun to refresh the data editor with the latest saved data
                    else:
                        st.info("কোনো পরিবর্তন সনাক্ত করা যায়নি।")
                except Exception as e:
                    logger.error(f"Update error: {str(e)}")
                    st.error(f"পরিবর্তন সংরক্ষণে সমস্যা হয়েছে: {str(e)}")
        
        with col2:
            popover = st.popover("🗓️ ইভেন্ট নির্ধারণ করুন", use_container_width=True)
            with popover:
                st.markdown("##### একটি রেকর্ডে এক বা একাধিক ইভেন্ট নির্ধারণ করুন")
                all_events = db.get_all_events()
                event_map = {event['name']: event['id'] for event in all_events}
                
                record_options = {f"{rec['ক্রমিক_নং']}: {rec['নাম']}": rec['id'] for rec in records}
                selected_record_display = st.selectbox(
                    "রেকর্ড নির্বাচন করুন",
                    options=record_options.keys(),
                    key="event_record_selector"
                )

                if selected_record_display:
                    selected_record_id = record_options[selected_record_display]
                    assigned_events_names = db.get_events_for_record(selected_record_id)

                    selected_events = st.multiselect(
                        "নির্ধারণ করার জন্য ইভেন্ট নির্বাচন করুন",
                        options=event_map.keys(),
                        default=assigned_events_names,
                        key="event_multiselect"
                    )

                    if st.button("✅ ইভেন্ট আপডেট করুন", type="primary"):
                        try:
                            selected_event_ids = [event_map[name] for name in selected_events]
                            db.assign_events_to_record(selected_record_id, selected_event_ids)
                            st.success(f"রেকর্ড '{selected_record_display}' এর জন্য ইভেন্ট সফলভাবে আপডেট করা হয়েছে।")
                            st.rerun()
                        except Exception as e:
                            logger.error(f"Event assignment error: {e}")
                            st.error("ইভেন্ট নির্ধারণের সময় একটি সমস্যা হয়েছে।")

    else:
        st.info("এই ফাইল বা ব্যাচে কোন রেকর্ড পাওয়া যায়নি।")

    st.markdown("---")
    st.subheader("ডেটাবেস ম্যানেজমেন্ট")

    # Delete specific batch button
    if selected_batch_name and selected_batch_name != 'সব ব্যাচ':
        if st.button(f"🗑️ '{selected_batch_name}' ব্যাচ মুছে ফেলুন", type="secondary", use_container_width=True):
            if st.session_state.get(f'confirm_delete_batch_{selected_batch_id}', False):
                try:
                    db.delete_batch(selected_batch_id)
                    st.success(f"✅ ব্যাচ '{selected_batch_name}' সফলভাবে মুছে ফেলা হয়েছে!")
                    st.session_state.pop(f'confirm_delete_batch_{selected_batch_id}', None) # Reset confirmation
                    st.rerun()
                except Exception as e:
                    logger.error(f"Error deleting batch {selected_batch_id}: {str(e)}")
                    st.error(f"ব্যাচ মুছে ফেলার সময় সমস্যা হয়েছে: {str(e)}")
            else:
                st.warning(f"আপনি কি নিশ্চিত যে আপনি '{selected_batch_name}' ব্যাচটি মুছে ফেলতে চান? এই ব্যাচের সমস্ত রেকর্ড মুছে যাবে।")
                st.session_state[f'confirm_delete_batch_{selected_batch_id}'] = True
                st.button("হ্যাঁ, আমি নিশ্চিত (ব্যাচ মুছে ফেলুন)", type="danger", key=f"confirm_delete_batch_btn_{selected_batch_id}")
    else:
        st.info("একটি নির্দিষ্ট ব্যাচ মুছে ফেলার জন্য, অনুগ্রহ করে উপরে একটি ব্যাচ নির্বাচন করুন।")


    # Clear entire database button
    if st.button("🔴 সম্পূর্ণ ডাটাবেস মুছে ফেলুন (সাবধান!)", type="secondary", use_container_width=True):
        if st.session_state.get('confirm_clear_db', False):
            try:
                # Delete all records first (which will also delete record_events due to CASCADE)
                with db.conn.cursor() as cur:
                    cur.execute("DELETE FROM records")
                    cur.execute("DELETE FROM batches")
                    cur.execute("DELETE FROM events")
                db.conn.commit()
                st.success("✅ সম্পূর্ণ ডাটাবেস সফলভাবে মুছে ফেলা হয়েছে!")
                st.session_state.pop('confirm_clear_db', None) # Reset confirmation
                st.rerun()
            except Exception as e:
                logger.error(f"Error clearing database: {str(e)}")
                st.error(f"ডাটাবেস মুছে ফেলার সময় সমস্যা হয়েছে: {str(e)}")
        else:
            st.warning("আপনি কি নিশ্চিত যে আপনি সম্পূর্ণ ডাটাবেস মুছে ফেলতে চান? এই ক্রিয়াটি অপরিবর্তনীয়।")
            st.session_state.confirm_clear_db = True
            st.button("হ্যাঁ, আমি নিশ্চিত (সম্পূর্ণ মুছে ফেলুন)", type="danger", key="confirm_clear_db_btn")


if __name__ == "__main__":
    all_data_page()
