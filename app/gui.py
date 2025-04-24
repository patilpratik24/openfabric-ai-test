import os
os.environ["NUMEXPR_MAX_THREADS"] = "12"  

import warnings
warnings.filterwarnings("ignore", category=Warning) 

import streamlit as st
from managers.llm_manager import LLMManager
from managers.openfabric_manager import OpenfabricManager
from managers.memory_manager import MemoryManager
from utils.utils import (
    save_binary_to_file, 
    image_to_base64, 
    create_model_viewer_html, 
    setup_logging, 
    format_timestamp,
    show_database_info
)
import logging
from datetime import datetime

st.set_page_config(
    page_title="AI Image to 3D Model Generator",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Setup logging
setup_logging()

# Initialize managers
@st.cache_resource
def init_managers():
    return {
        'llm': LLMManager(),
        'openfabric': OpenfabricManager(),
        'memory': MemoryManager()
    }

managers = init_managers()

# Initialize session state
if 'current_image' not in st.session_state:
    st.session_state.current_image = None
if 'current_model' not in st.session_state:
    st.session_state.current_model = None
if 'enhanced_prompt' not in st.session_state:
    st.session_state.enhanced_prompt = None
if 'reference_prompt' not in st.session_state:
    st.session_state.reference_prompt = None
if 'reference_image' not in st.session_state:
    st.session_state.reference_image = None
if 'reference_id' not in st.session_state:
    st.session_state.reference_id = None
if 'confirm_clear' not in st.session_state:
    st.session_state.confirm_clear = False
if 'show_db_info' not in st.session_state:
    st.session_state.show_db_info = False
if 'current_image_path' not in st.session_state:
    st.session_state.current_image_path = None

# Add custom CSS
st.markdown("""
    <style>
    /* Main container spacing */
    .main .block-container {
        padding: 2rem 1rem !important;
        max-width: 1200px;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        min-width: 400px !important;
        max-width: 300px !important;
        background-color: #1E1E1E;
    }
    [data-testid="stSidebarContent"] {
        padding: 1.5rem 1rem !important;
    }
    
    /* Button styling */
    div[data-testid="stButton"] button {
        background-color: #0E1117 !important;
        border-color: #31333F !important;
        border-radius: 4px !important;
        border-width: 1px !important;
        border-style: solid !important;
        padding: 0.5rem 1rem !important;
        font-size: 14px !important;
        font-weight: 400 !important;
        color: #FAFAFA !important;
        height: 42px !important;
        transition: all 0.2s ease !important;
    }
    
    div[data-testid="stButton"] button:hover {
        border-color: rgb(255, 75, 75) !important;
        color: rgb(255, 75, 75) !important;
    }
    
    /* Fix button width in columns */
    [data-testid="column"] > div > div > div > div > div[data-testid="stButton"] {
        width: 100%;
        min-width: 100%;
    }
    [data-testid="column"] > div > div > div > div > div[data-testid="stButton"] > button {
        width: 100%;
        min-width: 100%;
    }
    
    /* Ensure consistent padding in columns */
    [data-testid="column"] {
        padding: 0 1rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# Create a container for the modal at the top level
modal_placeholder = st.empty()

# Show database info modal if state is True
if st.session_state.show_db_info:
    db_info = managers['memory'].get_database_info()
    show_database_info(
        db_info=db_info,
        on_close=lambda: setattr(st.session_state, 'show_db_info', False)
    )

# Sidebar with search and history
with st.sidebar:
    st.header("Memory & History")
    
    search_query = st.text_input("Search by prompt:", key="search_box")
    
    if search_query:
        results = managers['memory'].search_generations(search_query)
        if results:
            st.write(f"Found {len(results)} results:")
            for idx, result in enumerate(results):
                with st.expander(f"{result['prompt'][:40]}...", expanded=False):
                    st.write("**Original Prompt:**")
                    st.write(result['prompt'])
                    if result['enhanced_prompt']:
                        st.write("**Enhanced Prompt:**")
                        st.write(result['enhanced_prompt'])
                    if result['image_path'] and os.path.exists(result['image_path']):
                        st.image(result['image_path'], use_column_width=True)
                    if result['model_path'] and os.path.exists(result['model_path']):
                        st.download_button(
                            "Download 3D Model",
                            data=open(result['model_path'], 'rb').read(),
                            file_name=os.path.basename(result['model_path']),
                            mime="model/gltf-binary",
                            key=f"download_search_{idx}"
                        )
                    if st.button("📎 Use as Reference", key=f"ref_search_{idx}"):
                        # Store reference data in session state
                        st.session_state.reference_prompt = result['prompt']
                        st.session_state.reference_image = result['image_path']
                        st.session_state.reference_id = result['id']
                        st.session_state.enhanced_prompt = result['enhanced_prompt']
                        # Update current image state
                        if result['image_path'] and os.path.exists(result['image_path']):
                            st.session_state.current_image = open(result['image_path'], 'rb').read()
                            st.session_state.current_image_path = result['image_path']
                        # Update prompt input
                        st.session_state["prompt_input"] = result['prompt']
                        st.rerun()
        else:
            st.info("No matching generations found.")
    
    # Recent generations
    st.subheader("Recent Generations")
    history = managers['memory'].get_generations(limit=10)
    
    if history:
        for idx, gen in enumerate(history):
            with st.container():
                title = gen['prompt'][:30] + "..." if len(gen['prompt']) > 30 else gen['prompt']
                with st.expander(title, expanded=False):
                    # Header row with timestamp and delete button
                    col1, col2 = st.columns([0.92, 0.08])
                    with col1:
                        st.markdown(f"<em>{format_timestamp(gen.get('created_at', 'Unknown'))}</em>", unsafe_allow_html=True)
                    with col2:
                        if st.button("✕", key=f"delete_recent_{idx}", help="Delete this generation", type="secondary", use_container_width=True):
                            if managers['memory'].delete_generation(gen['id']):
                                st.rerun()
                            else:
                                st.error("Failed to delete generation.")
                        st.markdown("""
                            <style>
                            /* Target the specific delete button */
                            div[data-testid="column"]:last-child button {
                                padding: 0 !important;
                                background: none !important;
                                border: none !important;
                                color: #ff4b4b !important;
                                width: 20px !important;
                                height: 20px !important;
                                line-height: 1 !important;
                                font-size: 10px !important;
                                min-height: 0 !important;
                            }
                            div[data-testid="column"]:last-child button:hover {
                                color: #ff0000 !important;
                                background: rgba(255, 0, 0, 0.1) !important;
                            }
                            </style>
                        """, unsafe_allow_html=True)
                    
                    # Show image if available
                    if gen['image_path'] and os.path.exists(gen['image_path']):
                        st.image(gen['image_path'], use_column_width=True)
                    
                    st.markdown('<div class="sidebar-buttons">', unsafe_allow_html=True)
                    
                    # Reference button
                    if st.button("📎 Use as Reference", key=f"ref_recent_{idx}", help="Use as Reference"):
                        # Store reference data in session state
                        st.session_state.reference_prompt = gen['prompt']
                        st.session_state.reference_image = gen['image_path']
                        st.session_state.reference_id = gen['id']
                        st.session_state.enhanced_prompt = gen['enhanced_prompt']
                        st.session_state.current_image = open(gen['image_path'], 'rb').read() if gen['image_path'] and os.path.exists(gen['image_path']) else None
                        st.session_state.current_image_path = gen['image_path']
                        
                        # Update prompt input
                        st.session_state["prompt_input"] = gen['prompt']
                        st.rerun()
                    
                    # Download button if model exists
                    if gen['model_path'] and os.path.exists(gen['model_path']):
                        st.download_button(
                            "Download 3D Model",
                            data=open(gen['model_path'], 'rb').read(),
                            file_name=os.path.basename(gen['model_path']),
                            mime="model/gltf-binary",
                            key=f"download_recent_{idx}",
                            help="Download 3D Model"
                        )
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<hr style="margin: 5px 0;">', unsafe_allow_html=True)
    else:
        st.info("No stored generations")
    
    # Database viewer button
    st.write("")
    if st.button("View Database Info", use_container_width=True):
        st.session_state.show_db_info = True
    
    # Clear All button
    st.write("")
    if st.button("Clear All History", type="secondary", use_container_width=True):
        st.session_state.confirm_clear = True
    
    # Cxonfirmation dialog 
    if st.session_state.confirm_clear:
        st.warning("Are you sure you want to clear all history? This cannot be undone.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, Clear All"):
                try:
                    for item in history:
                        try:
                            if item['image_path'] and os.path.exists(item['image_path']):
                                os.remove(item['image_path'])
                            if item['model_path'] and os.path.exists(item['model_path']):
                                os.remove(item['model_path'])
                        except Exception as e:
                            logging.error(f"Error deleting files: {e}")
                    
                    # Clear database
                    if managers['memory'].clear_database():
                        # Clear session state
                        for key in ['current_image', 'current_model', 'enhanced_prompt', 
                                  'reference_prompt', 'reference_image', 'reference_id']:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.session_state.confirm_clear = False
                        st.success("History cleared successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to clear history. Please try again.")
                except Exception as e:
                    logging.error(f"Error during cleanup: {e}")
                    st.error("Failed to clear history. Please try again.")
        with col2:
            if st.button("No, Cancel"):
                st.session_state.confirm_clear = False
                st.rerun()

st.title("AI - Text to 3D Model Generator")
st.markdown("Transform your text descriptions into images and 3D models using AI")

st.markdown('<div style="padding: 0 1rem;">', unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    # Text to Image section
    st.subheader("Text to Image Generation")
    prompt = st.text_area(
        "Enter your prompt:", 
        height=100,
        key="prompt_input",
        placeholder="Example: A beautiful glowing dragon standing on a cliff at sunset"
    )
    
    # Generation button
    if st.button("Generate Image", key="generate_btn", type="primary", use_container_width=True):
        if prompt:
            try:
                with st.spinner("Enhancing prompt..."):
                    enhanced_prompt = managers['llm'].enhance_prompt(prompt)
                    st.session_state.enhanced_prompt = enhanced_prompt
                
                with st.spinner("Generating image..."):
                    image_data = managers['openfabric'].generate_image(enhanced_prompt)
                    if image_data:
                        # Save image
                        image_path = save_binary_to_file(
                            image_data, 
                            "outputs/images", 
                            "generated", 
                            "png"
                        )
                        if image_path:
                            st.session_state.current_image = image_data
                            st.session_state.current_image_path = image_path  
                            
                            # Save to memory
                            managers['memory'].save_generation(
                                prompt=prompt,
                                enhanced_prompt=enhanced_prompt,
                                image_path=image_path
                            )
                        else:
                            st.error("Failed to save generated image")
                    else:
                        st.error("Failed to generate image")
            except Exception as e:
                logging.error(f"Error in generation pipeline: {e}")
                st.error(f"An error occurred: {str(e)}")
        else:
            st.warning("Please enter a prompt first")
    
    # Enhanced prompt
    if st.session_state.enhanced_prompt:
        with st.expander("✨ Enhanced Prompt", expanded=False):
            st.info(st.session_state.enhanced_prompt)
    
    # Current image
    if st.session_state.current_image:
        image_container = st.empty()
        image_container.image(st.session_state.current_image, caption="Generated Image", use_column_width=True)
        
        # Image editing section
        st.write("✨ Edit your image")
        edit_prompt = st.text_input(
            "Describe what you want to change:",
            placeholder="Example: make it more colorful, add sparkles, change background to night"
        )
        
        if st.button("Update Image", key="update_btn", type="primary", use_container_width=True):
            if edit_prompt:
                try:
                    with st.spinner("Enhancing edit prompt..."):
                        # Get the previous enhanced prompt
                        previous_prompt = st.session_state.enhanced_prompt
                        
                        # Get enhanced edit prompt using LLMManager
                        enhanced_edit_prompt = managers['llm'].enhance_edit_prompt(
                            current_prompt=previous_prompt,
                            edit_request=edit_prompt
                        )
                        st.session_state.enhanced_prompt = enhanced_edit_prompt
                        
                        # Show changes in prompts 
                        with st.expander("View prompt changes", expanded=False):
                            st.write("**Original Prompt:**")
                            st.write(previous_prompt)
                            st.write("**Requested Change:**")
                            st.write(edit_prompt)
                            st.write("**New Enhanced Prompt:**")
                            st.write(enhanced_edit_prompt)
                    
                    with st.spinner("Updating image..."):
                        image_data = managers['openfabric'].generate_image(enhanced_edit_prompt)
                        if image_data:
                            image_path = save_binary_to_file(
                                image_data, 
                                "outputs/images", 
                                "generated", 
                                "png"
                            )
                            if image_path:
                                st.session_state.current_image = image_data
                                st.session_state.current_image_path = image_path
                                
                                image_container.image(image_data, caption="Generated Image", use_column_width=True)
                                
                                # Save to memory with edit context
                                metadata = {
                                    "edit_history": {
                                        "original_prompt": prompt if 'prompt' in locals() else "unknown",
                                        "edit_prompt": edit_prompt,
                                        "previous_enhanced_prompt": previous_prompt,
                                        "timestamp": datetime.now().isoformat()
                                    }
                                }
                                
                                managers['memory'].save_generation(
                                    prompt=edit_prompt,
                                    enhanced_prompt=enhanced_edit_prompt,
                                    image_path=image_path,
                                    metadata=metadata
                                )
                                
                                st.success("Image updated successfully!")
                            else:
                                st.error("Failed to save updated image")
                        else:
                            st.error("Failed to update image")
                except Exception as e:
                    logging.error(f"Error in image update pipeline: {e}")
                    st.error(f"An error occurred: {str(e)}")
            else:
                st.warning("Please describe what changes you want to make")

with col2:
    # Image to 3D section
    st.subheader("Image to 3D Model Generation")
    
    for _ in range(4):
        st.write("")
    
    if st.session_state.current_image is not None:
        if st.button("Convert to 3D Model", key="convert_btn", type="primary", use_container_width=True):
            try:
                with st.spinner("Converting image to 3D model..."):
                    model_data = managers['openfabric'].convert_to_3d(
                        st.session_state.current_image,
                        image_path=st.session_state.current_image_path
                    )
                    if model_data:
                        model_path = save_binary_to_file(
                            model_data.get("model", b""),
                            "outputs/models",
                            "model",
                            "glb"
                        )
                        if model_path:
                            st.session_state.current_model = model_data.get("model", b"")
                            managers['memory'].save_generation(
                                prompt=prompt if 'prompt' in locals() else "",
                                enhanced_prompt=st.session_state.enhanced_prompt,
                                image_path=st.session_state.current_image_path,
                                model_path=model_path
                            )
                            st.success("3D model generated successfully!")
                        else:
                            st.error("Failed to save 3D model")
                    else:
                        st.error("Failed to generate 3D model")
            except Exception as e:
                logging.error(f"Error converting to 3D: {e}")
                st.error(f"An error occurred: {str(e)}")
    else:
        st.write("")
        st.info("Generate an image first to convert it to a 3D model")
        st.write("")
    
    # Display 3D model viewer
    if st.session_state.current_model is not None:
        st.write("")  
        st.write("### 3D Model Preview")
        st.components.v1.html(
            create_model_viewer_html(st.session_state.current_model),
            height=400,
            scrolling=False
        ) 