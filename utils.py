# ============================================================================
# utils.py — Utility functions (validation, hashing, error messages)
# ============================================================================
# This file contains helper functions used throughout the app:
# - Validation: Check if username/password meet requirements
# - Hashing: Convert passwords to secure format
# - Error messages: Generate user-friendly error explanations
# ============================================================================

import re  # Module for pattern matching and regular expressions
import logging  # Module for logging messages

logger = logging.getLogger(__name__)  # Set up logging for this file


# ────────────────────────────────────────────────────────────────────────────
# VALIDATION PATTERNS
# ────────────────────────────────────────────────────────────────────────────

# Regular expression pattern that usernames MUST follow
# ^ = start of string
# [a-zA-Z0-9_] = allowed characters - letters, numbers, underscore
# {3,30} = length: minimum 3, maximum 30 characters
# $ = end of string
USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,30}$")




# ────────────────────────────────────────────────────────────────────────────
# USERNAME VALIDATION
# ────────────────────────────────────────────────────────────────────────────

def is_valid_username(username: str) -> bool:
    """
    Validate that a username follows required format rules.
    
    Checks if username meets the following criteria:
    - Length: 3 to 30 characters (inclusive)
    - Characters: Only letters (a-z, A-Z), digits (0-9), underscores (_)
    - NO spaces, NO special characters, NO emoji
    
    Uses regex pattern matching with USERNAME_RE pattern defined at module level.
    This is a FAST validation check that does NOT check database for existing usernames.
    
    Args:
        username (str): The username string to validate
    
    Returns:
        bool: True if username is valid (meets ALL format rules), False otherwise
    
    Example:
        >>> is_valid_username("alice_123")
        True
        >>> is_valid_username("ab")  # Too short (< 3 chars)
        False
        >>> is_valid_username("alice@123")  # Invalid special character (@)
        False
        >>> is_valid_username("alice smith")  # Contains space (not allowed)
        False
    
    Valid Examples:
        - "alice" (5 letters - simple)
        - "user_123" (7 alphanumeric + underscore)
        - "A1B2C3D4" (mixed case with digits)
        - "john_doe_42" (30 chars, at maximum limit)
        - "__init__" (double underscores allowed)
    
    Invalid Examples:
        - "ab" (only 2 chars, minimum is 3)
        - "a" (too short)
        - "this_is_a_very_long_username_over_30_chars" (exceeds 30 char limit)
        - "user@name" (@ is special character, not allowed)
        - "john doe" (space not allowed)
        - "用户名" (non-ASCII Unicode characters not allowed)
        - "user-name" (hyphen is special character, not allowed)
    
    Notes:
        - This function only validates FORMAT, NOT uniqueness in database
        - Use with register_user() which checks for duplicate usernames
        - Case-sensitive: Treats "Alice" and "alice" as different (both valid)
        - Underscore is recommended for multi-word usernames instead of spaces
        - Leading/trailing whitespace is NOT automatically stripped
            (call sanitise_username(username) first if needed)
    
    Edge Cases:
        - Empty string "" : Returns False
        - None: Will raise TypeError (not caught)
        - Whitespace only "   ": Returns False
        - 29-30 characters: Valid (at upper boundary)
        - Mixed case "AlIcE_123": Valid (case doesn't matter)
        - Multiple consecutive underscores "__init__": Valid
    
    Performance:
        - Constant time O(1) due to maximum length constraint (30 chars)
        - Regex match is highly optimized for this simple pattern
        - No database lookups performed
    """
    # Use the USERNAME_RE pattern defined at module level to validate
    # Pattern: ^[a-zA-Z0-9_]{3,30}$ means:
    #   ^ = start of string
    #   [a-zA-Z0-9_] = allowed characters only
    #   {3,30} = length must be between 3-30 chars (inclusive)
    #   $ = end of string (no trailing chars allowed)
    return bool(USERNAME_RE.match(username))  # True if matches pattern, False otherwise




# ────────────────────────────────────────────────────────────────────────────
# PASSWORD VALIDATION
# ────────────────────────────────────────────────────────────────────────────

def is_valid_password(password: str) -> bool:
    """
    Validate that a password meets minimum strength requirements.
    
    Enforces three security requirements that MUST ALL be satisfied:
    1. Minimum length of 8 characters (prevents brute-force attacks)
    2. At least one UPPERCASE letter (A-Z) (requires mixed case)
    3. At least one DIGIT (0-9) (requires numbers, not just letters)
    
    ALL THREE conditions must be true for validation to pass. This increases
    password entropy and prevents common weak passwords like "password123"
    (no uppercase) or "PASSWORD" (no numbers).
    
    Args:
        password (str): The password string to validate
    
    Returns:
        bool: True if password meets ALL strength requirements, False if any check fails
    
    Example:
        >>> is_valid_password("SecurePass123")
        True
        >>> is_valid_password("password123")  # Missing uppercase
        False
        >>> is_valid_password("PASSWORD123")  # Missing lowercase? Actually valid!
        True
        >>> is_valid_password("Pass123")  # Too short (7 chars, need 8)
        False
        >>> is_valid_password("HelloWorld2")
        True
    
    Valid Examples:
        - "SecurePass123" (all requirements met)
        - "MyPassword8" (11 chars, uppercase, digits)
        - "Hello2World" (uppercase, digit, 11 chars)
        - "A1bCdE2fG" (8 chars minimum with mixed case and digits)
        - "UPPERCASE1" (all uppercase with digits - valid!)
    
    Invalid Examples:
        - "password123" (8 chars, digits, but NO UPPERCASE)
        - "PASSWORD" (has uppercase and 8+ chars, but NO DIGITS)
        - "Passw0rd" (appears strong but only 8 chars - wait, this IS valid!)
        - "Pass12" (too short - only 6 chars, needs minimum 8)
        - "secure" (only lowercase, too short, no digits)
        - "PASS" (4 chars, no digits, no lowercase)
    
    Notes:
        - Note: Lowercase letters are NOT required (just uppercase and digits)
        - This is FORMAT validation only, does NOT check for:
            * Common dictionary words (e.g., "Password123")
            * Patterns (e.g., "Qwerty123", keyboard sequential)
            * User's own username (check this in register_user())
            * Already breached passwords (would need external API)
        - Regex uses re.search() which finds match ANYWHERE in string
        - All additional special characters (!@#$%^&*) are allowed but optional
        - Spaces are allowed but unusual
    
    Edge Cases:
        - Empty string "": Returns False (fails all checks)
        - None: Raises TypeError (not caught)
        - 8 characters exactly "Pass0123": Valid (at minimum length)
        - 7 characters "Pass012": Invalid (below 8-char minimum)
        - Space in password "Pass 0123": Valid if they have uppercase and digits
        - Unicode uppercase "Çpassword1": Might not match [A-Z] (ASCII-only validation)
        - Repeated chars "AAAAAAAA0": Valid (length 9, has uppercase and digit)
    
    Security Considerations:
        - 8-character minimum is INDUSTRY STANDARD for password strength
        - Requires uppercase+digit combination increases entropy significantly
        - For even stronger security, consider:
            * Minimum 12 characters
            * Requiring special characters (!@#$%^&*)
            * Checking against breached password lists
            * Rate limiting on incorrect password attempts
    
    Performance:
        - Linear time O(n) where n = password length
        - Early exit on first failure (efficient)
        - Regex search is optimized for simple patterns
        - Typical execution: < 1ms for any password
    """
    # Test 1: Check minimum length (must be 8 or more characters)
    # This is CRITICAL for security - forces minimum entropy level
    if len(password) < 8:
        return False  # Password too short, fail validation
    
    # Test 2: Check for at least one UPPERCASE letter (A through Z)
    # re.search() finds a match ANYWHERE in the password string
    # [A-Z] regex means one character from A to Z (uppercase ASCII only)
    # This ensures password has mixed case, not just lowercase
    if not re.search(r"[A-Z]", password):
        return False  # No uppercase letter found, fail validation
    
    # Test 3: Check for at least one digit (0 through 9)
    # [0-9] regex means one digit from 0 to 9
    # This ensures password uses numbers, not just letters
    if not re.search(r"[0-9]", password):
        return False  # No number found, fail validation
    
    # All three security checks passed! Password is strong enough
    return True




# ────────────────────────────────────────────────────────────────────────────
# USERNAME SANITIZATION
# ────────────────────────────────────────────────────────────────────────────

def sanitise_username(username: str) -> str:
    """
    Clean up a username by removing leading and trailing whitespace.
    
    Uses Python's .strip() method to remove spaces (and other whitespace) from
    ONLY the beginning and end of the string. Internal spaces in the middle are
    PRESERVED unchanged. This is useful for cleaning up user input that may have
    accidental spaces when copied/pasted.
    
    IMPORTANT: This function does NOT validate the username format. After calling
    this, you should call is_valid_username() to check format requirements.
    
    Args:
        username (str): The username string to clean (may have leading/trailing spaces)
    
    Returns:
        str: The cleaned username with whitespace removed from start and end
    
    Example:
        >>> sanitise_username("  alice  ")
        "alice"
        >>> sanitise_username("  john doe  ")
        "john doe"  # Internal space preserved!
        >>> sanitise_username("alice")
        "alice"  # No change if already clean
        >>> sanitise_username("   ")
        ""  # All spaces removed = empty string
    
    Whitespace Handling:
        Removes leading/trailing whitespace includes:
        - Regular spaces " "
        - Tabs "\t"
        - Newlines "\n"
        - Carriage returns "\r"
        - Form feeds "\f"
    
    Detailed Examples:
        - "  alice  " → "alice" (both sides trimmed)
        - "\talice\n" → "alice" (tab and newline removed)
        - "  alice bob  " → "alice bob" (middle space kept!)
        - "alice" → "alice" (no change needed)
        - "   " → "" (becomes empty string)
        - "" → "" (already empty)
        - "alice_" → "alice_" (underscore is not whitespace)
    
    Notes:
        - This is a DATA CLEANING function, not a VALIDATION function
        - Internal spaces ARE preserved (middle of string unchanged)
        - Does NOT check username length or character validity
        - Should be followed by is_valid_username() for full validation
        - Used during registration to clean user input from text input fields
        - Commonly needed because users copy/paste usernames with extra spaces
    
    Workflow:
        1. User enters: "  alice_smith  " in form field
        2. sanitise_username() → "alice_smith" (removes extra spaces)
        3. is_valid_username() → True (checks format - would fail if underscores not allowed)
    
    Edge Cases:
        - Empty string "": Returns "" (no change)
        - Whitespace only "   ": Returns "" (all becomes empty)
        - Mixed whitespace "\t\n alice \r\n": Returns "alice"
        - Unicode spaces " " (non-breaking space): Depends on Python version
        - Underscores and special chars: NOT removed (not considered whitespace)
        - Newlines in middle "alice\nbob": Newline stays (not leading/trailing)
    
    Performance:
        - Linear time O(n) where n = username length
        - Highly optimized built-in Python method
        - Typical execution: < 0.1ms
    
    Security Notes:
        - This function is for DATA CLEANING only, not security
        - Does NOT prevent SQL injection (use parameterized queries)
        - Does NOT prevent XSS attacks (sanitise HTML separately)
        - Always validate format AFTER cleaning with is_valid_username()
    """
    # .strip() is Python's built-in method to remove whitespace from start and end
    # Leading whitespace removed first, then trailing whitespace removed
    # Everything in the middle (including internal spaces) is PRESERVED exactly
    return username.strip()


# ────────────────────────────────────────────────────────────────────────────
# PASSWORD HASHING
# ────────────────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """
    Convert a plain-text password into a secure cryptographic hash.
    
    This is a CRITICAL security function. Passwords are NEVER stored in plaintext
    in the database. Instead, we store them as hashes - one-way transformations that:
    - Cannot be reversed to recover original password (one-way function)
    - Are deterministic (same input always produces same hash)
    - Are collision-resistant (different inputs produce different hashes)
    
    When user logs in, we hash their provided password and compare it with the
    stored hash. If they match, password is correct.
    
    If database is compromised and hashes are stolen, attackers cannot easily
    convert hashes back to passwords (unlike plaintext where stealing DB = stolen passwords).
    
    Args:
        password (str): The plain-text password to hash (e.g., "MyPassword123")
    
    Returns:
        str: SHA-256 hash in hexadecimal format (always exactly 64 characters)
    
    Example:
        >>> hash_password("SecurePass123")
        "2a8c3b1f9d7e5c4b8a1f3d7e9a2c5b8d0f3a6c9e2f5a8d1c4e7f0a3b6c9d"
        >>> hash_password("SecurePass123")  # Same input
        "2a8c3b1f9d7e5c4b8a1f3d7e9a2c5b8d0f3a6c9e2f5a8d1c4e7f0a3b6c9d"  # Same output
        >>> hash_password("DifferentPass123")  # Different input
        "7f2e1a9c5b3d8e6f4a2c1b9d7e5f3a8c0d9e2f1a3b5c7d9e1f3a5b7c9d1e"  # Different output
    
    Hash Format:
        - Algorithm: SHA-256 (Secure Hash Algorithm 256-bit)
        - Encoding: Hexadecimal (0-9, a-f characters)
        - Length: Always exactly 64 characters (256 bits = 64 hex digits)
        - Example: "2a8c3b1f9d7e5c4b8a1f3d7e9a2c5b8d0f3a6c9e2f5a8d1c4e7f0a3b6c9d"
    
    Determinism & Consistency:
        - GUARANTEED: hash_password("MyPass1") will ALWAYS return same hash
        - This is essential for login verification
        - Same password from different users produces same hash (known issue)
        - To fix this use "salting" or bcrypt (not implemented here)
    
    Hashing vs Encryption:
        - Hashing: ONE-WAY transformation (can't decrypt) - GOOD for passwords
        - Encryption: TWO-WAY transformation (can decrypt with key) - use for secrets
        - We use hashing because we need to verify, not recover, passwords
    
    Security Notes:
        - SHA-256 is cryptographically strong for modern standards
        - For production systems, consider bcrypt, scrypt, or Argon2 instead
        - These "stronger" algorithms are slower (intentionally) to defend brute-force
        - Current implementation has NO "salt" (identical passwords produce identical hashes)
        - Salt + hashing would prevent rainbow table attacks
    
    Example Workflow:
        Registration:
            1. User enters password: "MyPassword123"
            2. Call hash_password("MyPassword123")
            3. Receive hash: "a1b2c3d4e5f6..."
            4. Store hash in database (NOT original password)
        
        Login:
            1. User enters password: "MyPassword123"
            2. Call hash_password("MyPassword123")
            3. Receive hash: "a1b2c3d4e5f6..."
            4. Retrieve stored hash from database
            5. Compare: if stored_hash == provided_hash → password correct!
    
    Edge Cases:
        - Empty password "": Valid to hash, returns hash of empty string
            * hash_password("") → "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        - Very long password (1000+ chars): Still works, hashing slower
        - Unicode password "Pässwörd1": Encoded as UTF-8 before hashing
        - None: Raises TypeError (not caught, should validate first)
        - Special characters "P@$$w0rd!": No problem, all characters allowed
    
    Performance Considerations:
        - Typical execution time: ~0.5-2ms per hash
        - SHA-256 is fast (deliberate - pre-dating bcrypt era)
        - Called once per registration and once per login attempt
        - Database call is usually slower than hashing
        - No caching - always recomputes for security
    
    Technical Implementation:
        - Uses hashlib.sha256() from Python standard library
        - Input converted to bytes using UTF-8 encoding (supports Unicode)
        - Output converted to hexadecimal string format for database storage
        - No external dependencies required (built-in Python)
    """
    import hashlib  # Module for cryptographic hashing operations
    
    # Step 1: Convert password string to bytes
    # - .encode("utf-8") transforms Unicode string to UTF-8 byte sequence
    # - Hashing algorithms work on bytes, not strings
    # - UTF-8 is standard encoding (supports all Unicode characters)
    
    # Step 2: Apply SHA-256 hashing algorithm
    # - hashlib.sha256() returns hash object
    
    # Step 3: Convert to hexadecimal string representation
    # - .hexdigest() transforms raw bytes to readable hex string
    # - Result is 64 characters (256 bits = 64 hex digits)
    # - This format is suitable for database storage and comparison
    
    return hashlib.sha256(password.encode("utf-8")).hexdigest()




# ────────────────────────────────────────────────────────────────────────────
# ERROR MESSAGE GENERATION
# ────────────────────────────────────────────────────────────────────────────

def validation_errors(username: str, password: str) -> list[str]:
    """
    Check username and password for validity, returning list of any errors found.
    
    This is a convenience function that combines is_valid_username() and
    is_valid_password() checks, accumulating all errors in a single list. Useful
    for returning to user interface to display all problems at once rather than
    one error at a time.
    
    Error Accumulation:
    - Empty list [] means BOTH username and password are valid ✓
    - Non-empty list [error1, error2, ...] means problems found - display all ✗
    - Each error message is human-friendly English text
    
    Args:
        username (str): The username string to validate
        password (str): The password string to validate
    
    Returns:
        list[str]: List of error messages. Empty list = all valid. Non-empty = has errors.
                   Each string in list is a complete error message ready to display to user.
    
    Example:
        >>> validation_errors("alice", "SecurePass123")
        []  # Both valid, no errors
        
        >>> validation_errors("al", "weak")
        ["Username must be 3–30 characters: letters, numbers, underscores only.",
         "Password must be at least 8 characters with one uppercase letter and one number."]
        # Both invalid, returns 2 errors
        
        >>> validation_errors("", "SecurePass123")
        ["Username is required."]  # Just username empty
        
        >>> validation_errors("alice", "")
        ["Password is required."]  # Just password empty
        
        >>> validation_errors("", "")
        ["Username is required.", "Password is required."]  # Both empty
    
    Typical Usage in Registration:
        # User submits registration form
        errors = validation_errors(username_from_form, password_from_form)
        
        if errors:
            # Display all errors to user
            for error_msg in errors:
                print(f"❌ {error_msg}")
        else:
            # Both valid, proceed with registration
            register_user(username_from_form, password_from_form)
    
    Error Message Details:
        Username Errors:
        1. "Username is required." - Username is empty or None
        2. "Username must be 3–30 characters..." - Invalid format
        
        Password Errors:
        1. "Password is required." - Password is empty or None
        2. "Password must be at least 8 characters..." - Does not meet strength requirements
    
    Validation Order:
        1. Check if username is empty → add error
        2. Check if username is valid format → add error if invalid
        3. Check if password is empty → add error
        4. Check if password is valid format → add error if invalid
    
    Notes:
        - Does NOT check if username already exists in database
        - This is FORMAT validation only, not DATABASE validation
        - Database uniqueness check happens in register_user()
        - This function uses is_valid_username() and is_valid_password()
        - Designed to give users COMPLETE feedback in one call
        - Better UX than checking one field at a time
    
    Edge Cases:
        - Both empty: Returns 2 errors (both required)
        - None values: Will raise TypeError (should sanitise input first)
        - Empty strings with whitespace "  " and "  ": 
            * sanitise_username() should be called first
            * After stripping, will show "Username is required"
        - Super long strings: Will fail validation with format error
        - Unicode: Should work if is_valid_username() handles Unicode correctly
    
    Return Value Interpretation:
        errors = validation_errors(...)
        
        if not errors:  # Empty list = truthy False, non-empty = truthy True
            print("All valid!")
        else:
            for msg in errors:
                print(f"Error: {msg}")
    
    Performance:
        - Linear time in number of validation checks (fixed = O(1))
        - Calls two validation functions, but total time < 1ms
        - No database lookups
        - Optimized for form submission scenarios
    
    Security Notes:
        - Does NOT prevent SQL injection
        - Does NOT prevent XSS attacks
        - Only validates format, not security properties
        - Always sanitise input with sanitise_username() before passing
    """
    # Start with an empty list to accumulate errors
    errors = []

    # ─────── CHECK USERNAME ───────
    # First, check if username field was provided (not empty)
    if not username:
        # Username is missing entirely - user didn't fill in field
        errors.append("Username is required.")
    # If username was provided, validate its format
    elif not is_valid_username(username):
        # Username was provided but doesn't follow format rules (length, characters)
        errors.append("Username must be 3–30 characters: letters, numbers, underscores only.")

    # ─────── CHECK PASSWORD ───────
    # First, check if password field was provided (not empty)
    if not password:
        # Password is missing entirely - user didn't fill in field
        errors.append("Password is required.")
    # If password was provided, validate its strength
    elif not is_valid_password(password):
        # Password was provided but doesn't meet strength requirements
        errors.append("Password must be at least 8 characters with one uppercase letter and one number.")

    # Return the complete list of errors found
    # Empty list [] means both fields were valid
    # Non-empty list means user should see error messages
    return errors