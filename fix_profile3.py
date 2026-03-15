import re

with open('templates/profile.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Fix multiline variables without injecting spaces before the closing brackets
html = re.sub(r'\{\{\s*([^\}]+?)\s*\}\}', lambda m: '{{ ' + re.sub(r'\s+', ' ', m.group(1)) + ' }}', html)

# Fix multiline tags without injecting spaces before the closing brackets
html = re.sub(r'\{%\s*([^%]+?)\s*%\}', lambda m: '{% ' + re.sub(r'\s+', ' ', m.group(1)) + ' %}', html)

# Specifically inject the primary_phone check
html = html.replace('{{ profile.phone|default:"UNASSIGNED" }}', '{{ profile.primary_phone|default:profile.phone|default:"UNASSIGNED" }}')

with open('templates/profile.html', 'w', encoding='utf-8') as f:
    f.write(html)
