import nodriver.core.browser as b
import inspect

src = inspect.getfile(b)
print(f"Patching: {src}")

with open(src, 'r') as f:
    content = f.read()

# Print lines around the root check
for i, line in enumerate(content.splitlines()):
    if 'getuid' in line or 'sandbox' in line.lower() or 'root' in line.lower():
        print(f"Line {i}: {line}")

# Apply patch
content = content.replace(
    'if os.getuid() == 0:',
    'if False:  # patched'
)

with open(src, 'w') as f:
    f.write(content)

# Verify
with open(src, 'r') as f:
    verify = f.read()

if 'if False:  # patched' in verify:
    print('✓ Patch applied successfully')
else:
    print('✗ Patch FAILED - trying alternative strings...')
    # Print all lines with conditions near sandbox/root
    for i, line in enumerate(content.splitlines()):
        if 'uid' in line.lower() or 'root' in line.lower():
            print(f"  Line {i}: '{line}'")
