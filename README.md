# FastAPI Server Starter Guide

This guide provides instructions to set up and run a FastAPI server. Follow the steps below to get started.

## Prerequisites

Ensure you have the following installed on your machine:

1. Python 3.8 or higher
2. pip (Python package manager)
3. A virtual environment manager (optional but recommended)

## Setup Instructions

### 1. Set Up a Virtual Environment (Optional but Recommended)

```bash
# Create a virtual environment
$ python -m venv .venv

# Activate the virtual environment
# On Windows:
$ .\env\Scripts\activate

# On macOS/Linux:
$ source env/bin/activate
```

### 2. Install Dependencies

```bash
# Install the required Python packages
$ pip install -r requirements.txt
```

### 4. Configure Environment Variables

1. Locate the `.env.example` file in the project directory.
2. Create a new `.env` file by copying the `.env.example` file:

   ```bash
   $ cp .env.example .env
   ```

3. Open the `.env` file and update the necessary values according to your environment.

### 5. Run the Application

```bash
# Start the FastAPI server
$ fastapi app/main.py
```

The application will be accessible at `http://127.0.0.1:8000` by default.

---

### Testing the API

1. Open your web browser and navigate to `http://127.0.0.1:8000/docs` to access the interactive API documentation (Swagger UI).
2. Alternatively, visit `http://127.0.0.1:8000/redoc` for Redoc documentation.

---

## Notes

- Remember to activate your virtual environment before running any commands.
- Update the `.env` file with accurate values to ensure the application runs correctly.

---

Happy coding!
