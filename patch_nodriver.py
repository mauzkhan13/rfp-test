import nodriver.core.browser as b
import inspect
import os

src = inspect.getfile(b)

with open(src, 'r') as f:
    content = f.read()

# Patch root check
content = content.replace(
    'if os.getuid() == 0:',
    'if False:  # patched'
)

content = content.replace(
    "if os.geteuid() == 0:",
    "if False:  # patched"
)

with open(src, 'w') as f:
    f.write(content)

print('✓ Patch applied successfully')
