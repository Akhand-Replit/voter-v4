import re
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mapping for Bengali numerals to English numerals
BENGALI_NUMERALS = {
    '০': '0', '১': '1', '২': '2', '৩': '3', '৪': '4',
    '৫': '5', '৬': '6', '৭': '7', '৮': '8', '৯': '9'
}

def convert_bengali_numerals_to_english(text):
    """Converts Bengali numerals in a string to English numerals."""
    if not isinstance(text, str):
        return text
    for bengali, english in BENGALI_NUMERALS.items():
        text = text.replace(bengali, english)
    return text

def calculate_age(dob_str):
    """
    Calculates age from a date of birth string.
    Expects date in DD-MM-YYYY format (English numerals).
    Returns age as an integer or None if parsing fails.
    """
    if not dob_str:
        return None
    
    # Convert any Bengali numerals to English first
    dob_str_english = convert_bengali_numerals_to_english(dob_str)

    try:
        # Attempt to parse common date formats
        # Prioritize DD-MM-YYYY, then YYYY-MM-DD, then MM-DD-YYYY
        for fmt in ["%d-%m-%Y", "%Y-%m-%d", "%m-%d-%Y", "%d/%m/%Y", "%Y/%m/%d", "%m/%d/%Y"]:
            try:
                birth_date = datetime.strptime(dob_str_english, fmt)
                today = datetime.today()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                return age
            except ValueError:
                continue # Try next format
        logger.warning(f"Could not parse date of birth string: {dob_str}. Returning None for age.")
        return None
    except Exception as e:
        logger.error(f"Error calculating age for '{dob_str}': {e}")
        return None

def process_text_file(content, default_gender=None):
    """Process the text file content and extract structured data."""
    records = []

    try:
        # Remove BOM and normalize newlines
        content = content.strip().replace('\ufeff', '').replace('\r\n', '\n')

        # Split into records using both Bengali and English numerals
        # This pattern looks for lines starting with numbers followed by a dot
        raw_records = re.split(r'\n\s*(?=(?:[০-৯]+|[0-9]+)\.)', content)
        logger.info(f"Initial split found {len(raw_records)} potential records")

        for record in raw_records:
            if not record.strip():
                continue

            logger.debug(f"Processing record: {record[:100]}...")
            record_dict = {}

            # Define field patterns with more flexible matching
            field_patterns = {
                'ক্রমিক_নং': (r'^([০-৯]+|[0-9]+)\.', True),  # True means take full match
                'নাম': (r'নাম:?\s*([^,\n।]+)', False),
                'ভোটার_নং': (r'ভোটার\s*নং:?\s*([^,\n।]+)', False),
                'পিতার_নাম': (r'পিতা:?\s*([^,\n।]+)', False),
                'মাতার_নাম': (r'মাতা:?\s*([^,\n।]+)', False),
                'পেশা': (r'পেশা:?\s*([^,।\n]+)', False),
                'জন্ম_তারিখ': (r'জন্ম\s*তারিখ:?\s*([^,\n।]+)', False),
                'ঠিকানা': (r'ঠিকানা:?\s*([^,\n।]+(?:[,\n।][^,\n।]+)*)', False),
                'gender': (r'লিঙ্গ:?\s*(পুরুষ|মহিলা|অন্যান্য|Male|Female|Other)', False) # Added gender pattern
            }

            # Extract each field
            for field, (pattern, full_match) in field_patterns.items():
                match = re.search(pattern, record, re.MULTILINE | re.IGNORECASE) # Ignore case for gender
                if match:
                    # For ক্রমিক_নং, take the full match and remove the dot
                    value = match.group(0).strip() if full_match else match.group(1).strip()
                    if field == 'ক্রমিক_নং':
                        value = value.rstrip('.')
                    record_dict[field] = value.strip()
            
            # If gender not found in text, use default_gender
            if 'gender' not in record_dict and default_gender:
                record_dict['gender'] = default_gender

            # Calculate age from 'জন্ম_তারিখ'
            dob = record_dict.get('জন্ম_তারিখ')
            if dob:
                record_dict['age'] = calculate_age(dob)
            else:
                record_dict['age'] = None # Ensure age is set to None if DOB is missing

            # Only add records that have at least a few key fields
            required_fields = {'ক্রমিক_নং', 'নাম', 'ভোটার_নং'}
            if all(field in record_dict for field in required_fields):
                records.append(record_dict)
                logger.debug(f"Added record with fields: {list(record_dict.keys())}")
            else:
                logger.warning(f"Skipped incomplete record: missing required fields")

        logger.info(f"Successfully processed {len(records)} complete records")
        return records

    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise Exception(f"Failed to process file: {str(e)}")
