import os.path
from pathlib import Path

WORDS = b"self None True False and as assert break class continue def del elif else except finally for from global if import in is lambda nonlocal not or pass raise return try while with yield"

ROOT_PATH = Path(os.path.dirname(os.path.dirname(__file__)))
IMG_PATH = ROOT_PATH / 'SRC' / 'IMG'
