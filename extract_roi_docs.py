#!/usr/bin/env python3
"""
Extract text from ROI documents for analysis
"""

import os
import PyPDF2
from zipfile import ZipFile
import xml.etree.ElementTree as ET

def extract_pdf_text(pdf_path):
    """Extract text from PDF file"""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
    return text

def extract_docx_text(docx_path):
    """Extract text from DOCX file"""
    text = ""
    try:
        with ZipFile(docx_path) as zip_file:
            with zip_file.open('word/document.xml') as xml_file:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                # Define namespace
                ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                
                # Extract text from all text elements
                for t in root.iter():
                    if t.tag.endswith('}t'):
                        if t.text:
                            text += t.text
                    elif t.tag.endswith('}br'):
                        text += '\n'
                    elif t.tag.endswith('}p'):
                        text += '\n'
    except Exception as e:
        print(f"Error reading DOCX {docx_path}: {e}")
    return text

def main():
    roi_docs_dir = "/Users/devingreenwell/Desktop/Devin/Projects/IOAgent/ROI_Docs"
    output_dir = "/Users/devingreenwell/Desktop/Devin/Projects/IOAgent/ROI_Docs_Text"
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Process each file in ROI_Docs
    for filename in os.listdir(roi_docs_dir):
        file_path = os.path.join(roi_docs_dir, filename)
        
        if filename.endswith('.pdf'):
            print(f"Extracting text from {filename}...")
            text = extract_pdf_text(file_path)
            output_file = os.path.join(output_dir, filename.replace('.pdf', '.txt'))
            
        elif filename.endswith('.docx'):
            print(f"Extracting text from {filename}...")
            text = extract_docx_text(file_path)
            output_file = os.path.join(output_dir, filename.replace('.docx', '.txt'))
            
        else:
            continue
            
        # Save extracted text
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)
        
        print(f"Saved extracted text to {output_file}")
        print(f"Text length: {len(text)} characters\n")

if __name__ == "__main__":
    main()