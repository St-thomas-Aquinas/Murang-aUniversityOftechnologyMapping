# main.py
"""
Campus Room Finder - Main Application Entry Point

This is the main entry point for the campus room finder application.
Run this file with: streamlit run main.py

The application architecture:
- campus_data_logic.py: Contains all business logic, data models, and utility functions
- campus_ui_components.py: Contains all UI components and map visualization logic  
- main.py: Application entry point and orchestration
"""

from campus_ui_components import main

if __name__ == "__main__":
    main()
