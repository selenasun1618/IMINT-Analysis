# IMINT-ADA-Analysis

## Setup Instructions

### 1. Install Python dependencies

First, ensure you have Python 3.8 or later installed. Then, install all required packages using pip:

```bash
pip install -r requirements.txt
```

This will install:
- streamlit
- python-dotenv
- plotly
- pandas
- Pillow
- requests

### 2. Set up environment variables

Create a `.env` file in the project root directory with your Mapbox API token:

```
MAPBOX_TOKEN=your_mapbox_token_here
```

### 3. Run the Streamlit app

Start the Streamlit interface with:

```bash
streamlit run yongbyon_ada.py
```

This will launch the web app in your default browser. Use the sidebar to enter nuclear site coordinates, search radius, and map size parameters.

---

If you encounter any issues or missing dependencies, ensure your Python version is compatible and all packages in `requirements.txt` are installed. Or contact me: selenas@stanford.edu.
