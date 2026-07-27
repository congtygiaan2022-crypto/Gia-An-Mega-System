import sys
import os
import re
from bs4 import BeautifulSoup

def main():
    filepath = "scratch/checkpoint_frame_after.html"
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
        
    print(f"Reading and parsing {filepath}...")
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()
        
    soup = BeautifulSoup(html, "html.parser")
    
    out_lines = []
    
    out_lines.append("\n=== INPUT ELEMENTS ===")
    for idx, el in enumerate(soup.find_all("input")):
        out_lines.append(f"Input {idx}: type='{el.get('type')}', name='{el.get('name')}', id='{el.get('id')}', value='{el.get('value')}', outerHTML='{str(el)[:200]}'")
        
    out_lines.append("\n=== BUTTON ELEMENTS ===")
    for idx, el in enumerate(soup.find_all("button")):
        out_lines.append(f"Button {idx}: id='{el.get('id')}', name='{el.get('name')}', type='{el.get('type')}', text='{el.get_text().strip()}', outerHTML='{str(el)[:200]}'")
        
    out_lines.append("\n=== DIV ROLE=BUTTON ELEMENTS ===")
    for idx, el in enumerate(soup.find_all("div", attrs={"role": "button"})):
        out_lines.append(f"DivButton {idx}: id='{el.get('id')}', class='{el.get('class')}', text='{el.get_text().strip()}', outerHTML='{str(el)[:400]}'")
        
    out_lines.append("\n=== ROLE=RADIO ELEMENTS ===")
    for idx, el in enumerate(soup.find_all(attrs={"role": "radio"})):
        out_lines.append(f"Radio {idx}: text='{el.get_text().strip()}', outerHTML='{str(el)[:400]}'")
        
    out_lines.append("\n=== ALL SPAN ELEMENTS containing text ===")
    for idx, el in enumerate(soup.find_all("span")):
        text = el.get_text().strip()
        if text:
            out_lines.append(f"Span {idx}: text='{text}', outerHTML='{str(el)[:150]}'")

    with open("scratch/dang_button_detail.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines))
    print("Parsed DOM details written to scratch/dang_button_detail.txt")

if __name__ == "__main__":
    main()
