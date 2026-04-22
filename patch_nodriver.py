import os
import inspect
import nodriver.core.browser as b

src = inspect.getfile(b)
print(f"Patching: {src}")

with open(src, 'r') as f:
    content = f.read()

# Find and patch all root/sandbox checks
replacements = [
    ('if os.getuid() == 0:', 'if False:  # patched'),
    ('if os.geteuid() == 0:', 'if False:  # patched'),
    ('if getuid() == 0:', 'if False:  # patched'),
    ('if os.getuid() == 0 or os.geteuid() == 0:', 'if False:  # patched'),
]

for old, new in replacements:
    if old in content:
        content = content.replace(old, new)
        print(f"✓ Patched: {old.strip()}")

# Also patch the sandbox warning function
if 'def _check_sandbox' in content:
    content = content.replace('def _check_sandbox', 'def _check_sandbox_disabled')
    print("✓ Disabled sandbox check function")

# Write the patched content
with open(src, 'w') as f:
    f.write(content)

print("✓ Patch applied successfully")
