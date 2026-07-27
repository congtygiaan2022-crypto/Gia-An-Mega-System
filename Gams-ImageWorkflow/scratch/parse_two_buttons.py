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
    div_buttons = soup.find_all("div", attrs={"role": "button"})
    
    out_lines = []
    out_lines.append("Found div buttons containing 'Tiếp tục':")
    count = 0
    for el in div_buttons:
        text = el.get_text().strip()
        if "Tiếp tục" in text or "Continue" in text:
            out_lines.append(f"\n--- Button {count} ---")
            out_lines.append(f"Text: '{text}'")
            out_lines.append(f"Attributes: {el.attrs}")
            # Find parent chain
            parent = el.parent
            parent_chain = []
            while parent and len(parent_chain) < 5:
                parent_chain.append(f"{parent.name} (class={parent.get('class')})")
                parent = parent.parent
            out_lines.append(f"Parent chain: {' -> '.join(parent_chain)}")
            count += 1

    with open("scratch/post_button_result.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines))
    print("Successfully wrote details to scratch/post_button_result.txt")

if __name__ == "__main__":
    main()
