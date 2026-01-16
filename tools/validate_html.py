import argparse
import os
from bs4 import BeautifulSoup

def validate_file(filepath):
    print(f"Validating: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    ids = set()
    errors = []

    # Check Duplicate IDs
    for tag in soup.find_all(True):
        if tag.has_attr('id'):
            tag_id = tag['id']
            if tag_id in ids:
                errors.append(f"Duplicate ID found: {tag_id}")
            ids.add(tag_id)

    # Check Broken Internal Links
    for a in soup.find_all('a'):
        href = a.get('href')
        if href and href.startswith('#') and len(href) > 1:
            target_id = href[1:]
            if target_id not in ids:
                errors.append(f"Broken internal link: {href} (ID '{target_id}' not found)")

    if errors:
        print(f"FAILED: {filepath}")
        for err in errors:
            print(f"  - {err}")
        return False
    else:
        print(f"PASSED: {filepath}")
        return True

def main():
    parser = argparse.ArgumentParser(description="Validate HTML files for ID uniqueness and broken internal links.")
    parser.add_argument('files', nargs='+', help='Files to validate')
    args = parser.parse_args()

    success_count = 0
    failure_count = 0

    for file in args.files:
        if os.path.isdir(file):
            for root, dirs, filenames in os.walk(file):
                for f in filenames:
                    if f.endswith('.html'):
                        if validate_file(os.path.join(root, f)):
                            success_count += 1
                        else:
                            failure_count += 1
        elif os.path.exists(file):
             if validate_file(file):
                 success_count += 1
             else:
                 failure_count += 1
        else:
            print(f"File not found: {file}")

    print(f"\nSummary: {success_count} Passed, {failure_count} Failed.")

if __name__ == "__main__":
    main()
