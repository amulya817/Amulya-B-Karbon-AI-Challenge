import pandas as pd
import pdfplumber
import re

def parse(file_path: str) -> pd.DataFrame:
    """
    Parse ICICI bank PDF/CSV file and return a pandas DataFrame.
    
    Parameters:
    file_path (str): Path to the PDF/CSV file.
    
    Returns:
    pd.DataFrame: A pandas DataFrame containing the parsed data.
    """
    
    # Check if the file is a PDF or CSV
    if file_path.endswith('.pdf'):
        # Extract text from PDF using pdfplumber
        with pdfplumber.open(file_path) as pdf:
            text = ''
            for page in pdf.pages:
                text += page.extract_text()
        
        # Split text into rows
        rows = re.split(r'\n\s*\n', text)
        
        # Remove empty rows
        rows = [row for row in rows if row.strip()]
        
        # Split rows into columns
        columns = rows[0].split('\t')
        data = [row.split('\t') for row in rows[1:]]
        
        # Create DataFrame
        df = pd.DataFrame(data, columns=columns)
        
    elif file_path.endswith('.csv'):
        # Read CSV file directly
        df = pd.read_csv(file_path)
    
    else:
        raise ValueError("Unsupported file format. Only PDF and CSV are supported.")
    
    # Handle repeated headers
    df.columns = df.columns.astype(str)
    df.columns = df.columns.str.strip()
    df.columns = df.columns.str.replace('\n', ' ')
    df.columns = df.columns.str.replace('\t', ' ')
    df.columns = df.columns.str.strip()
    
    # Remove empty rows
    df = df.dropna(how='all')
    
    # Replace NaN in numeric columns with 0.0
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    df[numeric_cols] = df[numeric_cols].fillna(0.0)
    
    # Replace NaN in string columns with ""
    string_cols = df.select_dtypes(include=['object']).columns
    df[string_cols] = df[string_cols].fillna("")
    
    return df