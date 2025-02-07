# Project Name: CASISS IA Proof of Concept

## Description
The proof of concept of the projet CASISS IA. This project provides a web interface for managing database entries. It includes functionality to detect duplicate entries, add new entries, or replace existing ones.

## Features
- Data import/export from Excel and CSV files.
- Add new entries via text input or file upload
- Detect and resolve duplicate entries
- Replace existing entries or add them as new

## Technologies Used
- **Frontend**: React, Bootstrap
- **Backend**: Flask, PostgreSQL
- **APIs**: OpenAI GPT for text processing

## Requirements
- Python 3.8+
- PostgreSQL
- Laravel 10.x
- Composer
- Node.js
- Jupyter Notebook

## Installation

### Clone the repository
   ```bash
   git clone https://github.com/your-username/casiss-ia.git
   cd casiss-ia
   ```

### Python Setup for CSV Import:
1. Navigate to the `scripts/` folder:
    ```bash
   cd scripts
    ```
2. Install Python dependencies:
    ```bash
    pip install pandas sqlalchemy psycopg2
    ```
3. Run the CSV import script:
   ```bash
    python init_database.py
    ```

### Backend Setup (Flask):
1. Navigate to the `backend_flask/` folder:
    ```bash
   cd backend_flask
    ```
2. Install dependencies:
    ```bash
    pip install
    ```
3. Copy the `.env` file:
   ```bash
    cp .env.example .env
    ```
4. Start the backend server:
    ```.bash
    python app.py
    ```

### Backend Setup:
1. Navigate to the `fontend/` folder:
    ```bash
   cd frontend
    ```
2. Install npm dependencies:
    ```bash
    npm install
    ```
3. Start the frontend:
   ```bash
    npm start
    ```

## Usage
- Load and preprocess data using the provided scripts.
- View and manage data through the frontend
- Generate embeddings and structured outputs using Python scripts.

## Contribution
Feel free to fork the repository and submit pull requests!

## License
MIT License

Copyright (c) 2024 CASISS IA

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
