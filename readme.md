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

## Features

- Text to Image Generation
- Image to 3D Model Conversion
- Enhanced Prompt Engineering
- Searchable Generation History
- Reference-based Generation
- Image Editing Capabilities
- 3D Model Preview
- Database Management Interface

## Memory System

### Short-Term Memory (Session State and with SQLite Database)

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

## Usage

1. Enter a text prompt describing your desired image
2. Generate the image using the enhanced prompt
3. Convert the generated image to a 3D model
4. Edit and refine your generations as needed
5. Use the sidebar to access history and previous generations
6. Search through your generations to find specific items
