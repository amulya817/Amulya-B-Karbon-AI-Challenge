import pandas as pd
import pdfplumber
import re

def parse(file_path: str) -> pd.DataFrame:
    """
    Parse SBI bank PDF/CSV file and return a DataFrame.
    
    Parameters:
    file_path (str): Path to the PDF/CSV file.
    
    Returns:
    pd.DataFrame: Parsed DataFrame.
    """
    
    # Check if file is a PDF or CSV
    if file_path.endswith('.pdf'):
        # Extract text from PDF
        with pdfplumber.open(file_path) as pdf:
            text = ''
            for page in pdf.pages:
                text += page.extract_text()
        
        # Split text into lines
        lines = text.split('\n')
        
        # Initialize lists to store data
        headers = []
        data = []
        
        # Initialize flag to track header
        is_header = True
        
        # Iterate over lines
        for line in lines:
            # Remove leading/trailing whitespaces and special characters
            line = re.sub(r'\s+', ' ', line).strip()
            line = re.sub(r'[^\w\s\.,-]', '', line)
            
            # If line is not empty
            if line:
                # If it's a header, store it
                if is_header:
                    headers = line.split(' ')
                    is_header = False
                # If it's not a header, store data
                else:
                    data.append(line.split(' '))
        
        # Create DataFrame
        df = pd.DataFrame(data, columns=headers)
        
    elif file_path.endswith(('.csv', '.txt')):
        # Read CSV/Text file
        df = pd.read_csv(file_path)
    
    else:
        raise ValueError("Unsupported file format. Only PDF and CSV are supported.")
    
    # Drop empty rows
    df = df.dropna(how='all')
    
    # Replace NaN in numeric columns with 0.0
    df = df.apply(lambda x: x.fillna(0.0) if x.dtype in ['int64', 'float64'] else x)
    
    # Replace NaN in non-numeric columns with ""
    df = df.apply(lambda x: x.fillna("") if x.dtype in ['object'] else x)
    
    return df