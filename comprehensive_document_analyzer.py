#!/usr/bin/env python3
"""
Comprehensive Document Analyzer - Extracts ALL content types and provides intelligent categorization
Supports: Text, Images, Tables, Links, Videos, Headings, Lists with AI-powered categorization
"""

import docx
import os
import json
import re
from docx.document import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph
from docx.shared import Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import base64
from urllib.parse import urlparse

# Import AI analyzer if available
try:
    from ai_document_analyzer import AIDocumentAnalyzer
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

# Import image extraction
try:
    from extract_word_content import extract_images_from_docx, create_images_folder
    IMAGE_EXTRACTION_AVAILABLE = True
except ImportError:
    IMAGE_EXTRACTION_AVAILABLE = False

class ComprehensiveDocumentAnalyzer:
    """Advanced document analyzer that extracts ALL content types with intelligent categorization."""
    
    def __init__(self):
        """Initialize the comprehensive analyzer."""
        self.ai_analyzer = AIDocumentAnalyzer() if AI_AVAILABLE else None
        self.content_blocks = []
        self.extracted_images = []
        self.extracted_tables = []
        self.extracted_links = []
        self.extracted_videos = []
        self.document_structure = []
        
    def is_ai_available(self):
        """Check if AI analysis is available."""
        return self.ai_analyzer and self.ai_analyzer.is_available()
    
    def extract_hyperlinks_from_paragraph(self, paragraph):
        """Extract all hyperlinks from a paragraph."""
        links = []
        
        # Method 1: Check for hyperlink elements in runs
        for run in paragraph.runs:
            # Check if run is part of a hyperlink
            hyperlink_elem = None
            current_elem = run.element
            
            # Traverse up to find hyperlink element
            while current_elem is not None:
                if current_elem.tag.endswith('hyperlink'):
                    hyperlink_elem = current_elem
                    break
                current_elem = current_elem.getparent()
            
            if hyperlink_elem is not None:
                # Extract relationship ID
                r_id = hyperlink_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
                if r_id and hasattr(paragraph.part, 'rels') and r_id in paragraph.part.rels:
                    try:
                        url = paragraph.part.rels[r_id].target_ref
                        text = run.text or hyperlink_elem.text or "Link"
                        links.append({
                            'text': text.strip(),
                            'url': url,
                            'type': self.classify_link_type(url)
                        })
                    except (KeyError, AttributeError):
                        # Relationship not found or invalid
                        pass
        
        # Method 2: Look for URL patterns in text (for plain text URLs)
        url_patterns = [
            r'https?://[^\s<>"{}|\\^`\[\]]+',  # Standard URLs
            r'www\.[^\s<>"{}|\\^`\[\]]+',      # www URLs
            r'[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?'  # Domain.com patterns
        ]
        
        for pattern in url_patterns:
            text_urls = re.findall(pattern, paragraph.text)
            for url in text_urls:
                # Clean up URL
                cleaned_url = url.rstrip('.,;:!?)')
                if not cleaned_url.startswith(('http://', 'https://')):
                    if cleaned_url.startswith('www.'):
                        cleaned_url = 'https://' + cleaned_url
                    elif '.' in cleaned_url:
                        cleaned_url = 'https://' + cleaned_url
                
                links.append({
                    'text': url,
                    'url': cleaned_url,
                    'type': self.classify_link_type(cleaned_url)
                })
        
        # Method 3: Check for email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, paragraph.text)
        for email in emails:
            links.append({
                'text': email,
                'url': f'mailto:{email}',
                'type': 'email'
            })
        
        return links
    
    def classify_link_type(self, url):
        """Classify the type of link (website, video, document, etc.)."""
        if not url or url.startswith('internal:'):
            return 'internal'
        
        url_lower = url.lower()
        
        # Email addresses
        if url.startswith('mailto:'):
            return 'email'
        
        # Video platforms
        video_platforms = [
            'youtube.com', 'youtu.be', 'vimeo.com', 'dailymotion.com', 
            'twitch.tv', 'facebook.com/watch', 'instagram.com/tv',
            'tiktok.com', 'linkedin.com/video'
        ]
        if any(platform in url_lower for platform in video_platforms):
            return 'video'
        
        # Document types
        document_extensions = [
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.txt', '.rtf', '.odt', '.ods', '.odp', '.pages', '.numbers', '.keynote'
        ]
        if any(ext in url_lower for ext in document_extensions):
            return 'document'
        
        # Image types
        image_extensions = [
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp',
            '.tiff', '.ico', '.heic', '.raw'
        ]
        if any(ext in url_lower for ext in image_extensions):
            return 'image'
        
        # Social media platforms
        social_platforms = [
            'facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com',
            'pinterest.com', 'snapchat.com', 'reddit.com', 'discord.com'
        ]
        if any(platform in url_lower for platform in social_platforms):
            return 'social'
        
        # Cloud storage
        cloud_platforms = [
            'dropbox.com', 'drive.google.com', 'onedrive.com', 'icloud.com',
            'box.com', 'mega.nz', 'mediafire.com'
        ]
        if any(platform in url_lower for platform in cloud_platforms):
            return 'cloud'
        
        # Development platforms
        dev_platforms = [
            'github.com', 'gitlab.com', 'bitbucket.org', 'stackoverflow.com',
            'codepen.io', 'jsfiddle.net', 'repl.it'
        ]
        if any(platform in url_lower for platform in dev_platforms):
            return 'development'
        
        # External websites
        if url.startswith(('http://', 'https://')):
            return 'external'
        
        return 'unknown'
    
    def extract_comprehensive_content(self, filename):
        """Extract ALL content types from the Word document."""
        print("🔍 Starting comprehensive document analysis...")
        
        doc = docx.Document(filename)
        self.content_blocks = []
        
        # Extract images first if available
        if IMAGE_EXTRACTION_AVAILABLE:
            try:
                print("📸 Extracting images...")
                self.extracted_images = extract_images_from_docx(filename)
                print(f"📸 Found {len(self.extracted_images)} images")
            except Exception as e:
                print(f"⚠️  Image extraction failed: {e}")
                self.extracted_images = []
        
        # Process document elements in order
        image_counter = 0
        table_counter = 0
        
        for element in doc.element.body:
            if isinstance(element, CT_P):
                # This is a paragraph
                paragraph = Paragraph(element, doc)
                text = paragraph.text.strip()
                
                # Extract hyperlinks
                links = self.extract_hyperlinks_from_paragraph(paragraph)
                if links:
                    self.extracted_links.extend(links)
                
                # Check if paragraph contains images
                has_images = False
                for run in paragraph.runs:
                    if run.element.xpath('.//a:blip'):
                        has_images = True
                        image_counter += 1
                
                # Determine paragraph type and importance
                paragraph_type = self.classify_paragraph_type(paragraph, text)
                
                if text or has_images or links:
                    content_block = {
                        'type': paragraph_type,
                        'content': text,
                        'has_image': has_images,
                        'image_ref': f"image_{image_counter}" if has_images else None,
                        'links': links,
                        'style': paragraph.style.name if paragraph.style else None,
                        'alignment': str(paragraph.alignment) if paragraph.alignment else None,
                        'level': self.get_heading_level(paragraph)
                    }
                    self.content_blocks.append(content_block)
                    
            elif isinstance(element, CT_Tbl):
                # This is a table
                table = Table(element, doc)
                table_counter += 1
                
                table_data = self.extract_table_data(table, table_counter)
                if table_data:
                    self.extracted_tables.append(table_data)
                    
                    content_block = {
                        'type': 'table',
                        'content': table_data['formatted_text'],
                        'table_data': table_data,
                        'has_image': False,
                        'image_ref': None,
                        'links': [],
                        'style': None,
                        'alignment': None,
                        'level': 0
                    }
                    self.content_blocks.append(content_block)
        
        print(f"📄 Extracted {len(self.content_blocks)} content blocks")
        print(f"🔗 Found {len(self.extracted_links)} links")
        print(f"📊 Found {len(self.extracted_tables)} tables")
        
        return self.content_blocks
    
    def classify_paragraph_type(self, paragraph, text):
        """Classify the type of paragraph (heading, list, normal, etc.)."""
        if not text:
            return 'empty'
        
        # Check style name
        style_name = paragraph.style.name.lower() if paragraph.style else ''
        
        if 'heading' in style_name:
            return 'heading'
        elif 'title' in style_name:
            return 'title'
        elif 'subtitle' in style_name:
            return 'subtitle'
        elif 'list paragraph' in style_name:
            return 'list_item'  # Treat "List Paragraph" style as list items
        
        # Check content patterns
        if text.startswith(('•', '-', '◦', '▪', '▫')):
            return 'bullet_point'
        elif re.match(r'^\d+\.', text.strip()):
            return 'numbered_list'
        elif text.endswith(':') and len(text) < 100:
            return 'label'
        elif len(text) < 50 and text.isupper():
            return 'section_header'
        elif text.startswith('-' * 10):  # Long dash separators
            return 'separator'
        
        return 'text'
    
    def get_heading_level(self, paragraph):
        """Get the heading level (1-6) or 0 for non-headings."""
        if paragraph.style and 'heading' in paragraph.style.name.lower():
            # Extract number from style name like "Heading 1", "Heading 2", etc.
            match = re.search(r'heading\s*(\d+)', paragraph.style.name.lower())
            if match:
                return int(match.group(1))
        return 0
    
    def extract_table_data(self, table, table_number):
        """Extract structured data from a table."""
        table_data = {
            'number': table_number,
            'rows': [],
            'headers': [],
            'formatted_text': '',
            'structure': {
                'rows': len(table.rows),
                'cols': len(table.columns) if table.rows else 0
            }
        }
        
        for row_idx, row in enumerate(table.rows):
            row_data = []
            for cell in row.cells:
                cell_text = cell.text.strip()
                
                # Extract links from cell
                cell_links = []
                for paragraph in cell.paragraphs:
                    cell_links.extend(self.extract_hyperlinks_from_paragraph(paragraph))
                
                row_data.append({
                    'text': cell_text,
                    'links': cell_links
                })
            
            table_data['rows'].append(row_data)
            
            # First row might be headers
            if row_idx == 0:
                table_data['headers'] = [cell['text'] for cell in row_data]
        
        # Create formatted text representation
        formatted_rows = []
        for row in table_data['rows']:
            formatted_rows.append(" | ".join([cell['text'] for cell in row]))
        table_data['formatted_text'] = "\n".join(formatted_rows)
        
        return table_data
    
    def categorize_content_intelligently(self, content_blocks):
        """Use AI and pattern matching to categorize content by device, page, component."""
        categories = {
            'device': {'mobile': [], 'desktop': [], 'both': []},
            'page_type': {'homepage': [], 'about': [], 'news': [], 'contact': [], 'general': []},
            'component': {'carousel': [], 'navigation': [], 'images': [], 'forms': [], 'layout': []},
            'issue_type': {'bug': [], 'improvement': [], 'feature': [], 'content': []}
        }
        
        # First pass: identify context from headings and titles
        document_context = {
            'headings': [],
            'titles': [],
            'current_section': 'general'
        }
        
        for block in content_blocks:
            if block['type'] in ['heading', 'title', 'section_header']:
                document_context['headings'].append(block['content'].lower())
                document_context['titles'].append(block['content'].lower())
                
                # Update current section context
                content_lower = block['content'].lower()
                if any(keyword in content_lower for keyword in ['mobile', 'smartphone', 'phone']):
                    document_context['current_section'] = 'mobile_context'
                elif any(keyword in content_lower for keyword in ['desktop', 'computer', 'pc']):
                    document_context['current_section'] = 'desktop_context'
                elif any(keyword in content_lower for keyword in ['homepage', 'home page']):
                    document_context['current_section'] = 'homepage'
                elif any(keyword in content_lower for keyword in ['about', 'über uns']):
                    document_context['current_section'] = 'about'
                elif any(keyword in content_lower for keyword in ['news', 'feed', 'articles']):
                    document_context['current_section'] = 'news'
                elif any(keyword in content_lower for keyword in ['contact', 'kontakt']):
                    document_context['current_section'] = 'contact'
        
        # Combine all heading/title context for better categorization
        all_context_text = ' '.join(document_context['headings'] + document_context['titles'])
        
        # Second pass: categorize content blocks using context
        for block in content_blocks:
            content = block['content'].lower()
            
            # Use both block content and document context for categorization
            combined_context = content + ' ' + all_context_text
            
            # Device categorization (enhanced with context)
            if any(keyword in combined_context for keyword in ['mobile', 'smartphone', 'phone', 'responsive']):
                categories['device']['mobile'].append(block)
            elif any(keyword in combined_context for keyword in ['desktop', 'computer', 'pc', 'large screen']):
                categories['device']['desktop'].append(block)
            else:
                categories['device']['both'].append(block)
            
            # Page type categorization (enhanced with context)
            if any(keyword in combined_context for keyword in ['homepage', 'home page', 'main page', 'landing']):
                categories['page_type']['homepage'].append(block)
            elif any(keyword in combined_context for keyword in ['about', 'über uns', 'about us']):
                categories['page_type']['about'].append(block)
            elif any(keyword in combined_context for keyword in ['news', 'feed', 'articles', 'blog']):
                categories['page_type']['news'].append(block)
            elif any(keyword in combined_context for keyword in ['contact', 'kontakt']):
                categories['page_type']['contact'].append(block)
            else:
                # Use current section context as fallback
                if document_context['current_section'] in ['homepage', 'about', 'news', 'contact']:
                    categories['page_type'][document_context['current_section']].append(block)
                else:
                    categories['page_type']['general'].append(block)
            
            # Component categorization (enhanced with context)
            if any(keyword in combined_context for keyword in ['carousel', 'slider', 'slideshow']):
                categories['component']['carousel'].append(block)
            elif any(keyword in combined_context for keyword in ['navigation', 'menu', 'nav', 'arrows']):
                categories['component']['navigation'].append(block)
            elif any(keyword in combined_context for keyword in ['image', 'picture', 'photo', 'quality']):
                categories['component']['images'].append(block)
            elif any(keyword in combined_context for keyword in ['form', 'input', 'field']):
                categories['component']['forms'].append(block)
            elif any(keyword in combined_context for keyword in ['layout', 'display', 'positioning', 'alignment']):
                categories['component']['layout'].append(block)
            
            # Issue type categorization (enhanced with context)
            if any(keyword in combined_context for keyword in ['error', 'broken', 'not working', 'duplicated', 'missing']):
                categories['issue_type']['bug'].append(block)
            elif any(keyword in combined_context for keyword in ['improve', 'optimize', 'better', 'enhance']):
                categories['issue_type']['improvement'].append(block)
            elif any(keyword in combined_context for keyword in ['add', 'new', 'create', 'implement']):
                categories['issue_type']['feature'].append(block)
            else:
                categories['issue_type']['content'].append(block)
        
        return categories
    
    def create_comprehensive_issues(self, content_blocks):
        """Create comprehensive issues with all content types and intelligent categorization."""
        print("🧠 Creating comprehensive issues with intelligent categorization...")
        
        # Get AI analysis if available
        ai_insights = None
        if self.is_ai_available():
            try:
                print("🤖 Getting AI insights...")
                # Combine all text for AI analysis
                combined_text = "\n".join([block['content'] for block in content_blocks if block['content']])
                ai_insights = self.ai_analyzer.analyze_document_with_ai(combined_text)
                print(f"🎯 AI found {len(ai_insights)} intelligent insights")
            except Exception as e:
                print(f"⚠️  AI analysis failed: {e}")
        
        # Categorize content
        categories = self.categorize_content_intelligently(content_blocks)
        
        # Create issues based on content structure
        issues = []
        current_issue = None
        image_counter = 0
        
        for block in content_blocks:
            content = block['content']
            
            # Skip empty content
            if not content.strip():
                continue
            
            # Skip headings/titles completely for ticket creation - they're only for categorization
            if block['type'] in ['heading', 'title', 'section_header']:
                # Add to current issue as context if one exists, but don't create new issues
                if current_issue:
                    current_issue['description_parts'].append(content)
                    current_issue['content_blocks'].append(block)
                continue
            
            # Handle separators - they indicate new issue boundaries
            if block['type'] == 'separator':
                # Finalize current issue if exists
                if current_issue:
                    issues.append(self.finalize_issue(current_issue, categories, ai_insights))
                    current_issue = None
                continue
            
            # Skip labels/context that are too short or look like labels
            if (len(content) < 15 or 
                content.endswith('| Homecare') or 
                content.startswith('Patient:') or 
                content.startswith('Fachkräfte') or
                content in ['Austria | Homecare', 'Patient:innen | Homecare', 'Fachkräfte | Homecare']):
                # Add to current issue as context if one exists
                if current_issue:
                    current_issue['description_parts'].append(content)
                    current_issue['content_blocks'].append(block)
                continue
            
            # Determine if this starts a new issue
            is_new_issue = (
                # Numbered list items should start new issues (1., 2., 3., etc.)
                block['type'] == 'numbered_list' or
                
                # List items (including "List Paragraph" style) that are substantial should start new issues
                (block['type'] == 'list_item' and len(content) > 20) or
                
                # Very specific content-based heuristics (more restrictive)
                (len(content) > 30 and 
                 not content.startswith(('•', '-', '◦')) and
                 any(keyword in content.lower() for keyword in 
                     ['fix the', 'resolve the', 'update the', 'correct the', 'improve the', 'implement', 
                      'display', 'optimal', 'space', 'cut off', 'jump']) and
                 (not current_issue or len(current_issue['description_parts']) > 4))
            )
            
            if is_new_issue or current_issue is None:
                # Finalize previous issue
                if current_issue:
                    issues.append(self.finalize_issue(current_issue, categories, ai_insights))
                
                # Start new issue
                current_issue = {
                    'title': content[:100] + ('...' if len(content) > 100 else ''),
                    'description_parts': [content],
                    'images': [],
                    'links': [],
                    'tables': [],
                    'content_blocks': [block],
                    'categories': self.get_block_categories(block, categories)
                }
            else:
                # Add to current issue
                if current_issue:
                    current_issue['description_parts'].append(content)
                    current_issue['content_blocks'].append(block)
            
            # Add content type specific data
            if block['has_image'] and block['image_ref'] and current_issue:
                # Find the corresponding extracted image
                image_num = int(block['image_ref'].split('_')[1]) if '_' in block['image_ref'] else 0
                if image_num > 0 and image_num <= len(self.extracted_images):
                    image_info = self.extracted_images[image_num - 1]  # Convert to 0-based index
                    current_issue['images'].append(image_info)
                    print(f"📸 Linked {image_info['filename']} to issue: {current_issue['title'][:50]}...")
            
            if block['links'] and current_issue:
                current_issue['links'].extend(block['links'])
            
            if block.get('table_data') and current_issue:
                current_issue['tables'].append(block['table_data'])
        
        # Finalize last issue
        if current_issue:
            issues.append(self.finalize_issue(current_issue, categories, ai_insights))
        
        # If we have leftover images that weren't linked, distribute them evenly
        linked_images = set()
        for issue in issues:
            for img in issue['images']:
                linked_images.add(img['filename'])
        
        unlinked_images = [img for img in self.extracted_images if img['filename'] not in linked_images]
        if unlinked_images:
            print(f"📸 Distributing {len(unlinked_images)} unlinked images across issues...")
            for i, img in enumerate(unlinked_images):
                issue_index = i % len(issues)
                issues[issue_index]['images'].append(img)
                print(f"📸 Added {img['filename']} to issue {issue_index + 1}")
        
        print(f"✅ Created {len(issues)} comprehensive issues")
        return issues
    
    def get_block_categories(self, block, categories):
        """Get categories for a specific content block."""
        block_categories = {}
        
        for category_type, category_groups in categories.items():
            for group_name, blocks in category_groups.items():
                if block in blocks:
                    block_categories[category_type] = group_name
                    break
        
        return block_categories
    
    def finalize_issue(self, issue_data, categories, ai_insights):
        """Finalize an issue with comprehensive formatting and AI insights."""
        # Build comprehensive description
        description_parts = []
        
        # Add main description
        description_parts.extend(issue_data['description_parts'])
        
        # Add categorization info
        if issue_data['categories']:
            description_parts.append("\n## 📋 **Issue Classification:**")
            for cat_type, cat_value in issue_data['categories'].items():
                description_parts.append(f"- **{cat_type.title()}**: {cat_value.title()}")
        
        # Add tables if present
        if issue_data['tables']:
            description_parts.append("\n## 📊 **Tables:**")
            for i, table in enumerate(issue_data['tables'], 1):
                description_parts.append(f"\n### Table {i} ({table['structure']['rows']}x{table['structure']['cols']}):")
                description_parts.append(f"```\n{table['formatted_text']}\n```")
        
        # Add links if present
        if issue_data['links']:
            description_parts.append("\n## 🔗 **Related Links:**")
            for link in issue_data['links']:
                link_type_emoji = {'video': '🎥', 'document': '📄', 'image': '🖼️', 'external': '🌐', 'internal': '🔗'}.get(link['type'], '🔗')
                description_parts.append(f"- {link_type_emoji} [{link['text']}]({link['url']}) ({link['type']})")
        
        # Add images if present
        if issue_data['images']:
            description_parts.append("\n## 📸 **Attached Images:**")
            for img in issue_data['images']:
                description_parts.append(f"- {img['filename']} ({img['size']:,} bytes)")
        
        # Add AI insights if available
        if ai_insights:
            # Find matching AI insight
            for ai_task in ai_insights:
                if any(keyword in ai_task['title'].lower() for keyword in issue_data['title'].lower().split()[:3]):
                    description_parts.append(f"\n## 🤖 **AI Analysis:**")
                    description_parts.append(f"- **Priority**: {ai_task.get('priority', 'Medium')}")
                    description_parts.append(f"- **Complexity**: {ai_task.get('complexity', 'Medium')}")
                    description_parts.append(f"- **Category**: {ai_task.get('category', 'Task')}")
                    break
        
        return {
            'title': issue_data['title'],
            'description': "\n".join(description_parts),
            'images': issue_data['images'],
            'links': issue_data['links'],
            'tables': issue_data['tables'],
            'categories': issue_data['categories'],
            'content_blocks': len(issue_data['content_blocks'])
        }
    
    def analyze_document_comprehensively(self, filename):
        """Main method to perform comprehensive document analysis."""
        print("🚀 Starting comprehensive document analysis...")
        print("=" * 80)
        
        try:
            # Extract all content types
            content_blocks = self.extract_comprehensive_content(filename)
            
            if not content_blocks:
                raise Exception("No content found in document")
            
            # Create comprehensive issues
            issues = self.create_comprehensive_issues(content_blocks)
            
            if not issues:
                raise Exception("No issues could be created from document content")
            
            # Print summary
            print("\n📊 **COMPREHENSIVE ANALYSIS SUMMARY:**")
            print("=" * 80)
            print(f"📄 Content Blocks: {len(content_blocks)}")
            print(f"📸 Images: {len(self.extracted_images)}")
            print(f"🔗 Links: {len(self.extracted_links)}")
            print(f"📊 Tables: {len(self.extracted_tables)}")
            print(f"🎫 Issues Created: {len(issues)}")
            
            # Print issue details
            for i, issue in enumerate(issues, 1):
                print(f"\n--- ISSUE {i} ---")
                print(f"📝 Title: {issue['title']}")
                print(f"📄 Content Blocks: {issue['content_blocks']}")
                print(f"📸 Images: {len(issue['images'])}")
                print(f"🔗 Links: {len(issue['links'])}")
                print(f"📊 Tables: {len(issue['tables'])}")
                if issue['categories']:
                    print(f"🏷️  Categories: {issue['categories']}")
                print(f"📄 Description: {issue['description'][:200]}...")
            
            return issues
            
        except Exception as e:
            print(f"❌ Comprehensive analysis failed: {e}")
            raise

def get_comprehensive_issues(filename):
    """Main function to get comprehensive issues from a document."""
    analyzer = ComprehensiveDocumentAnalyzer()
    return analyzer.analyze_document_comprehensively(filename)

def test_comprehensive_analysis():
    """Test the comprehensive analysis on the Word document."""
    filename = 'Changes to the HC website AT.docx'
    
    try:
        issues = get_comprehensive_issues(filename)
        return issues
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return []

if __name__ == "__main__":
    print("🔬 Testing Comprehensive Document Analysis...")
    test_comprehensive_analysis() 