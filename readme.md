# AI - Text to 3D Model Generator

Convert text descriptions into images and 3D models using AI. This application combines local LLM capabilities with Openfabric's image and 3D model generation services.

## Installation & Setup

### Prerequisites

1. **Install Ollama**

   ```bash
   # Install Ollama from https://ollama.ai/
   # Then pull the LLaMA model
   ollama pull llama3:latest
   ```

2. **Start Ollama Server**

   ```bash
   ollama serve
   ```

3. **Python Environment Setup**

   ```bash
   # Create a virtual environment
   python -m venv venv

   # Activate the environment
   # On macOS/Linux:
   source venv/bin/activate

   # On Windows:
   venv\Scripts\activate


   # Install requirements
   pip install -r requirements.txt
   ```

4. **Run the Application**

   ```bash
   streamlit run app/gui.py
   ```

## Project Structure

```
app/
├── config/               # Configuration files
├── core/                # Core functionality
│   ├── __init__.py
│   ├── remote.py
│   └── stub.py
├── managers/
│   ├── llm_manager.py  # Local LLM interactions
│   ├── memory_manager.py # Memory and storage
│   └── openfabric_manager.py # Openfabric API
├── utils/
│   └── utils.py        # utility functions
├── gui.py             # Streamlit UI
└── main.py

```

## Usage

1. Enter a text prompt describing your desired image
2. Generate the image using the enhanced prompt
3. Convert the generated image to a 3D model
4. Edit and refine your generations as needed
5. Use the sidebar to access history and previous generations
6. Search through your generations to find specific items

## Application Screenshot

![AI Text to 3D Model Generator Interface](screenshot.png)

## Memory System

### Short-Term and Long-Term Memory (Session State and with SQLite Database)

- Reference images and prompts
- Stores all generations with metadata
- Searchable prompt history
- Edit history tracking

## Technical Details

The application uses:

- Streamlit for the UI
- Ollama for local LLM capabilities
- Openfabric SDK and AI services
- SQLite for persistent storage

## Troubleshooting

### Common Issues

1. **ImportError: cannot import name 'has_resource_fields' from 'openfabric_pysdk.helper'**

   This error typically occurs when using Anaconda's Python instead of the virtual environment's Python. To fix:

   ```bash
   # 1. Deactivate any active environments (including conda)
   deactivate
   conda deactivate  # if using conda

   # 2. Create a fresh virtual environment
   python -m venv venv

   # 3. Activate the new environment
   source venv/bin/activate  # on macOS/Linux
   venv\Scripts\activate     # on Windows

   # 4. Install requirements
   pip install -r requirements.txt
   ```

   Verify you're using the correct Python:

   ```bash
   which python  # Should point to your venv, not Anaconda
   ```
