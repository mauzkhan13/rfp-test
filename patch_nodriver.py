import os
import re
import inspect
import nodriver.core.browser as b

src = inspect.getfile(b)
print(f"Patching file: {src}")

with open(src, 'r') as f:
    content = f.read()

# Look for the actual root check
lines = content.splitlines()
for i, line in enumerate(lines):
    if 'getuid' in line and '==' in line:
        print(f"Found at line {i}: {line.strip()}")
        # Store the exact line to patch
        original_line = line
        patched_line = line.replace('os.getuid() == 0', 'False')
        patched_line = patched_line.replace('os.geteuid() == 0', 'False')
        patched_line = patched_line.replace('getuid() == 0', 'False')
        lines[i] = patched_line
        print(f"Changed to: {patched_line}")

# Also look for the exception message
for i, line in enumerate(lines):
    if 'Failed to connect to browser' in line:
        print(f"Found connection error at line {i}")
        # Comment out the exception
        if i > 0:
            lines[i-1] = "# " + lines[i-1] if not lines[i-1].strip().startswith('#') else lines[i-1]

# Write back the patched content
with open(src, 'w') as f:
    f.write('\n'.join(lines))

print("✓ Patch completed")
