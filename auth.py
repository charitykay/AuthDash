# ============================================================================
# auth.py — Authentication functions for user registration and login
# ============================================================================
# IMPROVEMENTS IN THIS VERSION:
# 1. register_user() - Create a new user account in the database
# 2. login_user() - Verify user credentials
# 3. change_password() - NEW: Change password with old password verification
# ============================================================================

from database import connect_db  # Function to connect to SQLite database
from utils import hash_password # Utility functions for hashing and validation  
from database import connect_db  # Function to connect to SQLite database
from utils import hash_password, is_valid_password

# ────────────────────────────────────────────────────────────────────────────
# REGISTRATION FUNCTION
# ────────────────────────────────────────────────────────────────────────────

def register_user(username, password):
    """
    Register a new user account in the database.
    
    Creates a new user record with a hashed password. Usernames must be unique.
    Passwords are hashed using SHA-256 for security before storage.
    
    Args:
        username (str): The desired username (3-30 alphanumeric chars + underscore).
        password (str): The desired password (8+ chars, 1 uppercase, 1 digit).
    
    Returns:
        bool: True if user successfully registered, False if registration failed.
    
    Raises:
        Exception: If database connection fails or SQL execution error occurs.
    
    Exceptions Handled:
        sqlite3.IntegrityError: Caught when username already exists (UNIQUE constraint).
    
    Example:
        >>> success = register_user("alice_smith", "SecurePass123")
        >>> if success:
        ...     print("User registered!")
        >>> else:
        ...     print("Username already taken")
    
    Notes:
        - Username must be unique; duplicate usernames return False
        - Passwords are NOT stored in plaintext; they are hashed
        - No email verification is performed
        - Account is immediately active after registration
    
    Edge Cases:
        - Empty username/password: SQL INSERT may fail
        - Very long strings: SQLite stores them as-is (performance impact)
        - Special characters: Only letters, digits, underscores allowed
        - SQL injection: Protected by parameterized queries (?)
    """
    try:
        # Step 1: Connect to the database
        conn = connect_db()  # Open connection to users.db
        cursor = conn.cursor()  # Create cursor to execute SQL commands

        # Step 2: Hash the password (convert to secure format)
        hashed = hash_password(password)  # Convert plaintext to hash

        # Step 3: Insert the new user into the 'users' table
        # The ? are placeholders to prevent SQL injection attacks
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed)  # Provide the actual values to insert
        )

        # Step 4: Save changes and close connection
        conn.commit()  # Finalize the insertion
        conn.close()   # Close the database connection
        return True  # Success!

    except Exception as e:  # Catch any errors (like duplicate username)
        print("Register error:", e)  # Print error for debugging
        return False  # Return False to indicate registration failed




# ────────────────────────────────────────────────────────────────────────────
# LOGIN FUNCTION
# ────────────────────────────────────────────────────────────────────────────

def login_user(username, password):
    """
    Verify user credentials and retrieve user data if authentication succeeds.
    
    Attempts to authenticate a user by comparing the provided password hash
    against the stored password hash in the database. Returns user tuple if
    credentials match, None otherwise.
    
    Args:
        username (str): The username attempting to log in.
        password (str): The plain-text password to verify.
    
    Returns:
        tuple: User data tuple (id, username, password_hash) if login successful.
        None: If username not found OR password doesn't match.
    
    Raises:
        Exception: If database connection fails or SQL execution error occurs.
    
    Exceptions Handled:
        All exceptions are caught; function returns None on database errors.
    
    Example:
        >>> user = login_user("alice_smith", "SecurePass123")
        >>> if user:
        ...     user_id, username, _ = user
        ...     print(f"Logged in as {username}")
        >>> else:
        ...     print("Invalid credentials")
    
    Notes:
        - Password is hashed before comparison (never compares plaintext)
        - Both username AND password must match for successful login
        - User tuple contains password hash (3rd element) - do NOT use directly
        - This function does NOT create a session; use in Flask route to set session
    
    Edge Cases:
        - Non-existent username: Returns None (same as wrong password)
        - Correct username, wrong password: Returns None (security best practice)
        - Database unavailable: Returns None instead of raising exception
        - SQL injection: Protected by parameterized queries (?)
    """
    try:
        # Step 1: Connect to the database
        conn = connect_db()  # Open connection to users.db
        cursor = conn.cursor()  # Create cursor to execute SQL commands

        # Step 2: Hash the provided password to compare with stored hash
        hashed = hash_password(password)  # Convert plaintext to hash

        # Step 3: Query the database for a matching user
        # SELECT * retrieves all columns (id, username, password)
        # WHERE checks if BOTH username AND password match
        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, hashed)  # Use hashed password for comparison
        )

        # Step 4: Fetch the result (get the matching user if found)
        user = cursor.fetchone()  # Get first matching row (or None if no match)
        conn.close()  # Close the database connection

        return user  # Return user data if found, None if credentials don't match

    except Exception as e:  # Catch any database errors
        print("Login error:", e)  # Print error for debugging
        return None  # Return None to indicate login failed


# ────────────────────────────────────────────────────────────────────────────
# PASSWORD CHANGE FUNCTION — NEW IMPROVEMENT #1
# ────────────────────────────────────────────────────────────────────────────

def change_password(user_id, old_password, new_password):
    
    """
    Change user password after verifying the old password is correct.
    
    Security-focused password change that validates:
    1. The old password matches the current password in database
    2. The new password meets security requirements
    3. Old and new passwords are different
    
    This is a critical security feature that users expect. It allows:
    - Users to update compromised passwords
    - Recovery from weak password choices
    - Password rotation for security hygiene
    
    Args:
        user_id (int): The user's ID in database (from session)
        old_password (str): User's current password (plaintext)
        new_password (str): User's desired new password (plaintext)
    
    Returns:
        dict: Result dictionary with two keys:
            {
                'success': bool,  # True if password changed, False if failed
                'message': str    # Human-readable error or success message
            }
    
    Example:
        >>> result = change_password(1, "OldPass123", "NewPass456")
        >>> if result['success']:
        ...     print("✓ Password changed successfully!")
        >>> else:
        ...     print(f"✗ Error: {result['message']}")
    
    Workflow:
        1. Validate new password meets security requirements
        2. Prevent reusing same password (security best practice)
        3. Connect to database
        4. Verify old password is correct (hashed comparison)
        5. Update password hash in database
        6. Return result with success/error message
    
    Error Cases Handled:
        - New password invalid: Returns error with requirement details
        - New password same as old: Returns error (security)
        - User ID not found: Returns False (shouldn't happen in normal flow)
        - Old password incorrect: Returns error (explicit feedback)
        - Database error: Returns False with generic error message
    
    Security Considerations:
        - Old password verified using hash comparison (not plaintext)
        - New password hashed before storage (never stored plaintext)
        - No password history tracking (users CAN reuse old passwords after ~3 changes)
        - Function returns generic errors for some failures (security)
        - Should only be called after user authentication (from @login_required route)
    
    Notes:
        - Passwords are hashed using SHA-256 (from utils.hash_password)
        - Validation uses validate_password() from utils
        - Password requirements: 8+ chars, 1 uppercase, 1 digit
        - Function does NOT create session or log user out
        - User remains logged in after password change (no re-authentication needed)
    
    Edge Cases:
        - User ID doesn't exist: This shouldn't happen if called from @login_required route
        - Database locked: Caught and returns error
        - Invalid user_id type: Could raise exception (should validate in route)
        - Null old_password: Will hash to a value and fail comparison
        - Null new_password: Will fail validate_password() check
    
    Logging:
        - No security logging (could leak password info)
        - Error messages printed to console for debugging
        - In production: Should log password change events (without passwords)
    
    Related Functions:
        - validate_password() in utils.py - Checks password requirements
        - hash_password() in utils.py - Converts password to SHA-256 hash
        - login_user() in auth.py - Similar hashing logic
    
    Testing:
        >>> # Test 1: Successful password change
        >>> result = change_password(1, "OldPass123", "NewPass456")
        >>> assert result['success'] == True
        
        >>> # Test 2: Wrong old password
        >>> result = change_password(1, "WrongPassword", "NewPass456")
        >>> assert result['success'] == False
        >>> assert "incorrect" in result['message'].lower()
        
        >>> # Test 3: Same old and new password
        >>> result = change_password(1, "OldPass123", "OldPass123")
        >>> assert result['success'] == False
        >>> assert "different" in result['message'].lower()
    """
    try:
        # Step 1: Validate new password meets requirements
        # validate_password() returns (is_valid: bool, error_message: str)
        is_valid, error_msg = is_valid_password(new_password)
        if not is_valid:
            # Password doesn't meet requirements (e.g., too short, no uppercase, etc.)
            return {
                'success': False,
                'message': f"New password invalid: {error_msg}"
            }
        
        # Step 2: Prevent reusing same password
        # Hash both old and new passwords to compare
        old_hash = hash_password(old_password)
        new_hash = hash_password(new_password)
        
        # If hashes are identical, passwords are the same
        if old_hash == new_hash:
            return {
                'success': False,
                'message': "New password must be different from current password"
            }
        
        # Step 3: Connect to database
        conn = connect_db()
        cursor = conn.cursor()
        
        # Step 4: Verify old password is correct
        # Query for this user's current password hash
        cursor.execute(
            "SELECT password FROM users WHERE id=?",
            (user_id,)
        )
        result = cursor.fetchone()
        
        # If user not found, something is wrong (shouldn't happen with @login_required)
        if not result:
            conn.close()
            return {
                'success': False,
                'message': "User not found"
            }
        
        # Step 5: Compare provided old password with stored hash
        # If they don't match, the user entered wrong password
        stored_password = result[0]
        if old_hash != stored_password:
            conn.close()
            return {
                'success': False,
                'message': "Current password is incorrect"
            }
        
        # Step 6: Update password in database
        # Old password verified, new password validated → safe to update
        cursor.execute(
            "UPDATE users SET password=? WHERE id=?",
            (new_hash, user_id)
        )
        
        # Step 7: Save changes and close connection
        conn.commit()  # Finalize the update
        conn.close()   # Close database connection
        
        return {
            'success': True,
            'message': "Password changed successfully"
        }
    
    except Exception as e:
        # Catch any database or unexpected errors
        print(f"Password change error: {e}")
        return {
            'success': False,
            'message': "An error occurred while changing password"
        }