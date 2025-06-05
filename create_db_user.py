"""
Create a new PostgreSQL admin user and database for the application.
"""
import os
import sys
import subprocess
import getpass

def create_user_and_db():
    """Create a new PostgreSQL user and database."""
    
    print("=== PostgreSQL New User and Database Setup ===")
    
    # Get credentials
    username = input("Enter new username (default: moneyy_admin): ").strip() or "moneyy_admin"
    password = getpass.getpass("Enter password for new user: ")
    if not password:
        print("Error: Password cannot be empty")
        return False
        
    db_name = input("Enter database name (default: moneyy_trading): ").strip() or "moneyy_trading"
    
    # Platform-specific commands
    if sys.platform.startswith('win'):
        # Windows - using psql command line
        try:
            # Create user
            create_user_cmd = f'createuser -s {username}'
            subprocess.run(create_user_cmd, shell=True, check=True)
            
            # Set password (needs psql)
            set_pwd_cmd = f'psql -c "ALTER USER {username} WITH PASSWORD \'{password}\';" postgres'
            subprocess.run(set_pwd_cmd, shell=True, check=True)
            
            # Create database
            create_db_cmd = f'createdb -U {username} {db_name}'
            subprocess.run(create_db_cmd, shell=True, check=True)
            
        except subprocess.CalledProcessError as e:
            print(f"Command execution failed: {e}")
            print("Note: Make sure PostgreSQL bin directory is in your PATH")
            return False
    else:
        # Linux/Mac - using sudo -u postgres
        try:
            # Create user
            create_user_cmd = f'sudo -u postgres createuser -s {username}'
            subprocess.run(create_user_cmd, shell=True, check=True)
            
            # Set password
            set_pwd_cmd = f'sudo -u postgres psql -c "ALTER USER {username} WITH PASSWORD \'{password}\';"'
            subprocess.run(set_pwd_cmd, shell=True, check=True)
            
            # Create database
            create_db_cmd = f'sudo -u postgres createdb -O {username} {db_name}'
            subprocess.run(create_db_cmd, shell=True, check=True)
            
        except subprocess.CalledProcessError as e:
            print(f"Command execution failed: {e}")
            return False
    
    # Create/update .env file with new credentials
    env_content = f"""DATABASE_URL=postgresql://{username}:{password}@localhost/{db_name}
DEBUG=True
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print(f"\nSuccess! Created:")
    print(f"- User: {username}")
    print(f"- Database: {db_name}")
    print(f"- Updated .env file with connection info")
    
    print("\nYou can now connect to your database with these credentials.")
    return True

if __name__ == "__main__":
    create_user_and_db()
