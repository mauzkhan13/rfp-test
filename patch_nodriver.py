import nodriver.core.browser as b
import inspect

src = inspect.getfile(b)
print(f"Patching file: {src}")

with open(src, 'r') as f:
    content = f.read()

print(f"Root check found: {'if os.getuid() == 0:' in content}")

content = content.replace(
    'if os.getuid() == 0:',
    'if False:  # patched - allow root'
)

with open(src, 'w') as f:
    f.write(content)

# Verify patch applied
with open(src, 'r') as f:
    verify = f.read()

if 'if False:  # patched - allow root' in verify:
    print('✓ nodriver patched successfully')
else:
    print('✗ patch FAILED - string not found, printing relevant lines:')
    for i, line in enumerate(verify.splitlines()):
        if 'getuid' in line or 'sandbox' in line.lower() or 'root' in line.lower():
            print(f"  Line {i}: {line}")
