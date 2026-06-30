import sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open('google_ai_dom.html', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Find ms-image-message or any image-related tags
img_related = re.findall(r'<(ms-image[^>]{0,50}|[a-z-]*image-message[^>]{0,50})>', content)
print('Image-related tags:', img_related[:10])

# Search within model turns for image data
model_content = re.findall(r'class="chat-turn-container[^"]*model[^"]*".*?(?=<ms-chat-turn|$)', content, re.DOTALL)
for i, mc in enumerate(model_content):
    imgs = re.findall(r'<img[^>]*>', mc)
    print(f'\nModel turn {i+1} imgs:', imgs[:3])
    blobs = re.findall(r'(blob:[^\"\s]+|data:image[^\"\s]+)', mc[:5000])
    print(f'Model turn {i+1} data URLs:', blobs[:3])
    # Find any src attributes
    srcs = re.findall(r'src="([^"]{0,150})"', mc[:5000])
    print(f'Model turn {i+1} src attrs:', srcs[:5])
