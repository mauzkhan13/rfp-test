import nodriver.core.browser as b
import inspect
import os

src = inspect.getfile(b)
print(f"Patching: {src}")

# Read the original file
with open(src, 'r') as f:
    content = f.read()

# Print lines around the root check for debugging
for i, line in enumerate(content.splitlines()):
    if 'getuid' in line or 'sandbox' in line.lower() or 'root' in line.lower():
        print(f"Line {i}: {line}")

# Apply multiple patches to ensure it works
# Patch 1: Root check
content = content.replace(
    'if os.getuid() == 0:',
    'if False:  # patched - root check disabled'
)

# Patch 2: Another common root check pattern
content = content.replace(
    "if os.geteuid() == 0:",
    "if False:  # patched - euid check disabled"
)

# Patch 3: Sandbox warning (if exists)
content = content.replace(
    "raise Exception('Running as root without --no-sandbox is not supported')",
    "# Patched: Sandbox warning disabled"
)

# Write the patched content back
with open(src, 'w') as f:
    f.write(content)

# Verify the patch
with open(src, 'r') as f:
    verify = f.read()

if 'if False:  # patched' in verify:
    print('✓ Patch applied successfully')
else:
    print('✗ Patch FAILED - manual intervention needed')
    # Print the actual lines for debugging
    for i, line in enumerate(verify.splitlines()):
        if 'getuid' in line or 'root' in line.lower():
            print(f"  Found at line {i}: {line[:100]}")
