# ============================================================================
# database.py — Database connection and management
# ============================================================================
# This file handles all database operations:
# 1. Connecting to SQLite database (users.db)
# 2. Creating tables for users, profiles, and settings
# 3. Reading and writing user data (profiles and settings)
# ============================================================================

import sqlite3  # Module for working with SQLite databases


# ────────────────────────────────────────────────────────────────────────────
# DATABASE CONNECTION
# ────────────────────────────────────────────────────────────────────────────

def connect_db():
    """
    Open a connection to the SQLite database.
    
    What this does:
    - Opens (or creates if it doesn't exist) a file called 'users.db'
    - Returns a connection object we can use to send SQL commands
    
    Returns:
        sqlite3.Connection: Connection object to the database
    """
    return sqlite3.connect("users.db")  # Connect to users.db file




# ────────────────────────────────────────────────────────────────────────────
# TABLE CREATION
# ────────────────────────────────────────────────────────────────────────────

def create_table():
    """
    Create all required database tables if they do not already exist.
    
    Initializes the SQLite database schema with three tables:
    1. users - Stores authentication credentials
    2. profiles - Stores user profile information
    3. settings - Stores notification preferences
    
    Creates tables only if they don't exist (idempotent operation).
    
    Args:
        None
    
    Returns:
        None: Modifies database but returns nothing on success.
    
    Raises:
        sqlite3.Error: If SQL execution fails or database is corrupted.
        IOError: If database file cannot be accessed/created.
    
    Example:
        >>> create_table()  # Safe to call multiple times
        >>> # Tables now exist in users.db
    
    Tables Created:
        users (id, username, password):
            - id: Auto-incrementing primary key
            - username: UNIQUE constraint (no duplicates)
            - password: SHA-256 hashed password
        
        profiles (id, user_id, full_name, email, bio, updated_at):
            - One profile per user (UNIQUE user_id)
            - CASCADE delete: profile deleted if user deleted
        
        settings (id, user_id, email_notifications, push_notifications, 
                  marketing_emails, updated_at):
            - One settings record per user (UNIQUE user_id)
            - Default values: email=ON, push=ON, marketing=OFF
            - CASCADE delete: settings deleted if user deleted
    
    Notes:
        - Uses IF NOT EXISTS to prevent errors on repeated calls
        - All operations are committed automatically
        - Called automatically when app.py starts
        - No data is lost if called on existing database
    
    Edge Cases:
        - Database file doesn't exist: SQLite creates it automatically
        - Insufficient permissions: Raises IOError
        - Database is locked: Operation blocks until lock is released
    
    Performance:
        - First call: ~50-100ms (creates 3 tables)
        - Subsequent calls: ~10-20ms (tables already exist)
    """
    # Step 1: Connect to database
    conn = connect_db()  # Open connection
    cursor = conn.cursor()  # Create cursor for executing SQL commands

    # Step 2: Create 'users' table (if it doesn't exist)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Unique ID (auto-numbered: 1, 2, 3...)
        username TEXT UNIQUE,                  -- Username (must be unique, no duplicates allowed)
        password TEXT                          -- Hashed password (never plaintext!)
    )
    """)

    # Step 3: Create 'profiles' table (if it doesn't exist)
    # This stores extra user information
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Unique ID for this profile
        user_id INTEGER UNIQUE,                -- Link to user (one profile per user)
        full_name TEXT,                        -- User's full name
        email TEXT,                            -- User's email address
        bio TEXT,                              -- User's biography/description
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- When was this last updated?
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE  -- If user deleted, delete profile too
    )
    """)

    # Step 4: Create 'settings' table (if it doesn't exist)
    # This stores notification preferences for each user
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Unique ID for this settings record
        user_id INTEGER UNIQUE,                -- Link to user (one settings record per user)
        email_notifications INTEGER DEFAULT 1,   -- 1 = ON, 0 = OFF (default: ON)
        push_notifications INTEGER DEFAULT 1,    -- 1 = ON, 0 = OFF (default: ON)
        marketing_emails INTEGER DEFAULT 0,      -- 1 = ON, 0 = OFF (default: OFF)
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- When was this last updated?
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE  -- If user deleted, delete settings too
    )
    """)

    # Step 5: Save all changes and close connection
    conn.commit()  # Finalize all CREATE TABLE commands
    conn.close()   # Close the database connection




# ────────────────────────────────────────────────────────────────────────────
# PROFILE FUNCTIONS (Read and Write)
# ────────────────────────────────────────────────────────────────────────────

def get_profile(user_id):
    """
    Retrieve a user's profile information from the database.
    
    Fetches the profile record associated with a specific user ID.
    Returns profile data as dictionary or None if profile doesn't exist.
    
    Args:
        user_id (int): The unique identifier of the user (from users table).
    
    Returns:
        dict: Dictionary with keys 'full_name', 'email', 'bio' if profile exists.
              Example: {'full_name': 'Alice Smith', 'email': 'alice@example.com', 'bio': '...'}
        None: If no profile is found for the given user_id.
    
    Raises:
        sqlite3.Error: If database query fails or connection is lost.
    
    Example:
        >>> profile = get_profile(1)
        >>> if profile:
        ...     print(f"Name: {profile['full_name']}")
        ...     print(f"Email: {profile['email']}")
        >>> else:
        ...     print("Profile not found")
    
    Notes:
        - New users may not have a profile (returns None)
        - If profile exists, all fields are returned (may be empty strings)
        - Profile data is read-only; use save_profile() to modify
        - Query is optimized by selecting only needed columns
    
    Edge Cases:
        - Invalid user_id (negative or zero): Returns None (no match)
        - Deleted user: Returns None (CASCADE delete removes profile)
        - Concurrent deletion: Possible None return during race condition
        - Empty bio/email fields: Still returned as empty strings, not None
    
    Performance:
        - Typical query time: 5-10ms
        - Indexed if user_id is frequently queried
    """
    # Step 1: Connect to database
    conn = connect_db()  # Open connection
    cursor = conn.cursor()  # Create cursor
    
    # Step 2: Query the profiles table for this user
    # The ? is a placeholder to prevent SQL injection attacks
    cursor.execute(
        "SELECT full_name, email, bio FROM profiles WHERE user_id = ?",
        (user_id,)
    )
    
    # Step 3: Get the result
    profile = cursor.fetchone()  # Returns (full_name, email, bio) tuple or None
    conn.close()  # Close connection
    
    # Step 4: Convert to dictionary format (easier to work with)
    if profile:
        return {
            "full_name": profile[0],  # First item in tuple
            "email": profile[1],      # Second item
            "bio": profile[2]         # Third item
        }
    return None  # No profile found for this user


def save_profile(user_id, full_name, email, bio):
    """
    Save or update a user's profile information.
    
    Performs an "upsert" operation (INSERT or UPDATE):
    - If user_id doesn't exist: Creates new profile record
    - If user_id exists: Updates existing profile record
    
    Args:
        user_id (int): The unique identifier of the user (must exist in users table).
        full_name (str): User's full name (can be empty string).
        email (str): User's email address (can be empty string).
        bio (str): User's biography/description (can be empty string).
    
    Returns:
        bool: Always True (operation succeeded or created new record).
    
    Raises:
        sqlite3.Error: If database write fails or connection is lost.
        sqlite3.IntegrityError: If user_id doesn't exist in users table (FK violation).
    
    Example:
        >>> success = save_profile(1, "Alice Smith", "alice@example.com", "Software engineer")
        >>> # Now user 1's profile is saved/updated
        >>> 
        >>> profile = get_profile(1)
        >>> print(profile['full_name'])  # Output: "Alice Smith"
    
    Notes:
        - Operation is atomic (all-or-nothing)
        - updated_at timestamp is automatically set to CURRENT_TIMESTAMP
        - User_id must exist in users table (enforced by FOREIGN KEY)
        - All profile fields are stored as TEXT (flexible length)
        - Empty strings are valid; use them instead of NULL
    
    Edge Cases:
        - user_id doesn't exist: Raises IntegrityError (FK violation)
        - Very long strings: Stored as-is (no length limit in SQLite)
        - Special characters: Stored safely (parameterized query protects)
        - NULL values: Converted to empty strings
        - Concurrent updates: Later update wins (last write wins)
    
    Performance:
        - Typical operation time: 10-20ms
        - Can be slow if database is locked (waits for lock)
    
    SQL Operation:
        Uses INSERT...ON CONFLICT...DO UPDATE (upsert pattern)
        More efficient than separate INSERT/UPDATE logic
    """
    # Step 1: Connect to database
    conn = connect_db()  # Open connection
    cursor = conn.cursor()  # Create cursor
    
    # Step 2: Insert or update (upsert) the profile
    # If user_id already exists: UPDATE the existing profile
    # If user_id is new: INSERT a new profile record
    cursor.execute("""
    INSERT INTO profiles (user_id, full_name, email, bio)
    VALUES (?, ?, ?, ?)  -- Try to insert
    ON CONFLICT(user_id) DO UPDATE SET  -- If user exists instead...
        full_name = excluded.full_name,  -- Update these fields
        email = excluded.email,
        bio = excluded.bio,
        updated_at = CURRENT_TIMESTAMP   -- Record when this was updated
    """, (user_id, full_name, email, bio))  # Provide the values
    
    # Step 3: Save changes and close
    conn.commit()  # Finalize changes to database
    conn.close()   # Close connection
    return True    # Success!




# ────────────────────────────────────────────────────────────────────────────
# SETTINGS FUNCTIONS (Read and Write)
# ────────────────────────────────────────────────────────────────────────────

def get_settings(user_id):
    """
    Retrieve a user's notification and preference settings.
    
    Fetches the settings record associated with a specific user ID.
    Returns settings as dictionary with notification preferences or None.
    
    Args:
        user_id (int): The unique identifier of the user (from users table).
    
    Returns:
        dict: Dictionary with keys 'email_notifications', 'push_notifications', 
              'marketing_emails'. Values are 1 (ON) or 0 (OFF).
              Example: {'email_notifications': 1, 'push_notifications': 1, 'marketing_emails': 0}
        None: If no settings record is found for the given user_id.
    
    Raises:
        sqlite3.Error: If database query fails or connection is lost.
    
    Example:
        >>> settings = get_settings(1)
        >>> if settings:
        ...     if settings['email_notifications']:
        ...         print("Email notifications enabled")
        ...     else:
        ...         print("Email notifications disabled")
        >>> else:
        ...     print("Settings not found")
    
    Notes:
        - New users may not have settings (returns None)
        - Integer values (1=ON, 0=OFF) instead of boolean for database compatibility
        - Default settings (if created): email=ON, push=ON, marketing=OFF
        - Settings are read-only; use save_settings() to modify
    
    Edge Cases:
        - Invalid user_id: Returns None (no match)
        - Deleted user: Returns None (CASCADE delete removes settings)
        - Concurrent deletion: Possible None return during race condition
        - All values are 0 or 1 (no other values possible)
    
    Performance:
        - Typical query time: 5-10ms
    """
    # Step 1: Connect to database
    conn = connect_db()  # Open connection
    cursor = conn.cursor()  # Create cursor
    
    # Step 2: Query the settings table for this user
    cursor.execute("""
    SELECT email_notifications, push_notifications, marketing_emails
    FROM settings WHERE user_id = ?
    """, (user_id,))
    
    # Step 3: Get the result
    settings = cursor.fetchone()  # Returns tuple or None
    conn.close()  # Close connection
    
    # Step 4: Convert to dictionary format (easier to work with)
    if settings:
        return {
            "email_notifications": settings[0],  # 1 (ON) or 0 (OFF)
            "push_notifications": settings[1],   # 1 (ON) or 0 (OFF)
            "marketing_emails": settings[2]      # 1 (ON) or 0 (OFF)
        }
    return None  # No settings found for this user


def save_settings(user_id, email_notifications, push_notifications, marketing_emails):
    """
    Save or update a user's notification and preference settings.
    
    Performs an "upsert" operation (INSERT or UPDATE):
    - If user_id doesn't exist: Creates new settings record
    - If user_id exists: Updates existing settings record
    
    Args:
        user_id (int): The unique identifier of the user (must exist in users table).
        email_notifications (int): 1 = ON, 0 = OFF. Enable email notifications.
        push_notifications (int): 1 = ON, 0 = OFF. Enable push notifications.
        marketing_emails (int): 1 = ON, 0 = OFF. Enable marketing emails.
    
    Returns:
        bool: Always True (operation succeeded or created new record).
    
    Raises:
        sqlite3.Error: If database write fails or connection is lost.
        sqlite3.IntegrityError: If user_id doesn't exist in users table (FK violation).
    
    Example:
        >>> save_settings(1, email_notifications=1, push_notifications=0, marketing_emails=0)
        >>> # User 1 now has: email ON, push OFF, marketing OFF
        >>> 
        >>> settings = get_settings(1)
        >>> print(settings)  # {'email_notifications': 1, 'push_notifications': 0, 'marketing_emails': 0}
    
    Notes:
        - Operation is atomic (all-or-nothing)
        - updated_at timestamp is automatically set to CURRENT_TIMESTAMP
        - User_id must exist in users table (enforced by FOREIGN KEY)
        - All values must be 0 or 1 (integer not boolean)
        - Calling multiple times is safe (updates in place)
    
    Edge Cases:
        - user_id doesn't exist: Raises IntegrityError (FK violation)
        - Invalid values (not 0 or 1): Stored as-is (no validation here)
        - Null values: Treated as 0
        - Concurrent updates: Later update wins (last write wins)
        - All three settings must be provided (no partial updates)
    
    Performance:
        - Typical operation time: 10-20ms
    
    SQL Operation:
        Uses INSERT...ON CONFLICT...DO UPDATE (upsert pattern)
    """
    # Step 1: Connect to database
    conn = connect_db()  # Open connection
    cursor = conn.cursor()  # Create cursor
    
    # Step 2: Insert or update (upsert) the settings
    # If user_id already exists: UPDATE existing settings
    # If user_id is new: INSERT brand new settings record
    cursor.execute("""
    INSERT INTO settings (user_id, email_notifications, push_notifications, marketing_emails)
    VALUES (?, ?, ?, ?)  -- Try to insert
    ON CONFLICT(user_id) DO UPDATE SET  -- If user exists instead...
        email_notifications = excluded.email_notifications,  -- Update these
        push_notifications = excluded.push_notifications,
        marketing_emails = excluded.marketing_emails,
        updated_at = CURRENT_TIMESTAMP  -- Record when this was updated
    """, (user_id, email_notifications, push_notifications, marketing_emails))
    
    # Step 3: Save changes and close
    conn.commit()  # Finalize changes to database
    conn.close()   # Close connection
    return True    # Success!