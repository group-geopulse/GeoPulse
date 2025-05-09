# GeoPulse Backend Setup

This document provides instructions to set up the backend for the GeoPulse project, install all required dependencies, and run the scripts for data processing and uploading.

## **Prerequisites**

Before setting up the backend, ensure you have the following installed on your system:
1. **Python 3.11.9** (recommended version for compatibility with all dependencies)
2. **pip** (Python package manager)
3. **Git** (optional, for cloning the repository)

## **Setup Instructions**

### **1. Clone the Repository**
If you haven't already, clone the repository to your local machine:
```bash
> git clone https://github.com/group-geopulse/GeoPulse.git
```

Then move to the backend folder:
```bash
> cd GeoPulse/backend
```

### **2. Create a Virtual Environment**

It is recommended to use a virtual environment to isolate dependencies:
```bash
> python -m venv venv
```

Activate the virtual environment:
- On Windows:
    ```bash
    > venv\Scripts\activate
    ```

- On macOS/Linux: 
    ```bash
    > source venv/bin/activate
    ```

### **3. Install Dependencies**

Install all required Python libraries using the [requirements.txt](http://_vscodecontentref_/1) file:
```bash
> pip install -r requirements.txt
```

This will install key dependencies. Additionally, the en_core_web_lg language model for spaCy will also be installed.

Run the following to check PyTorch version:
```bash
> python -c "import torch; print(torch.__version__)"
```

### **4. Set up Environment Variables**

Place the following in a file called .env in the backend folder:

```bash
# MongoDB connection string
MONGO_URI=mongo-uri-goes-here-see-teams_

# API key for external services
API_KEY=api-key-goes-here-see-teams_

# Search engine ID for Google Custom Search
SEARCH_ENGINE_ID=search-engine-id-goes-here-see-teams_

# API request limit
API_REQUEST_LIMIT=100
```

- Replace the placeholders (_mongo-uri-goes-here-see-teams_, etc.) with the actual values provided on Teams.
- Never commit the .env file to version control. Make sure your .gitignore file in the root of your local repository ignores this file.

## **Debugging**

If you encounter any issues:

- Check the log files (upload_price.log and upload_news.log) for detailed error messages.
- Ensure MongoDB is running and accessible.
- Verify that all required environment variables are set correctly.


