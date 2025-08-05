import os
import sys
import streamlit as st
import logging

# Add the current directory to Python path to ensure imports work correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from attached_assets.auth import init_auth, login_form, logout
from utils.styling import apply_custom_styling
from utils.database import Database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Akhand Data Dashboard",
    page_icon="📊",
    layout="wide"  # Use wide layout for a better dashboard feel
)

# Apply custom CSS styling
apply_custom_styling()

# Hide Streamlit's default branding
hide_st_style = """
<style>
._profileContainer_gzau3_53 {visibility: hidden!important;}
._link_gzau3_10  {visibility: hidden!important;}
.st-emotion-cache-15wzwg4 .e1d5ycv517  {visibility: hidden!important;}
.st-emotion-cache-q16mip .e1i26tt71  {visibility: hidden!important;}
</style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# Initialize session state for authentication
init_auth()

def main():
    """
    The main function that runs the Streamlit application.
    It handles authentication and displays the appropriate view (login page or dashboard).
    """
    # If user is authenticated, show the main dashboard
    if st.session_state.get('authenticated', False):
        db = Database()

        # --- Header with Title and Logout Button ---
        col_header1, col_header2 = st.columns([5, 1])
        with col_header1:
            st.title("📊 Akhand Data ড্যাশবোর্ড")
            st.markdown("আপনার ডাটা ম্যানেজমেন্ট এবং বিশ্লেষণের জন্য একটি সমন্বিত প্ল্যাটফর্ম।")
        with col_header2:
            if st.button("⬅️ লগ আউট", use_container_width=True):
                logout()
                st.rerun()

        st.markdown("---")

        # --- Key Performance Indicators (KPIs) ---
        st.subheader("এক নজরে গুরুত্বপূর্ণ পরিসংখ্যান")
        
        # Fetch dashboard statistics from the database
        stats = db.get_dashboard_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="📝 মোট রেকর্ড", value=stats.get('total_records', 0))
        with col2:
            st.metric(label="🗂️ মোট ব্যাচ", value=stats.get('total_batches', 0))
        with col3:
            st.metric(label="🤝 বন্ধু", value=stats.get('relationships', {}).get('Friend', 0))
        with col4:
            st.metric(label="⚔️ শত্রু", value=stats.get('relationships', {}).get('Enemy', 0))

        st.markdown("<br>", unsafe_allow_html=True)

        # --- Core Features / Navigation ---
        st.subheader("অ্যাপ্লিকেশনের মূল ফিচারসমূহ")
        
        with st.container(border=True):
            col_nav1, col_nav2, col_nav3 = st.columns(3)
            with col_nav1:
                st.markdown("##### 📤 ডাটা ম্যানেজমেন্ট")
                st.markdown("""
                - **আপলোড:** টেক্সট ফাইল থেকে সহজেই ডাটা আপলোড করুন।
                - **সম্পাদনা:** 'সব তথ্য' পেজ থেকে সরাসরি ডাটা পরিবর্তন ও পরিবর্ধন করুন।
                - **রেকর্ড যোগ:** ম্যানুয়ালি নতুন রেকর্ড যোগ করুন।
                """)
            with col_nav2:
                st.markdown("##### 🔍 অনুসন্ধান এবং ফিল্টারিং")
                st.markdown("""
                - **সার্চ:** নাম, ভোটার নং, ঠিকানাসহ বিভিন্ন ফিল্টার ব্যবহার করে দ্রুত তথ্য খুঁজুন।
                - **সম্পাদনাযোগ্য সার্চ:** অনুসন্ধানের ফলাফল সরাসরি সম্পাদনা করুন।
                - **ইভেন্ট ফিল্টার:** নির্দিষ্ট ইভেন্টের সাথে যুক্ত ব্যক্তিদের তালিকা দেখুন।
                """)
            with col_nav3:
                st.markdown("##### 📊 বিশ্লেষণ এবং সম্পর্ক")
                st.markdown("""
                - **অ্যানালাইসিস:** পেশাভিত্তিক ডাটা বিশ্লেষণের মাধ্যমে মূল্যবান তথ্য জানুন।
                - **সম্পর্ক:** 'বন্ধু', 'শত্রু' এবং 'সংযুক্ত' হিসেবে সম্পর্ক নির্ধারণ ও ট্র্যাক করুন।
                - **সারসংক্ষেপ:** সম্পর্ক এবং অন্যান্য পরিসংখ্যানের একটি ভিজ্যুয়াল চিত্র দেখুন।
                """)

    # If user is not authenticated, show the login form
    else:
        login_form()

if __name__ == "__main__":
    main()
