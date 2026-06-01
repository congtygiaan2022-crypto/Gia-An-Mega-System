import re

with open('fb_upload_dom_after_click.html', 'r', encoding='utf-8') as f:
    html = f.read()

print("Occurrences of type='file':", len(re.findall(r'type=["\']file["\']', html, re.IGNORECASE)))
print("Occurrences of input:", len(re.findall(r'<input', html, re.IGNORECASE)))

# Print all inputs found
for m in re.finditer(r'<input[^>]*>', html, re.IGNORECASE):
    print("Found input tag:", m.group(0))
