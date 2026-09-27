import os
import shutil
from pathlib import Path

# Get the current directory
current_dir = Path.cwd()

# Source and target paths
source_schema = current_dir / "tests" / "data" / "schema.bin"
target_dir = current_dir / "src" / "shotgrid_mcp_server" / "data"
target_schema = target_dir / "schema.bin"

# Ensure target directory exists
os.makedirs(target_dir, exist_ok=True)

# Copy the file
print(f"Copying {source_schema} to {target_schema}")
shutil.copy2(source_schema, target_schema)
print(f"File copied successfully: {os.path.exists(target_schema)}")

# List files in target directory
print(f"Files in {target_dir}:")
for file in os.listdir(target_dir):
    print(f"  {file}")
