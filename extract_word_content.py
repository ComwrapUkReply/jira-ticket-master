#!/usr/bin/env python3
"""
Enhanced Word document parser that extracts both text and images
"""
import docx
import os
import base64
from docx.document import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph
from PIL import Image
import io

def create_images_folder():
    """Create a folder to store extracted images"""
    images_folder = "extracted_images"
    if not os.path.exists(images_folder):
        os.makedirs(images_folder)
    return images_folder

def extract_images_from_docx(docx_path):
    """Extract all images from a Word document"""
    doc = docx.Document(docx_path)
    images_folder = create_images_folder()
    extracted_images = []
    
    # Get all image relationships
    for rel in doc.part.rels.values():
        if "image" in rel.target_ref:
            try:
                # Get image data
                image_data = rel.target_part.blob
                
                # Determine file extension
                content_type = rel.target_part.content_type
                if 'png' in content_type:
                    ext = '.png'
                elif 'jpeg' in content_type or 'jpg' in content_type:
                    ext = '.jpg'
                elif 'gif' in content_type:
                    ext = '.gif'
                else:
                    ext = '.png'  # Default
                
                # Save image
                image_filename = f"image_{len(extracted_images) + 1}{ext}"
                image_path = os.path.join(images_folder, image_filename)
                
                with open(image_path, 'wb') as img_file:
                    img_file.write(image_data)
                
                extracted_images.append({
                    'filename': image_filename,
                    'path': image_path,
                    'size': len(image_data)
                })
                
                print(f"📸 Extracted image: {image_filename} ({len(image_data)} bytes)")
                
            except Exception as e:
                print(f"⚠️  Could not extract image: {e}")
    
    return extracted_images

def get_enhanced_text_with_images(filename):
    """Extract text and identify image locations in the document"""
    doc = docx.Document(filename)
    images_folder = create_images_folder()
    
    # Extract images first
    extracted_images = extract_images_from_docx(filename)
    
    content_blocks = []
    image_counter = 0
    
    # Process document elements in order
    for element in doc.element.body:
        if isinstance(element, CT_P):
            # This is a paragraph
            paragraph = Paragraph(element, doc)
            text = paragraph.text.strip()
            
            # Check if paragraph contains images
            has_images = False
            for run in paragraph.runs:
                if run.element.xpath('.//a:blip'):
                    has_images = True
                    image_counter += 1
                    
            if text:
                content_blocks.append({
                    'type': 'text',
                    'content': text,
                    'has_image': has_images,
                    'image_ref': f"image_{image_counter}" if has_images else None
                })
            elif has_images:
                content_blocks.append({
                    'type': 'image_only',
                    'content': f"[Image {image_counter}]",
                    'has_image': True,
                    'image_ref': f"image_{image_counter}"
                })
                
        elif isinstance(element, CT_Tbl):
            # This is a table - extract text from it
            table = Table(element, doc)
            table_text = []
            for row in table.rows:
                row_text = []
                for cell in row.cells:
                    row_text.append(cell.text.strip())
                if any(row_text):  # Only add non-empty rows
                    table_text.append(" | ".join(row_text))
            
            if table_text:
                content_blocks.append({
                    'type': 'table',
                    'content': "\\n".join(table_text),
                    'has_image': False,
                    'image_ref': None
                })
    
    return content_blocks, extracted_images

def parse_enhanced_issues(content_blocks, extracted_images):
    """Parse content blocks into structured issues with image references"""
    issues = []
    current_issue = None
    
    for block in content_blocks:
        content = block['content']
        
        # Skip empty content
        if not content.strip():
            continue
            
        # Determine if this starts a new issue (heuristic)
        is_new_issue = (
            len(content) > 20 and  # Substantial content
            not content.startswith(('•', '-', '◦')) and  # Not a bullet point
            ('website' in content.lower() or 
             'issue' in content.lower() or
             'problem' in content.lower() or
             'error' in content.lower() or
             content.endswith(':') or
             len(issues) == 0)  # First issue
        )
        
        if is_new_issue or current_issue is None:
            # Start new issue
            if current_issue:
                issues.append(current_issue)
            
            current_issue = {
                'title': content[:100] + ('...' if len(content) > 100 else ''),
                'description_parts': [content],
                'images': []
            }
        else:
            # Add to current issue
            if current_issue:
                current_issue['description_parts'].append(content)
        
        # Add image reference if present
        if block['has_image'] and block['image_ref']:
            image_info = next((img for img in extracted_images if block['image_ref'] in img['filename']), None)
            if image_info and current_issue:
                current_issue['images'].append(image_info)
    
    # Add the last issue
    if current_issue:
        issues.append(current_issue)
    
    # Format final issues
    formatted_issues = []
    for issue in issues:
        description = "\\n\\n".join(issue['description_parts'])
        
        # Add image references to description
        if issue['images']:
            description += "\\n\\n📸 **Attached Images:**\\n"
            for img in issue['images']:
                description += f"- {img['filename']} ({img['size']} bytes)\\n"
        
        formatted_issues.append({
            'title': issue['title'],
            'description': description,
            'images': issue['images']
        })
    
    return formatted_issues

def test_extraction():
    """Test the enhanced extraction on your Word document"""
    filename = 'Changes to the HC website AT.docx'
    
    print("🔍 Testing enhanced Word document extraction...")
    print("=" * 60)
    
    try:
        # Extract content and images
        content_blocks, extracted_images = get_enhanced_text_with_images(filename)
        
        print(f"📄 Found {len(content_blocks)} content blocks")
        print(f"📸 Extracted {len(extracted_images)} images")
        print()
        
        # Parse into issues
        issues = parse_enhanced_issues(content_blocks, extracted_images)
        
        print(f"🎫 Parsed {len(issues)} issues:")
        print("=" * 60)
        
        for i, issue in enumerate(issues, 1):
            print(f"\\n--- ISSUE {i} ---")
            print(f"📝 Title: {issue['title']}")
            print(f"📄 Description: {issue['description'][:200]}...")
            if issue['images']:
                print(f"📸 Images: {len(issue['images'])} attached")
                for img in issue['images']:
                    print(f"   • {img['filename']}")
            print()
        
        return issues, extracted_images
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return [], []

if __name__ == "__main__":
    test_extraction() 