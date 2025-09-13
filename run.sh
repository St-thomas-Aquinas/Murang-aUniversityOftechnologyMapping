#!/bin/bash

source venv/bin/activate 
pip install -r campus-room-finder/requirements.txt 
streamlit run campus-room-finder/streamlit_app.py 