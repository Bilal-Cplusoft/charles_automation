# Automated Bet Creation - Admin Dashboard

This repository contains the Dockerized Streamlit Admin Dashboard for creating automated sports square boards.

## Setup & Running

1. **Service Account JSON:** 
   Place your Google Cloud Service Account JSON file (e.g., `cosmic-heaven-506712-e4-e652026d0682.json`) directly into this directory.

2. **Environment Variable Configuration:**
   If your JSON file has a different name, edit the `.env` file (which generates automatically from `.env.example`).
   ```env
   GCP_KEY=your_key_file.json
   ```

3. **Start the Application:**
   Run the setup bash script which automatically wraps and executes docker build & run mechanisms.
   ```bash
   chmod +x run.sh
   ./run.sh
   ```

4. **Access the Application:**
   Open a browser and navigate to:
   ```
   http://localhost:8501
   ```

Press `Ctrl+C` in your terminal to automatically stop the application and clean up docker processes and images.
