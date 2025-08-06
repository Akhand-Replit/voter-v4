import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import os
import streamlit as st
from datetime import datetime
import re # For Bengali numeral conversion

# Configure logging
logger = logging.getLogger(__name__)

class Database:
    """
    Handles all database operations for the application, including connecting to
    PostgreSQL, creating tables, and managing records, batches, and events,
    and now family relationships.
    """
    def __init__(self):
        """Initializes the database connection using credentials from Streamlit secrets."""
        try:
            self.conn = psycopg2.connect(
                dbname=st.secrets["DB_NAME"],
                user=st.secrets["DB_USER"],
                password=st.secrets["DB_PASSWORD"],
                host=st.secrets["DB_HOST"],
                port=st.secrets["DB_PORT"],
            )
            # Ensure auto-commit is off to manage transactions manually
            self.conn.autocommit = False 
            self.create_tables()
            self.add_missing_columns() # Call method to add new columns if they don't exist
        except psycopg2.OperationalError as e:
            logger.error(f"Database connection failed: {e}")
            st.error("ডাটাবেস সংযোগ করতে ব্যর্থ। অনুগ্রহ করে আপনার শংসাপত্রগুলি পরীক্ষা করুন।")
            raise Exception("Failed to connect to database.")

    def create_tables(self):
        """
        Creates all necessary tables if they do not already exist.
        Removed DROP TABLE statements to ensure data persistence.
        """
        with self.conn.cursor() as cur:
            # Batches Table: Stores information about data batches.
            cur.execute("""
                CREATE TABLE IF NOT EXISTS batches (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Records Table: Stores the main data records.
            # Added new columns for political status, social media links, etc.
            cur.execute("""
                CREATE TABLE IF NOT EXISTS records (
                    id SERIAL PRIMARY KEY,
                    batch_id INTEGER REFERENCES batches(id) ON DELETE CASCADE,
                    file_name VARCHAR(255),
                    ক্রমিক_নং VARCHAR(50),
                    নাম TEXT,
                    ভোটার_নং VARCHAR(100),
                    পিতার_নাম TEXT,
                    মাতার_নাম TEXT,
                    পেশা TEXT,
                    occupation_details TEXT,
                    জন্ম_তারিখ VARCHAR(100),
                    ঠিকানা TEXT,
                    phone_number VARCHAR(50),
                    whatsapp_number VARCHAR(100),
                    facebook_link TEXT,
                    tiktok_link TEXT,
                    youtube_link TEXT,
                    insta_link TEXT,
                    photo_link TEXT DEFAULT 'https://placehold.co/100x100/EEE/31343C?text=No+Image',
                    description TEXT,
                    political_status TEXT,
                    relationship_status VARCHAR(20) DEFAULT 'Regular',
                    gender VARCHAR(10),
                    age INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Events Table: Stores event information.
            cur.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Record-Events Junction Table: Manages the many-to-many relationship between records and events.
            cur.execute("""
                CREATE TABLE IF NOT EXISTS record_events (
                    record_id INTEGER REFERENCES records(id) ON DELETE CASCADE,
                    event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
                    PRIMARY KEY (record_id, event_id)
                )
            """)

            # Family Relationships Table: Stores connections between records as family members.
            cur.execute("""
                CREATE TABLE IF NOT EXISTS family_connections (
                    id SERIAL PRIMARY KEY,
                    source_record_id INTEGER REFERENCES records(id) ON DELETE CASCADE,
                    target_record_id INTEGER REFERENCES records(id) ON DELETE CASCADE,
                    relationship_to_source VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (source_record_id, target_record_id, relationship_to_source)
                )
            """)
            self.conn.commit()

    def add_missing_columns(self):
        """
        Adds new columns to existing tables if they do not already exist.
        This is crucial for schema evolution without dropping data.
        """
        with self.conn.cursor() as cur:
            columns_to_add = {
                'age': 'INTEGER',
                'political_status': 'TEXT',
                'tiktok_link': 'TEXT',
                'youtube_link': 'TEXT',
                'insta_link': 'TEXT',
                'occupation_details': 'TEXT',
                'whatsapp_number': 'VARCHAR(100)'
            }
            for col, col_type in columns_to_add.items():
                try:
                    cur.execute(f"ALTER TABLE records ADD COLUMN IF NOT EXISTS {col} {col_type}")
                    logger.info(f"Added '{col}' column to 'records' table (if not exists).")
                except psycopg2.Error as e:
                    logger.warning(f"Could not add '{col}' column: {e}")
                    self.conn.rollback()
            
            # Set default for photo_link and update existing records
            try:
                cur.execute("ALTER TABLE records ALTER COLUMN photo_link SET DEFAULT 'https://placehold.co/100x100/EEE/31343C?text=No+Image'")
                cur.execute("UPDATE records SET photo_link = 'https://placehold.co/100x100/EEE/31343C?text=No+Image' WHERE photo_link IS NULL OR photo_link = ''")
                logger.info("Set default for 'photo_link' and updated existing NULL/empty records.")
            except psycopg2.Error as e:
                logger.warning(f"Could not set default for 'photo_link' column: {e}")
                self.conn.rollback()

            self.conn.commit()


    def get_dashboard_stats(self):
        """Retrieves key statistics for the main dashboard."""
        stats = {}
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Total records
            cur.execute("SELECT COUNT(*) as total_records FROM records")
            stats['total_records'] = cur.fetchone()['total_records']

            # Total batches
            cur.execute("SELECT COUNT(*) as total_batches FROM batches")
            stats['total_batches'] = cur.fetchone()['total_batches']

            # Total events
            cur.execute("SELECT COUNT(*) as total_events FROM events")
            stats['total_events'] = cur.fetchone()['total_events']

            # Relationship counts
            cur.execute("SELECT relationship_status, COUNT(*) as count FROM records GROUP BY relationship_status")
            relationship_counts = cur.fetchall()
            stats['relationships'] = {item['relationship_status']: item['count'] for item in relationship_counts}

            # Gender counts
            cur.execute("SELECT gender, COUNT(*) as count FROM records WHERE gender IS NOT NULL AND gender != '' GROUP BY gender")
            gender_counts = cur.fetchall()
            stats['genders'] = {item['gender']: item['count'] for item in gender_counts}

            # Age distribution (optional, for dashboard or analysis page)
            cur.execute("SELECT CASE WHEN age IS NULL THEN 'Unknown' ELSE (FLOOR(age / 10) * 10 || '-' || (FLOOR(age / 10) * 10 + 9)) END as age_group, COUNT(*) as count FROM records WHERE age IS NOT NULL GROUP BY age_group ORDER BY age_group")
            age_distribution = cur.fetchall()
            stats['age_distribution'] = age_distribution

        return stats

    # --- Event Management ---
    def add_event(self, event_name):
        """Adds a new event to the database."""
        with self.conn.cursor() as cur:
            cur.execute("INSERT INTO events (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (event_name,))
            self.conn.commit()

    def get_all_events(self):
        """Retrieves all events from the database."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM events ORDER BY name")
            return cur.fetchall()

    def delete_event(self, event_id):
        """Deletes an event and its associations from the database."""
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM record_events WHERE event_id = %s", (event_id,))
            cur.execute("DELETE FROM events WHERE id = %s", (event_id,))
            self.conn.commit()

    def get_events_for_record(self, record_id):
        """Retrieves all event names assigned to a specific record."""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT e.name
                FROM events e
                JOIN record_events re ON e.id = re.event_id
                WHERE re.record_id = %s
                ORDER BY e.name
            """, (record_id,))
            return [row[0] for row in cur.fetchall()]

    def assign_events_to_record(self, record_id, event_ids):
        """Assigns a list of events to a record, replacing any existing assignments."""
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM record_events WHERE record_id = %s", (record_id,))
            if event_ids:
                args_str = ','.join(cur.mogrify("(%s,%s)", (record_id, event_id)).decode('utf-8') for event_id in event_ids)
                cur.execute("INSERT INTO record_events (record_id, event_id) VALUES " + args_str)
            self.conn.commit()

    def get_records_for_event(self, event_id):
        """Gets all records associated with a specific event ID."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT r.*, b.name as batch_name
                FROM records r
                JOIN record_events re ON r.id = re.record_id
                JOIN batches b ON r.batch_id = b.id
                WHERE re.event_id = %s
                ORDER BY r.id
            """, (event_id,))
            records = cur.fetchall()
        # Fetch associated events for each record (though they should all include the filtered event)
        for record in records:
            record['events'] = self.get_events_for_record(record['id'])
        return records

    # --- Record & Batch Management ---
    def add_batch(self, batch_name):
        """Adds a new batch or returns the ID of an existing one."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO batches (name) VALUES (%s) ON CONFLICT (name) DO UPDATE SET name=EXCLUDED.name RETURNING id",
                (batch_name,)
            )
            result = cur.fetchone()
            self.conn.commit()
            return result['id']

    def add_record(self, batch_id, file_name, record_data):
        """
        Adds a new record to the database, including calculated age.
        This function only executes the INSERT statement; the calling function
        is responsible for committing or rolling back the transaction.
        """
        with self.conn.cursor() as cur:
            whatsapp_number = record_data.get('whatsapp_number')
            if whatsapp_number and not whatsapp_number.startswith('https://wa.me/'):
                whatsapp_number = f"https://wa.me/{whatsapp_number}"

            phone_number = record_data.get('phone_number')
            if phone_number and not phone_number.startswith('tel:'):
                phone_number = f"tel:{phone_number}"
            
            photo_link = record_data.get('photo_link')
            if not photo_link or not photo_link.strip():
                photo_link = 'https://placehold.co/100x100/EEE/31343C?text=No+Image'
            
            cur.execute("""
                INSERT INTO records (
                    batch_id, file_name, ক্রমিক_নং, নাম, ভোটার_নং,
                    পিতার_নাম, মাতার_নাম, পেশা, occupation_details, জন্ম_তারিখ, ঠিকানা,
                    phone_number, whatsapp_number, facebook_link, tiktok_link, youtube_link, insta_link, photo_link, description,
                    political_status, relationship_status, gender, age
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, ( # Added RETURNING id here
                batch_id, file_name,
                record_data.get('ক্রমিক_নং'), record_data.get('নাম'),
                record_data.get('ভোটার_নং'), record_data.get('পিতার_নাম'),
                record_data.get('মাতার_নাম'), record_data.get('পেশা'), record_data.get('occupation_details'),
                record_data.get('জন্ম_তারিখ'), record_data.get('ঠিকানা'),
                phone_number, whatsapp_number, record_data.get('facebook_link'),
                record_data.get('tiktok_link'), record_data.get('youtube_link'), record_data.get('insta_link'),
                photo_link, record_data.get('description'),
                record_data.get('political_status'),
                record_data.get('relationship_status', 'Regular'),
                record_data.get('gender'),
                record_data.get('age')
            ))
            return cur.fetchone()[0] # Return the ID of the newly added record


    def commit_changes(self):
        """Commits the current database transaction."""
        try:
            self.conn.commit()
            logger.info("Database changes committed successfully.")
        except psycopg2.Error as e:
            logger.error(f"Error committing transaction: {e}")
            self.conn.rollback() # Rollback on commit failure
            raise

    def rollback_changes(self):
        """Rolls back the current database transaction."""
        self.conn.rollback()
        logger.warning("Database transaction rolled back.")

    def update_record(self, record_id, updated_data):
        """Updates an existing record with new data, including age if provided."""
        with self.conn.cursor() as cur:
            whatsapp_number = updated_data.get('whatsapp_number')
            if whatsapp_number and not str(whatsapp_number).startswith('https://wa.me/'):
                whatsapp_number = f"https://wa.me/{whatsapp_number}"
            
            phone_number = updated_data.get('phone_number')
            if phone_number and not str(phone_number).startswith('tel:'):
                phone_number = f"tel:{phone_number}"

            photo_link = updated_data.get('photo_link')
            if not photo_link or not photo_link.strip():
                photo_link = 'https://placehold.co/100x100/EEE/31343C?text=No+Image'

            query = """
                UPDATE records SET
                    ক্রমিক_নং = %s, নাম = %s, ভোটার_নং = %s, পিতার_নাম = %s,
                    মাতার_নাম = %s, পেশা = %s, occupation_details = %s, ঠিকানা = %s, জন্ম_তারিখ = %s,
                    phone_number = %s, whatsapp_number = %s, facebook_link = %s, tiktok_link = %s, youtube_link = %s, insta_link = %s, photo_link = %s,
                    description = %s, political_status = %s, relationship_status = %s,
                    gender = %s, age = %s
                WHERE id = %s
            """
            values = (
                str(updated_data.get('ক্রমিক_নং', '')), str(updated_data.get('নাম', '')),
                str(updated_data.get('ভোটার_নং', '')), str(updated_data.get('পিতার_নাম', '')),
                str(updated_data.get('মাতার_নাম', '')), str(updated_data.get('পেশা', '')),
                str(updated_data.get('occupation_details', '')), str(updated_data.get('ঠিকানা', '')), str(updated_data.get('জন্ম_তারিখ', '')),
                phone_number, whatsapp_number, str(updated_data.get('facebook_link', '')),
                str(updated_data.get('tiktok_link', '')), str(updated_data.get('youtube_link', '')), str(updated_data.get('insta_link', '')),
                photo_link, str(updated_data.get('description', '')),
                str(updated_data.get('political_status', '')),
                str(updated_data.get('relationship_status', 'Regular')),
                str(updated_data.get('gender', '')),
                updated_data.get('age'),
                record_id
            )
            cur.execute(query, values)
            self.conn.commit()

    def search_records_advanced(self, criteria):
        """Performs an advanced search for records based on multiple criteria."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            query_parts = []
            params = []

            # Handle 'নাম' and 'ভোটার_নং' with OR logic if both are provided
            name_query = criteria.get('নাম')
            voter_no_query = criteria.get('ভোটার_নং')

            if name_query and voter_no_query and name_query == voter_no_query:
                # If the same query is used for both, search either name OR voter_no
                query_parts.append("(নাম ILIKE %s OR ভোটার_নং ILIKE %s)")
                params.extend([f"%{name_query}%", f"%{voter_no_query}%"])
            else:
                # Otherwise, treat them as separate AND conditions or if only one is present
                if name_query:
                    query_parts.append("নাম ILIKE %s")
                    params.append(f"%{name_query}%")
                if voter_no_query:
                    query_parts.append("ভোটার_নং ILIKE %s")
                    params.append(f"%{voter_no_query}%")

            # Handle other criteria (e.g., gender) with AND logic
            for field, value in criteria.items():
                if field not in ['নাম', 'ভোটার_নং'] and value:
                    if field == 'gender' and value != 'সব':
                        query_parts.append(f"{field} = %s")
                        params.append(value)
                    elif field != 'gender':
                        query_parts.append(f"{field} ILIKE %s")
                        params.append(f"%{value}%")
            
            final_query = "SELECT r.*, b.name as batch_name FROM records r JOIN batches b ON r.batch_id = b.id"
            if query_parts:
                final_query += " WHERE " + " AND ".join(query_parts)
            
            final_query += " ORDER BY r.id"
            
            cur.execute(final_query, params)
            records = cur.fetchall()
        for record in records:
            record['events'] = self.get_events_for_record(record['id'])
        return records

    def get_all_batches(self):
        """Retrieves all batches from the database."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM batches ORDER BY created_at DESC")
            return cur.fetchall()

    def get_batch_records(self, batch_id):
        """Retrieves all records for a specific batch."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT r.*, b.name as batch_name
                FROM records r
                JOIN batches b ON r.batch_id = b.id
                WHERE r.batch_id = %s
                ORDER BY r.id
            """, (batch_id,))
            records = cur.fetchall()
        for record in records:
            record['events'] = self.get_events_for_record(record['id'])
        return records
        
    def get_batch_files(self, batch_id):
        """Get unique files in a batch"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT DISTINCT file_name
                FROM records
                WHERE batch_id = %s
                ORDER BY file_name
            """, (batch_id,))
            return cur.fetchall()

    def get_file_records(self, batch_id, file_name):
        """Get records for a specific file in a batch"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT r.*, b.name as batch_name
                FROM records r
                JOIN batches b ON r.batch_id = b.id
                WHERE r.batch_id = %s AND r.file_name = %s
                ORDER BY r.id
            """, (batch_id, file_name))
            records = cur.fetchall()
        for record in records:
            record['events'] = self.get_events_for_record(record['id'])
        return records

    def get_batch_occupation_stats(self, batch_id):
        """Retrieves occupation statistics for a specific batch."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT পেশা, COUNT(*) as count
                FROM records
                WHERE batch_id = %s AND পেশা IS NOT NULL AND পেশা != ''
                GROUP BY পেশা ORDER BY count DESC
            """, (batch_id,))
            return cur.fetchall()

    def get_occupation_stats(self):
        """Retrieves overall occupation statistics across all batches."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT পেশা, COUNT(*) as count
                FROM records
                WHERE পেশা IS NOT NULL AND পেশা != ''
                GROUP BY পেশা ORDER BY count DESC
            """)
            return cur.fetchall()

    def get_gender_stats(self, batch_id=None):
        """Retrieves gender statistics for a specific batch or all batches."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT gender, COUNT(*) as count
                FROM records
                WHERE gender IS NOT NULL AND gender != ''
            """
            if batch_id:
                query += " AND batch_id = %s"
                params = (batch_id,)
            else:
                params = ()
            query += " GROUP BY gender ORDER BY count DESC"
            cur.execute(query, params)
            return cur.fetchall()

    def update_relationship_status(self, record_id: int, status: str):
        """Updates the relationship status for a specific record."""
        with self.conn.cursor() as cur:
            cur.execute("UPDATE records SET relationship_status = %s WHERE id = %s", (status, record_id))
            self.conn.commit()

    def get_relationship_records(self, status: str):
        """Retrieves all records with a specific relationship status, including their events."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT r.*, b.name as batch_name
                FROM records r
                JOIN batches b ON r.batch_id = b.id
                WHERE r.relationship_status = %s
                ORDER BY r.created_at DESC
            """, (status,))
            records = cur.fetchall()
        for record in records:
            record['events'] = self.get_events_for_record(record['id'])
        return records

    def get_batch_by_name(self, batch_name):
        """Retrieves batch information by its name."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM batches WHERE name = %s", (batch_name,))
            return cur.fetchone()

    def get_batch_by_id(self, batch_id):
        """Retrieves batch information by its ID."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM batches WHERE id = %s", (batch_id,))
            return cur.fetchone()

    def delete_batch(self, batch_id: int):
        """Deletes a batch and all its associated records."""
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM records WHERE batch_id = %s", (batch_id,))
            cur.execute("DELETE FROM batches WHERE id = %s", (batch_id,))
            self.conn.commit()

    def get_total_records_count(self):
        """Retrieves the total number of records in the database."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM records")
            return cur.fetchone()[0]

    def get_all_records_with_dob(self):
        """Retrieves all records that have a 'জন্ম_তারিখ' (date of birth)."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, জন্ম_তারিখ
                FROM records
                WHERE জন্ম_তারিখ IS NOT NULL AND জন্ম_তারিখ != ''
            """)
            return cur.fetchall()

    def update_record_age(self, record_id: int, age: int):
        """Updates the 'age' column for a specific record."""
        with self.conn.cursor() as cur:
            cur.execute("UPDATE records SET age = %s WHERE id = %s", (age, record_id))
            # No commit here, as it will be part of a larger transaction in the age management page

    def get_record_by_id(self, record_id: int):
        """Retrieves a single record by its ID."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT r.*, b.name as batch_name
                FROM records r
                JOIN batches b ON r.batch_id = b.id
                WHERE r.id = %s
            """, (record_id,))
            record = cur.fetchone()
            if record:
                record['events'] = self.get_events_for_record(record['id'])
            return record

    def get_record_by_voter_no(self, voter_no: str):
        """Retrieves a single record by its voter number."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT r.*, b.name as batch_name
                FROM records r
                JOIN batches b ON r.batch_id = b.id
                WHERE r.ভোটার_নং = %s
            """, (voter_no,))
            record = cur.fetchone()
            if record:
                record['events'] = self.get_events_for_record(record['id'])
            return record

    def add_family_connection(self, source_record_id: int, target_record_id: int, relationship_to_source: str):
        """
        Adds a family connection between two records.
        This function adds a unidirectional relationship from source to target.
        For bidirectional relationships (e.g., parent-child), call this function twice.
        """
        with self.conn.cursor() as cur:
            try:
                cur.execute("""
                    INSERT INTO family_connections (source_record_id, target_record_id, relationship_to_source)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (source_record_id, target_record_id, relationship_to_source) DO NOTHING
                """, (source_record_id, target_record_id, relationship_to_source))
                self.conn.commit()
                return True
            except psycopg2.Error as e:
                logger.error(f"Error adding family connection: {e}")
                self.conn.rollback()
                return False

    def get_family_connections_for_record(self, record_id: int):
        """
        Retrieves all family connections for a given record.
        Returns a list of dictionaries, each containing the connected record's details
        and the relationship type to the source record.
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    fc.relationship_to_source,
                    r.id, r.নাম, r.ভোটার_নং, r.পিতার_নাম, r.মাতার_নাম, r.photo_link, r.gender, r.age
                FROM family_connections fc
                JOIN records r ON fc.target_record_id = r.id
                WHERE fc.source_record_id = %s
                ORDER BY r.নাম
            """, (record_id,))
            return cur.fetchall()

    def delete_family_connection(self, source_record_id: int, target_record_id: int, relationship_to_source: str):
        """Deletes a specific unidirectional family connection."""
        with self.conn.cursor() as cur:
            try:
                cur.execute("""
                    DELETE FROM family_connections
                    WHERE source_record_id = %s AND target_record_id = %s AND relationship_to_source = %s
                """, (source_record_id, target_record_id, relationship_to_source))
                self.conn.commit()
                return True
            except psycopg2.Error as e:
                logger.error(f"Error deleting family connection: {e}")
                self.conn.rollback()
                return False

    def get_all_voters_for_search(self):
        """Retrieves a minimal set of voter data for search/selection dropdowns."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, নাম, ভোটার_নং, পিতার_নাম, মাতার_নাম, photo_link FROM records ORDER BY নাম")
            return cur.fetchall()
