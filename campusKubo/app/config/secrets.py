"""
Configuration for secrets and security settings.
"""
import os
import secrets


def generate_secret_key(length: int = 32) -> str:
    """
    Generate a cryptographically secure random secret key.
    This creates a unique key every time the function is called.

    Args:
        length: Length of the key in bytes (default 32 for 256 bits)

    Returns:
        Hexadecimal string representation of the random key
    """
    return secrets.token_hex(length)


def get_or_create_secret_key() -> str:
    """
    Get SECRET_KEY from environment, or generate a new one if not set.
    This ensures a unique secret key for each app run if not explicitly set.
    If the .env file contains the default value, it will be updated with a new key.
    """
    key = os.getenv('SECRET_KEY')
    env_file = os.path.join(os.path.dirname(__file__), '..', 'storage', '.env')

    if not key or key == 'change_me_with_random_value':
        key = generate_secret_key()
        os.environ['SECRET_KEY'] = key

        # Update .env file if it exists and contains the default
        if os.path.exists(env_file):
            try:
                with open(env_file, 'r') as f:
                    content = f.read()

                if 'SECRET_KEY=change_me_with_random_value' in content:
                    new_content = content.replace('SECRET_KEY=change_me_with_random_value', f'SECRET_KEY={key}')
                    with open(env_file, 'w') as f:
                        f.write(new_content)
                    print(f"[secrets] Updated .env with new SECRET_KEY")
                else:
                    print(f"[secrets] Generated new SECRET_KEY (not updating .env as it has custom value)")
            except Exception as e:
                print(f"[secrets] Error updating .env: {e}")
        else:
            print(f"[secrets] Generated new SECRET_KEY: {key[:8]}...")

    return key