"""
Find and replace all references to postgres in the project.
"""
import os
import glob

def find_references():
    """Find all files containing references to postgres."""
    print("Searching for 'postgres' references...")
    
    # Define search paths
    search_paths = [
        "*.py", 
        "*/*.py",  # Check one level deep
        "*/*/*.py"  # Check two levels deep
    ]
    
    # Store files with matches
    found_files = []
    
    # Search through files
    for pattern in search_paths:
        for file_path in glob.glob(pattern):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if "postgres" in content:
                        found_files.append(file_path)
                        print(f"- Found reference in: {file_path}")
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
    
    if not found_files:
        print("No references found!")
    else:
        print(f"\nFound {len(found_files)} files with 'postgres' references")
        
        replace = input("\nDo you want to replace all references with 'postgres'? (y/n): ")
        if replace.lower() == 'y':
            for file_path in found_files:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Replace references
                    updated = content.replace("postgres", "postgres")
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(updated)
                    
                    print(f"✓ Updated {file_path}")
                except Exception as e:
                    print(f"Error updating {file_path}: {e}")

if __name__ == "__main__":
    find_references()
