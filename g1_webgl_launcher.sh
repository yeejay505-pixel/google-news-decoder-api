#!/bin/sh
set -eu
src=/app/ax_browser_broker/browser_pool/bin/launch_chrome.sh
dst=/tmp/g1_launch_chrome_webgl.sh
python - "$src" "$dst" <<'PY'
from pathlib import Path
import sys
src=Path(sys.argv[1]).read_text()
needle='    --disable-gpu \\\n'
assert src.count(needle)==1, "Upstream launcher changed; refuse to patch"
src=src.replace(needle, '    --enable-webgl \\\n    --use-gl=angle \\\n    --use-angle=swiftshader \\\n    --enable-unsafe-swiftshader \\\n',1)
Path(sys.argv[2]).write_text(src)
PY
exec bash "$dst" "$@"
