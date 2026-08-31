import sys
import zipfile
from pathlib import Path

wheel = Path(sys.argv[1])
assert wheel.name == "engcalc_colab-0.9.1-py3-none-any.whl", wheel

with zipfile.ZipFile(wheel) as archive:
    metadata_names = [
        name for name in archive.namelist()
        if name.endswith(".dist-info/METADATA")
    ]
    assert len(metadata_names) == 1, metadata_names
    metadata = archive.read(metadata_names[0]).decode("utf-8")

assert "\nVersion: 0.9.1\n" in "\n" + metadata, metadata
print("WHEEL_METADATA_VERSION=0.9.1")
