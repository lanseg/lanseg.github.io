name ollama

# Block everything
net none
private
caps.drop all

# Needed for client scripts
include allow-python3.inc

# Allow project-specific directories
whitelist /path/to/ollama/install/   # Ollama binaries (can be anywhere)
whitelist /path/to/work/dir          # Scripts that use ollama to analyze the data (can be anywhere)
whitelist /path/to/models/           # Models (I keep that on a big long term storage)
whitelist /path/to/data/dir          # Data directory (can be anywhere, e.g. on a usb drive)