import streamlit as st
from utils.database import Database
from utils.styling import apply_custom_styling
from datetime import datetime

# Initialize database connection
db = Database()

# Set page style
apply_custom_styling()

st.title("পরিবার বৃক্ষ ব্যবস্থাপনা 🌳")
st.markdown("আপনার ভোটার ডেটাবেসের মধ্যে পারিবারিক সম্পর্ক তৈরি এবং পরিচালনা করুন।")

# --- Session State Initialization ---
if 'selected_main_voter_id' not in st.session_state:
    st.session_state.selected_main_voter_id = None
if 'family_search_query' not in st.session_state:
    st.session_state.family_search_query = ""
if 'new_family_member_data' not in st.session_state:
    st.session_state.new_family_member_data = {
        "নাম": "", "পিতার_নাম": "", "মাতার_নাম": "", "ভোটার_নং": "",
        "gender": "", "জন্ম_তারিখ": ""
    }
if 'relationship_type' not in st.session_state:
    st.session_state.relationship_type = "পিতা" # Default relationship

# Helper function to get bidirectional relationships
def get_bidirectional_relationships(relationship_type, source_gender=None, target_gender=None):
    """
    Returns the relationship types for both directions based on the user's input.
    The source is the main voter, target is the family member being added.
    """
    relationships = {
        "পিতা": {"source_to_target": "পিতা", "target_to_source": "সন্তান"},
        "মাতা": {"source_to_target": "মাতা", "target_to_source": "সন্তান"},
        "স্বামী": {"source_to_target": "স্বামী", "target_to_source": "স্ত্রী"},
        "স্ত্রী": {"source_to_target": "স্ত্রী", "target_to_source": "স্বামী"},
        "ছেলে": {"source_to_target": "ছেলে", "target_to_source": "পিতা"},
        "মেয়ে": {"source_to_target": "মেয়ে", "target_to_source": "মাতা"},
        "ভাই": {"source_to_target": "ভাই", "target_to_source": "ভাই/বোন"},
        "বোন": {"source_to_target": "বোন", "target_to_source": "ভাই/বোন"},
        "দাদা": {"source_to_target": "দাদা", "target_to_source": "নাতি/নাতনি"},
        "দাদী": {"source_to_target": "দাদী", "target_to_source": "নাতি/নাতনি"},
        "নাতি": {"source_to_target": "নাতি", "target_to_source": "দাদা/দাদী"},
        "নাতনি": {"source_to_target": "নাতনি", "target_to_source": "দাদা/দাদী"},
        "চাচা": {"source_to_target": "চাচা", "target_to_source": "ভাতিজা/ভাতিজি"},
        "চাচী": {"source_to_target": "চাচী", "target_to_source": "ভাতিজা/ভাতিজি"},
        "ভাতিজা": {"source_to_target": "ভাতিজা", "target_to_source": "চাচা/চাচী"},
        "ভাতিজি": {"source_to_target": "ভাতিজি", "target_to_source": "চাচা/চাচী"},
        "মামা": {"source_to_target": "মামা", "target_to_source": "ভাগ্নে/ভাগ্নি"},
        "মামি": {"source_to_target": "মামি", "target_to_source": "ভাগ্নে/ভাগ্নি"},
        "ভাগ্নে": {"source_to_target": "ভাগ্নে", "target_to_source": "মামা/মামি"},
        "ভাগ্নি": {"source_to_target": "ভাগ্নি", "target_to_source": "মামা/মামি"},
        "শ্বশুর": {"source_to_target": "শ্বশুর", "target_to_source": "জামাই/বউমা"},
        "শাশুড়ি": {"source_to_target": "শাশুড়ি", "target_to_source": "জামাই/বউমা"},
        "জামাই": {"source_to_target": "জামাই", "target_to_source": "শ্বশুর/শাশুড়ি"},
        "বউমা": {"source_to_target": "বউমা", "target_to_source": "শ্বশুর/শাশুড়ি"},
        "শালা": {"source_to_target": "শালা", "target_to_source": "ভগ্নিপতি"},
        "শালী": {"source_to_target": "শালী", "target_to_source": "ভগ্নিপতি"},
        "দেবর": {"source_to_target": "দেবর", "target_to_source": "বউদি"},
        "ননদ": {"source_to_target": "ননদ", "target_to_source": "বউদি"},
        "ভাসুর": {"source_to_target": "ভাসুর", "target_to_source": "বউদি"},
        "বউদি": {"source_to_target": "বউদি", "target_to_source": "দেবর/ভাসুর"},
        "অন্যান্য": {"source_to_target": "অন্যান্য", "target_to_source": "অন্যান্য"}
    }
    return relationships.get(relationship_type, {"source_to_target": relationship_type, "target_to_source": "সম্পর্কিত ব্যক্তি"})


# --- Main Voter Selection ---
st.header("১. প্রধান ভোটার নির্বাচন করুন")
all_voters = db.get_all_voters_for_search()
voter_options = {f"{voter['নাম']} ({voter['ভোটার_নং'] or 'N/A'}) - ID: {voter['id']}" : voter['id'] for voter in all_voters}

selected_option = st.selectbox(
    "ভোটার খুঁজুন এবং নির্বাচন করুন:",
    options=[""] + list(voter_options.keys()),
    index=0,
    format_func=lambda x: x if x else "একটি ভোটার নির্বাচন করুন"
)

if selected_option:
    st.session_state.selected_main_voter_id = voter_options[selected_option]
    main_voter_details = db.get_record_by_id(st.session_state.selected_main_voter_id)
    if main_voter_details:
        st.subheader(f"নির্বাচিত ভোটার: {main_voter_details['নাম']}")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(main_voter_details.get('photo_link', 'https://placehold.co/100x100/EEE/31343C?text=No+Image'), width=100)
        with col2:
            st.write(f"**ভোটার নং:** {main_voter_details['ভোটার_নং']}")
            st.write(f"**পিতা:** {main_voter_details['পিতার_নাম']}")
            st.write(f"**মাতা:** {main_voter_details['মাতার_নাম']}")
            st.write(f"**ঠিকানা:** {main_voter_details['ঠিকানা']}")
            st.write(f"**লিঙ্গ:** {main_voter_details['gender']}")
            st.write(f"**বয়স:** {main_voter_details['age'] if main_voter_details['age'] else 'N/A'}")
    else:
        st.warning("নির্বাচিত ভোটার পাওয়া যায়নি।")
else:
    st.session_state.selected_main_voter_id = None
    st.info("একটি প্রধান ভোটার নির্বাচন করুন পারিবারিক সম্পর্ক যোগ করতে।")

st.markdown("---")

if st.session_state.selected_main_voter_id:
    st.header("২. পারিবারিক সদস্য যোগ করুন")

    tab1, tab2 = st.tabs(["বিদ্যমান সদস্য খুঁজুন", "নতুন সদস্য যোগ করুন"])

    with tab1:
        st.subheader("বিদ্যমান সদস্য খুঁজুন এবং যোগ করুন")
        search_col1, search_col2 = st.columns([3, 1])
        with search_col1:
            st.session_state.family_search_query = st.text_input("নাম বা ভোটার নং দ্বারা খুঁজুন:", value=st.session_state.family_search_query, key="family_search_input")
        with search_col2:
            st.markdown("<br>", unsafe_allow_html=True) # For alignment
            search_button = st.button("অনুসন্ধান করুন", key="search_family_member_button")

        found_members = []
        if search_button and st.session_state.family_search_query:
            search_criteria = {
                "নাম": st.session_state.family_search_query,
                "ভোটার_নং": st.session_state.family_search_query
            }
            # This search will return records matching either name or voter_no
            found_members = db.search_records_advanced(search_criteria)
            # Filter out the main voter themselves
            found_members = [m for m in found_members if m['id'] != st.session_state.selected_main_voter_id]

        if found_members:
            st.write(f"**{len(found_members)} জন সদস্য পাওয়া গেছে:**")
            for member in found_members:
                col_m1, col_m2, col_m3 = st.columns([0.5, 3, 1])
                with col_m1:
                    st.image(member.get('photo_link', 'https://placehold.co/50x50/EEE/31343C?text=No+Image'), width=50)
                with col_m2:
                    st.markdown(f"**নাম:** {member['নাম']}<br>**ভোটার নং:** {member['ভোটার_নং']}<br>**পিতা:** {member['পিতার_নাম']}", unsafe_allow_html=True)
                with col_m3:
                    relationship_options = ["পিতা", "মাতা", "স্বামী", "স্ত্রী", "ছেলে", "মেয়ে", "ভাই", "বোন", "দাদা", "দাদী", "নাতি", "নাতনি", "চাচা", "চাচী", "ভাতিজা", "ভাতিজি", "মামা", "মামি", "ভাগ্নে", "ভাগ্নি", "শ্বশুর", "শাশুড়ি", "জামাই", "বউমা", "শালা", "শালী", "দেবর", "ননদ", "ভাসুর", "বউদি", "অন্যান্য"]
                    selected_relation = st.selectbox(
                        f"সম্পর্ক ({member['id']}):",
                        options=relationship_options,
                        key=f"relation_select_{member['id']}"
                    )
                    if st.button(f"যোগ করুন ({member['নাম']})", key=f"add_existing_member_{member['id']}"):
                        main_voter_gender = main_voter_details.get('gender')
                        member_gender = member.get('gender')
                        
                        # Get bidirectional relationships based on the selected relationship from the main voter's perspective
                        rel_map = get_bidirectional_relationships(selected_relation, main_voter_gender, member_gender)
                        
                        st.info(f"Adding connection: Main Voter ID: {st.session_state.selected_main_voter_id}, Target ID: {member['id']}, Relationship: {rel_map['source_to_target']}")
                        # Add connection from main voter to family member
                        success1 = db.add_family_connection(
                            st.session_state.selected_main_voter_id,
                            member['id'],
                            rel_map["source_to_target"]
                        )
                        st.info(f"Connection 1 Success: {success1}")

                        # Add connection from family member to main voter
                        st.info(f"Adding inverse connection: Source ID: {member['id']}, Target ID: {st.session_state.selected_main_voter_id}, Relationship: {rel_map['target_to_source']}")
                        success2 = db.add_family_connection(
                            member['id'],
                            st.session_state.selected_main_voter_id,
                            rel_map["target_to_source"]
                        )
                        st.info(f"Connection 2 Success: {success2}")

                        if success1 and success2:
                            st.success(f"{member['নাম']} কে পরিবারে যোগ করা হয়েছে এবং সম্পর্ক '{selected_relation}' হিসাবে সেট করা হয়েছে।")
                            st.session_state.family_search_query = "" # Clear search
                            st.rerun() # Rerun to update family list
                        else:
                            st.error(f"{member['নাম']} কে যোগ করতে ব্যর্থ। সম্পর্ক ইতিমধ্যে বিদ্যমান থাকতে পারে।")
        elif search_button and not found_members and st.session_state.family_search_query:
            st.info(f"'{st.session_state.family_search_query}' এর জন্য কোনো সদস্য পাওয়া যায়নি।")
        
    with tab2:
        st.subheader("নতুন সদস্য যোগ করুন এবং সম্পর্ক তৈরি করুন")
        with st.form("new_family_member_form"):
            st.session_state.new_family_member_data['নাম'] = st.text_input("নাম", value=st.session_state.new_family_member_data['নাম'], key="new_member_name")
            st.session_state.new_family_member_data['পিতার_নাম'] = st.text_input("পিতার নাম", value=st.session_state.new_family_member_data['পিতার_নাম'], key="new_member_father")
            st.session_state.new_family_member_data['মাতার_নাম'] = st.text_input("মাতার নাম", value=st.session_state.new_family_member_data['মাতার_নাম'], key="new_member_mother")
            st.session_state.new_family_member_data['ভোটার_নং'] = st.text_input("ভোটার নং (ঐচ্ছিক)", value=st.session_state.new_family_member_data['ভোটার_নং'], key="new_member_voter_no")
            st.session_state.new_family_member_data['gender'] = st.selectbox("লিঙ্গ", ["", "পুরুষ", "মহিলা", "অন্যান্য"], key="new_member_gender")
            
            # Date of Birth input with conversion
            dob_str = st.text_input("জন্ম তারিখ (DD-MM-YYYY)", value=st.session_state.new_family_member_data['জন্ম_তারিখ'], key="new_member_dob_input")
            st.session_state.new_family_member_data['জন্ম_তারিখ'] = dob_str # Store as string

            relationship_options = ["পিতা", "মাতা", "স্বামী", "স্ত্রী", "ছেলে", "মেয়ে", "ভাই", "বোন", "দাদা", "দাদী", "নাতি", "নাতনি", "চাচা", "চাচী", "ভাতিজা", "ভাতিজি", "মামা", "মামি", "ভাগ্নে", "ভাগ্নি", "শ্বশুর", "শাশুড়ি", "জামাই", "বউমা", "শালা", "শালী", "দেবর", "ননদ", "ভাসুর", "বউদি", "অন্যান্য"]
            st.session_state.relationship_type = st.selectbox(
                "সম্পর্ক:",
                options=relationship_options,
                key="new_member_relation_select"
            )

            submitted = st.form_submit_button("নতুন সদস্য যোগ করুন")

            if submitted:
                if not st.session_state.new_family_member_data['নাম']:
                    st.error("নাম আবশ্যক।")
                else:
                    try:
                        # Calculate age if DOB is provided
                        age = None
                        if st.session_state.new_family_member_data['জন্ম_তারিখ']:
                            try:
                                dob = datetime.strptime(st.session_state.new_family_member_data['জন্ম_তারিখ'], '%d-%m-%Y')
                                today = datetime.today()
                                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                            except ValueError:
                                st.warning("জন্ম তারিখের বিন্যাস ভুল (DD-MM-YYYY)। বয়স গণনা করা সম্ভব হয়নি।")
                                age = None

                        # Add new record to database (using a dummy batch_id or a generic "Family Tree Additions" batch)
                        # First, ensure a batch exists for manually added family members
                        family_batch_id = db.add_batch("Family Tree Additions")

                        new_member_record_data = {
                            "ক্রমিক_নং": "", # Can be empty or generated
                            "নাম": st.session_state.new_family_member_data['নাম'],
                            "ভোটার_নং": st.session_state.new_family_member_data['ভোটার_নং'],
                            "পিতার_নাম": st.session_state.new_family_member_data['পিতার_নাম'],
                            "মাতার_নাম": st.session_state.new_family_member_data['মাতার_নাম'],
                            "পেশা": "অজানা", # Default
                            "occupation_details": "",
                            "জন্ম_তারিখ": st.session_state.new_family_member_data['জন্ম_তারিখ'],
                            "ঠিকানা": "অজানা", # Default
                            "phone_number": "", "whatsapp_number": "",
                            "facebook_link": "", "tiktok_link": "", "youtube_link": "", "insta_link": "",
                            "photo_link": 'https://placehold.co/100x100/EEE/31343C?text=No+Image',
                            "description": "ম্যানুয়ালি পরিবার বৃক্ষে যোগ করা হয়েছে",
                            "political_status": "অজানা",
                            "relationship_status": "Regular",
                            "gender": st.session_state.new_family_member_data['gender'],
                            "age": age
                        }
                        new_member_id = db.add_record(family_batch_id, "family_tree_manual_entry", new_member_record_data)
                        db.commit_changes() # Commit the new record addition

                        if new_member_id:
                            main_voter_gender = main_voter_details.get('gender')
                            new_member_gender = new_member_record_data.get('gender')

                            rel_map = get_bidirectional_relationships(st.session_state.relationship_type, main_voter_gender, new_member_gender)
                            
                            st.info(f"Adding connection: Main Voter ID: {st.session_state.selected_main_voter_id}, Target ID: {new_member_id}, Relationship: {rel_map['source_to_target']}")
                            # Add connection from main voter to new family member
                            success1 = db.add_family_connection(
                                st.session_state.selected_main_voter_id,
                                new_member_id,
                                rel_map["source_to_target"]
                            )
                            st.info(f"Connection 1 Success: {success1}")

                            st.info(f"Adding inverse connection: Source ID: {new_member_id}, Target ID: {st.session_state.selected_main_voter_id}, Relationship: {rel_map['target_to_source']}")
                            # Add connection from new family member to main voter
                            success2 = db.add_family_connection(
                                new_member_id,
                                st.session_state.selected_main_voter_id,
                                rel_map["target_to_source"]
                            )
                            st.info(f"Connection 2 Success: {success2}")

                            if success1 and success2:
                                st.success(f"নতুন সদস্য '{st.session_state.new_family_member_data['নাম']}' যোগ করা হয়েছে এবং পরিবার বৃক্ষে সম্পর্ক তৈরি করা হয়েছে।")
                                # Clear form data
                                st.session_state.new_family_member_data = {
                                    "নাম": "", "পিতার_নাম": "", "মাতার_নাম": "", "ভোটার_নং": "",
                                    "gender": "", "জন্ম_তারিখ": ""
                                }
                                st.rerun() # Rerun to update family list
                            else:
                                st.error("পারিবারিক সম্পর্ক যোগ করতে ব্যর্থ।")
                        else:
                            st.error("নতুন সদস্য যোগ করতে ব্যর্থ।")
                    except Exception as e:
                        st.error(f"একটি ত্রুটি হয়েছে: {e}")
                        db.rollback_changes()

    st.markdown("---")

    st.header("৩. পরিবার বৃক্ষ প্রদর্শন")
    family_connections = db.get_family_connections_for_record(st.session_state.selected_main_voter_id)

    if family_connections:
        st.write(f"**{main_voter_details['নাম']} এর পারিবারিক সদস্যগণ:**")
        for i, connection in enumerate(family_connections):
            col_d1, col_d2, col_d3 = st.columns([0.5, 3, 1])
            with col_d1:
                st.image(connection.get('photo_link', 'https://placehold.co/50x50/EEE/31343C?text=No+Image'), width=50)
            with col_d2:
                st.markdown(f"**সম্পর্ক:** {connection['relationship_to_source']}<br>"
                            f"**নাম:** {connection['নাম']}<br>"
                            f"**ভোটার নং:** {connection['ভোটার_নং'] or 'N/A'}", unsafe_allow_html=True)
            with col_d3:
                if st.button("সম্পর্ক মুছুন", key=f"delete_connection_{connection['id']}_{i}"):
                    # To delete a bidirectional relationship, we need to delete both sides
                    # First, delete the connection from source to target
                    db.delete_family_connection(
                        st.session_state.selected_main_voter_id,
                        connection['id'],
                        connection['relationship_to_source']
                    )
                    # Then, infer the reverse relationship and delete it
                    # This is a bit tricky and might require a more robust relationship mapping
                    # For simplicity, let's just delete the direct link for now.
                    # A more advanced solution would involve storing the reverse relationship type explicitly
                    # when adding, or having a lookup table for inverse relationships.
                    
                    # For a robust deletion, we need to find the inverse relationship
                    # This is a simplified approach, assuming we can infer the inverse
                    # based on the main relationship types.
                    # This part needs careful consideration for all possible relationships.
                    
                    # For now, let's just delete the direct link. A full bidirectional delete
                    # would require knowing the exact inverse relationship type.
                    # To make it truly bidirectional delete, we would need to pass the
                    # original relationship type and then calculate its inverse.
                    # For example, if A is "Father" of B, then B is "Child" of A.
                    # If we delete A->B as "Father", we also need to delete B->A as "Child".
                    
                    # Let's add a simple inverse relationship mapping for deletion
                    inverse_relationships = {
                        "পিতা": "সন্তান", "মাতা": "সন্তান", "স্বামী": "স্ত্রী", "স্ত্রী": "স্বামী",
                        "ছেলে": "পিতা", "মেয়ে": "মাতা", "ভাই": "ভাই/বোন", "বোন": "ভাই/বোন",
                        "দাদা": "নাতি/নাতনি", "দাদী": "নাতি/নাতনি", "নাতি": "দাদা/দাদী", "নাতনি": "দাদা/দাদী",
                        "চাচা": "ভাতিজা/ভাতিজি", "চাচী": "ভাতিজা/ভাতিজি", "ভাতিজা": "চাচা/চাচী", "ভাতিজি": "চাচা/চাচী",
                        "মামা": "ভাগ্নে/ভাগ্নি", "মামি": "ভাগ্নে/ভাগ্নি", "ভাগ্নে": "মামা/মামি", "ভাগ্নি": "মামা/মামি",
                        "শ্বশুর": "জামাই/বউমা", "শাশুড়ি": "জামাই/বউমা", "জামাই": "শ্বশুর/শাশুড়ি", "বউমা": "শ্বশুর/শাশুড়ি",
                        "শালা": "ভগ্নিপতি", "শালী": "ভগ্নিপতি", "দেবর": "বউদি", "ননদ": "বউদি", "ভাসুর": "বউদি", "বউদি": "দেবর/ভাসুর",
                        "অন্যান্য": "অন্যান্য" # Default for unknown
                    }
                    
                    inverse_relation_type = inverse_relationships.get(connection['relationship_to_source'], "সম্পর্কিত ব্যক্তি")
                    
                    db.delete_family_connection(
                        connection['id'], # This is now the source
                        st.session_state.selected_main_voter_id, # This is now the target
                        inverse_relation_type
                    )
                    st.success("সম্পর্ক সফলভাবে মুছে ফেলা হয়েছে।")
                    st.rerun()
    else:
        st.info("এই ভোটারের জন্য কোনো পারিবারিক সম্পর্ক নেই।")

