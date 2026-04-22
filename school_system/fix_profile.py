import re

with open('templates/profile.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Fix multiline variables
html = re.sub(r'\{\{\s*([^\}]+?)\s*\}\}', lambda m: '{{ ' + re.sub(r'\s+', ' ', m.group(1)) + ' }}', html)

# Fix multiline tags
html = re.sub(r'\{%\s*([^%]+?)\s*%\}', lambda m: '{% ' + re.sub(r'\s+', ' ', m.group(1)) + ' %}', html)

with open('templates/profile.html', 'w', encoding='utf-8') as f:
    f.write(html)
