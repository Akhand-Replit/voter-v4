import streamlit as st
from utils.database import Database
from utils.styling import apply_custom_styling
from datetime import datetime

# --- Page Configuration and Initialization ---
st.set_page_config(page_title="Family Tree", layout="wide")
apply_custom_styling()

# Initialize database connection
db = Database()

# --- Caching ---
@st.cache_data(ttl=60)
def search_voters(query):
    """Cached function to search for voters by name or ID."""
    if not query:
        return []
    search_criteria = {"নাম": query, "ভোটার_নং": query}
    return db.search_records_advanced(search_criteria)

@st.cache_data(ttl=30)
def get_family_connections(_voter_id):
    """Cached function to get family connections for a specific voter."""
    if _voter_id is None:
        return []
    return db.get_family_connections_for_record(_voter_id)

# --- Helper Functions ---
def get_bidirectional_relationships(relationship_type):
    """Returns the forward and reverse relationship types."""
    relationships = {
        "পিতা": {"source_to_target": "পিতা", "target_to_source": "সন্তান"},
        "মাতা": {"source_to_target": "মাতা", "target_to_source": "সন্তান"},
        "স্বামী": {"source_to_target": "স্বামী", "target_to_source": "স্ত্রী"},
        "স্ত্রী": {"source_to_target": "স্ত্রী", "target_to_source": "স্বামী"},
        "ছেলে": {"source_to_target": "ছেলে", "target_to_source": "পিতা"},
        "মেয়ে": {"source_to_target": "মেয়ে", "target_to_source": "মাতা"},
        "ভাই": {"source_to_target": "ভাই", "target_to_source": "ভাই"},
        "বোন": {"source_to_target": "বোন", "target_to_source": "বোন"},
        "দাদা": {"source_to_target": "দাদা", "target_to_source": "নাতি"},
        "দাদী": {"source_to_target": "দাদী", "target_to_source": "নাতনি"},
        "নাতি": {"source_to_target": "নাতি", "target_to_source": "দাদা"},
        "নাতনি": {"source_to_target": "নাতনি", "target_to_source": "দাদী"},
        "চাচা": {"source_to_target": "চাচা", "target_to_source": "ভাতিজা"},
        "চাচী": {"source_to_target": "চাচী", "target_to_source": "ভাতিজি"},
        "ভাতিজা": {"source_to_target": "ভাতিজা", "target_to_source": "চাচা"},
        "ভাতিজি": {"source_to_target": "ভাতিজি", "target_to_source": "চাচী"},
        "মামা": {"source_to_target": "মামা", "target_to_source": "ভাগ্নে"},
        "মামি": {"source_to_target": "মামি", "target_to_source": "ভাগ্নি"},
        "ভাগ্নে": {"source_to_target": "ভাগ্নে", "target_to_source": "মামা"},
        "ভাগ্নি": {"source_to_target": "ভাগ্নি", "target_to_source": "মামি"},
        "শ্বশুর": {"source_to_target": "শ্বশুর", "target_to_source": "জামাই"},
        "শাশুড়ি": {"source_to_target": "শাশুড়ি", "target_to_source": "বউমা"},
        "জামাই": {"source_to_target": "জামাই", "target_to_source": "শ্বশুর"},
        "বউমা": {"source_to_target": "বউমা", "target_to_source": "শাশুড়ি"},
        "অন্যান্য": {"source_to_target": "অন্যান্য", "target_to_source": "অন্যান্য"},
    }
    return relationships.get(relationship_type, {"source_to_target": relationship_type, "target_to_source": "সম্পর্কিত ব্যক্তি"})

def clear_and_rerun():
    """Clears relevant caches and session state, then reruns the app."""
    get_family_connections.clear()
    search_voters.clear()
    
    keys_to_clear = ['family_search_query', 'new_family_member_data', 'main_voter_radio', 'current_voter_options', 'main_search_results']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
            
    st.rerun()

# --- Session State Initialization & Callbacks ---
if 'selected_main_voter_id' not in st.session_state:
    st.session_state.selected_main_voter_id = None
if 'main_search_results' not in st.session_state:
    st.session_state.main_search_results = None
if 'current_voter_options' not in st.session_state:
    st.session_state.current_voter_options = {}

def on_voter_selection_change():
    """Callback to update the selected voter ID based on radio button."""
    selected_option_str = st.session_state.main_voter_radio
    voter_options = st.session_state.get('current_voter_options', {})
    
    if selected_option_str == "-- নির্বাচন বাতিল করুন --":
        st.session_state.selected_main_voter_id = None
    elif selected_option_str in voter_options:
        st.session_state.selected_main_voter_id = voter_options[selected_option_str]

# --- UI Rendering ---
st.title("পরিবার বৃক্ষ ব্যবস্থাপনা 🌳")
st.markdown("আপনার ভোটার ডেটাবেসের মধ্যে পারিবারিক সম্পর্ক তৈরি এবং পরিচালনা করুন।")

# --- 1. Main Voter Selection (Search-based with Button) ---
st.header("১. প্রধান ভোটার নির্বাচন করুন")
search_col1, search_col2 = st.columns([3, 1])
with search_col1:
    main_voter_search_query = st.text_input("নাম বা ভোটার নং দ্বারা প্রধান ভোটার খুঁজুন:", key="main_voter_search_input")
with search_col2:
    st.write("") # Vertical spacer for alignment
    if st.button("অনুসন্ধান", key="main_search_button"):
        with st.spinner("অনুসন্ধান করা হচ্ছে..."):
            st.session_state.main_search_results = search_voters(main_voter_search_query)
        # Clear previous selection when a new search is made
        st.session_state.selected_main_voter_id = None
        if 'main_voter_radio' in st.session_state:
            del st.session_state['main_voter_radio']

# Display search results only if they exist in the session state
if st.session_state.main_search_results is not None:
    search_results = st.session_state.main_search_results
    if search_results:
        st.session_state.current_voter_options = {f"{voter['নাম']} ({voter['ভোটার_নং'] or 'N/A'}) - ID: {voter['id']}": voter['id'] for voter in search_results}
        options_list = ["-- নির্বাচন বাতিল করুন --"] + list(st.session_state.current_voter_options.keys())
        st.radio(
            "অনুসন্ধানের ফলাফল থেকে নির্বাচন করুন:",
            options=options_list,
            key="main_voter_radio",
            on_change=on_voter_selection_change
        )
    else:
        st.info("আপনার অনুসন্ধানের জন্য কোনো ভোটার পাওয়া যায়নি।")

# --- Display Selected Voter and Main Logic ---
if st.session_state.selected_main_voter_id:
    main_voter_details = db.get_record_by_id(st.session_state.selected_main_voter_id)
    if main_voter_details:
        with st.container(border=True):
            st.subheader(f"নির্বাচিত ভোটার: {main_voter_details['নাম']}")
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(main_voter_details.get('photo_link', 'https://placehold.co/100x100/EEE/31343C?text=No+Image'), width=100)
            with col2:
                st.write(f"**ভোটার নং:** {main_voter_details.get('ভোটার_নং', 'N/A')}")
                st.write(f"**পিতা:** {main_voter_details.get('পিতার_নাম', 'N/A')}")
                st.write(f"**লিঙ্গ:** {main_voter_details.get('gender', 'N/A')}")
                st.write(f"**বয়স:** {main_voter_details.get('age', 'N/A')}")
        
        st.markdown("---")
        
        # --- 2. Add Family Member ---
        st.header("২. পারিবারিক সদস্য যোগ করুন")
        RELATIONSHIP_OPTIONS = ["পিতা", "মাতা", "স্বামী", "স্ত্রী", "ছেলে", "মেয়ে", "ভাই", "বোন", "দাদা", "দাদী", "নাতি", "নাতনি", "চাচা", "চাচী", "ভাতিজা", "ভাতিজি", "মামা", "মামি", "ভাগ্নে", "ভাগ্নি", "শ্বশুর", "শাশুড়ি", "জামাই", "বউমা", "অন্যান্য"]
        tab1, tab2 = st.tabs(["বিদ্যমান সদস্য খুঁজুন", "নতুন সদস্য যোগ করুন"])

        with tab1:
            st.subheader("বিদ্যমান সদস্য খুঁজুন এবং যোগ করুন")
            search_query = st.text_input("নাম বা ভোটার নং দ্বারা খুঁজুন:", key="family_search_input")
            if search_query:
                found_members = search_voters(search_query)
                found_members = [m for m in found_members if m['id'] != st.session_state.selected_main_voter_id]
                if found_members:
                    st.write(f"**{len(found_members)} জন সদস্য পাওয়া গেছে:**")
                    for member in found_members:
                        with st.container(border=True):
                            col_m1, col_m2, col_m3 = st.columns([1, 4, 2])
                            with col_m1:
                                st.image(member.get('photo_link', 'https://placehold.co/60x60/EEE/31343C?text=N/A'), width=60)
                            with col_m2:
                                st.markdown(f"**নাম:** {member['নাম']}<br>**ভোটার নং:** {member.get('ভোটার_নং', 'N/A')}", unsafe_allow_html=True)
                            with col_m3:
                                selected_relation = st.selectbox("সম্পর্ক:", RELATIONSHIP_OPTIONS, key=f"relation_select_{member['id']}")
                                if st.button("যোগ করুন", key=f"add_existing_member_{member['id']}"):
                                    rel_map = get_bidirectional_relationships(selected_relation)
                                    try:
                                        db.add_family_connection(st.session_state.selected_main_voter_id, member['id'], rel_map["source_to_target"])
                                        db.add_family_connection(member['id'], st.session_state.selected_main_voter_id, rel_map["target_to_source"])
                                        db.commit_changes()
                                        st.success(f"{member['নাম']} কে পরিবারে যোগ করা হয়েছে।")
                                        clear_and_rerun()
                                    except Exception as e:
                                        db.rollback_changes()
                                        st.error(f"যোগ করতে ব্যর্থ: {e}. সম্পর্ক ইতিমধ্যে বিদ্যমান থাকতে পারে।")
                else:
                    st.info("কোনো সদস্য পাওয়া যায়নি।")
        
        with tab2:
            st.subheader("নতুন সদস্য যোগ করুন এবং সম্পর্ক তৈরি করুন")
            with st.form("new_family_member_form"):
                name = st.text_input("নাম")
                father_name = st.text_input("পিতার নাম")
                voter_no = st.text_input("ভোটার নং (ঐচ্ছিক)")
                gender = st.selectbox("লিঙ্গ", ["", "পুরুষ", "মহিলা", "অন্যান্য"])
                relationship_type = st.selectbox("প্রধান ভোটারের সাথে সম্পর্ক:", RELATIONSHIP_OPTIONS)
                submitted = st.form_submit_button("নতুন সদস্য যোগ করুন")
                if submitted:
                    if not name:
                        st.error("নাম আবশ্যক।")
                    else:
                        try:
                            family_batch_id = db.add_batch("Family Tree Additions")
                            new_member_data = {"নাম": name, "পিতার_নাম": father_name, "ভোটার_নং": voter_no, "gender": gender, "description": "পরিবার বৃক্ষ থেকে যোগ করা হয়েছে"}
                            new_member_id = db.add_record(family_batch_id, "family_tree_manual", new_member_data)
                            rel_map = get_bidirectional_relationships(relationship_type)
                            db.add_family_connection(st.session_state.selected_main_voter_id, new_member_id, rel_map["source_to_target"])
                            db.add_family_connection(new_member_id, st.session_state.selected_main_voter_id, rel_map["target_to_source"])
                            db.commit_changes()
                            st.success(f"নতুন সদস্য '{name}' যোগ করা হয়েছে।")
                            clear_and_rerun()
                        except Exception as e:
                            db.rollback_changes()
                            st.error(f"নতুন সদস্য যোগ করতে ব্যর্থ: {e}")
        
        st.markdown("---")
        
        # --- 3. Display Family Tree ---
        st.header("৩. পরিবার বৃক্ষ প্রদর্শন")
        family_connections = get_family_connections(st.session_state.selected_main_voter_id)
        if family_connections:
            st.write(f"**{main_voter_details['নাম']} এর পারিবারিক সদস্যগণ:**")
            for connection in family_connections:
                with st.container(border=True):
                    col_d1, col_d2, col_d3 = st.columns([1, 4, 1.5])
                    with col_d1:
                        st.image(connection.get('photo_link', 'https://placehold.co/60x60/EEE/31343C?text=N/A'), width=60)
                    with col_d2:
                        st.markdown(f"**সম্পর্ক:** {connection['relationship_to_source']}<br>**নাম:** {connection['নাম']}", unsafe_allow_html=True)
                    with col_d3:
                        if st.button("মুছুন", key=f"delete_connection_{connection['id']}"):
                            try:
                                rel_map = get_bidirectional_relationships(connection['relationship_to_source'])
                                db.delete_family_connection(st.session_state.selected_main_voter_id, connection['id'], rel_map["source_to_target"])
                                db.delete_family_connection(connection['id'], st.session_state.selected_main_voter_id, rel_map["target_to_source"])
                                db.commit_changes()
                                st.success(f"{connection['নাম']} এর সাথে সম্পর্ক মুছে ফেলা হয়েছে।")
                                clear_and_rerun()
                            except Exception as e:
                                db.rollback_changes()
                                st.error(f"মুছতে ব্যর্থ: {e}")
        else:
            st.info("এই ভোটারের জন্য কোনো পারিবারিক সম্পর্ক নেই।")

else:
    st.info("শুরু করতে, অনুগ্রহ করে উপরে একজন প্রধান ভোটার খুঁজুন এবং নির্বাচন করুন।")
