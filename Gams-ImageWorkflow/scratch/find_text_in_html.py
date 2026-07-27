import sys
import os
from bs4 import BeautifulSoup

def main():
    filepath = "scratch/checkpoint_frame_before.html"
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
        
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()
        
    soup = BeautifulSoup(html, "html.parser")
    
    out_lines = []
    
    # We look for any element containing the text "Ứng dụng xác thực" or "Authentication app"
    # Note: text can be split or contain extra spaces, so we search with a custom function
    def contains_auth_text(tag):
        if not tag.name:
            return False
        # We only want leaf elements or elements whose direct text child matches
        text = tag.get_text().strip()
        return "Ứng dụng xác thực" in text or "Authentication app" in text or "Authenticator app" in text
        
    matching_tags = soup.find_all(contains_auth_text)
    out_lines.append(f"Found {len(matching_tags)} tags containing auth text:")
    
    for idx, tag in enumerate(matching_tags):
        # Only print if it's a leaf node or has short length to avoid printing the whole body
        if len(str(tag)) < 2000:
            out_lines.append(f"\n--- Match {idx} ---")
            out_lines.append(f"Tag: {tag.name}")
            out_lines.append(f"Attributes: {tag.attrs}")
            out_lines.append(f"Text: '{tag.get_text().strip()}'")
            out_lines.append(f"OuterHTML: {str(tag)[:500]}")
            
    with open("scratch/find_text_result.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines))
    print("Search completed. Results written to scratch/find_text_result.txt")

if __name__ == "__main__":
    main()
