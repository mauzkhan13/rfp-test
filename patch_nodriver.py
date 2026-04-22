import nodriver.core.browser as b
import inspect

src = inspect.getfile(b)
with open(src, 'r') as f:
    content = f.read()

content = content.replace(
    'if os.getuid() == 0:',
    'if False:  # patched - allow root'
)

with open(src, 'w') as f:
    f.write(content)

print('nodriver patched successfully')
