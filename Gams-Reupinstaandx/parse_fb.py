import os
from bs4 import BeautifulSoup

def find_upload_buttons():
    if not os.path.exists("fb_upload_dom_after_click2.html"):
        print("fb_upload_dom_after_click2.html not found.")
        return
        
    with open("fb_upload_dom_after_click2.html", "r", encoding="utf-8") as f:
        html = f.read()
        
    soup = BeautifulSoup(html, "html.parser")
    
    inputs = soup.find_all("input", type="file")
    with open("parse_fb_output.txt", "w", encoding="utf-8") as out:
        out.write(f"Tìm thấy {len(inputs)} thẻ input type=file:\n")
        for inp in inputs:
            out.write(f" - {inp.attrs}\n")
            
        out.write("\n---\n")
        
        import re
        texts_to_find = ["Add photo", "Thêm ảnh", "Upload from desktop", "Tải lên từ máy tính"]
        for text in texts_to_find:
            elems = soup.find_all(string=re.compile(text, re.IGNORECASE))
            if elems:
                out.write(f"\nTìm thấy text '{text}':\n")
                for elem in elems:
                    parent = elem.parent
                    ancestor = parent
                    for _ in range(3):
                        if ancestor and ancestor.parent:
                            ancestor = ancestor.parent
                    out.write(f"HTML: {str(ancestor)[:1000]}...\n")

if __name__ == "__main__":
    find_upload_buttons()
