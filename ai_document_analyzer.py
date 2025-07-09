import json
import docx
from openai import OpenAI
import re

# Import enhanced extraction for images
try:
    from extract_word_content import extract_images_from_docx
    IMAGE_EXTRACTION_AVAILABLE = True
except ImportError:
    IMAGE_EXTRACTION_AVAILABLE = False

# Import configuration
try:
    from config import OPENAI_CONFIG
except ImportError:
    OPENAI_CONFIG = {
        "api_key": "YOUR_OPENAI_API_KEY_HERE",
        "model": "gpt-4o-mini",
        "max_tokens": 4000,
        "temperature": 0.1
    }

class AIDocumentAnalyzer:
    """AI-powered document analyzer using OpenAI to extract structured tasks."""
    
    def __init__(self):
        """Initialize the AI analyzer with OpenAI client."""
        self.client = None
        self.setup_openai()
    
    def setup_openai(self):
        """Setup OpenAI client if API key is available."""
        api_key = OPENAI_CONFIG.get("api_key")
        if api_key and api_key != "YOUR_OPENAI_API_KEY_HERE":
            try:
                self.client = OpenAI(api_key=api_key)
                print("✅ OpenAI client initialized successfully")
            except Exception as e:
                print(f"❌ Failed to initialize OpenAI client: {e}")
                self.client = None
        else:
            print("⚠️  OpenAI API key not configured. AI analysis will be disabled.")
    
    def is_available(self):
        """Check if AI analysis is available."""
        return self.client is not None
    
    def extract_text_from_docx(self, filename):
        """Extract text content from Word document."""
        try:
            doc = docx.Document(filename)
            full_text = []
            
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text.strip())
            
            return "\n".join(full_text)
        except Exception as e:
            raise Exception(f"Failed to extract text from document: {e}")
    
    def analyze_document_with_ai(self, document_text):
        """Use AI to analyze document and extract structured tasks."""
        if not self.client:
            raise Exception("OpenAI client not available")
        
        prompt = f"""
You are an expert at analyzing project documents and extracting actionable tasks. 

Please analyze the following document and extract all tasks/issues that need to be addressed. Look for:
- Numbered lists (1., 2., 3., etc.)
- Bullet points with action items
- Issues or problems mentioned
- Tasks or requirements described

For each task you find, provide:
1. A clear, concise title (suitable for a Jira ticket summary)
2. A detailed description with context
3. Priority level (High, Medium, Low)
4. Estimated complexity (Simple, Medium, Complex)

Return the results as a JSON array with this structure:
[
  {{
    "title": "Clear task title",
    "description": "Detailed description with context and requirements",
    "priority": "High|Medium|Low",
    "complexity": "Simple|Medium|Complex",
    "category": "Bug|Feature|Improvement|Task"
  }}
]

Document to analyze:
{document_text}

Please extract all actionable tasks and format them as JSON:
"""
        
        try:
            response = self.client.chat.completions.create(
                model=OPENAI_CONFIG["model"],
                messages=[
                    {"role": "system", "content": "You are an expert project manager who excels at extracting actionable tasks from documents."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=OPENAI_CONFIG["max_tokens"],
                temperature=OPENAI_CONFIG["temperature"]
            )
            
            ai_response = response.choices[0].message.content
            
            # Try to extract JSON from the response
            json_match = re.search(r'\[.*\]', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                tasks = json.loads(json_str)
                return tasks
            else:
                # If no JSON found, try to parse the entire response
                return json.loads(ai_response)
                
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse AI response as JSON: {e}")
            print(f"Raw response: {ai_response}")
            raise Exception("AI returned invalid JSON format")
        except Exception as e:
            print(f"❌ OpenAI API error: {e}")
            raise Exception(f"AI analysis failed: {e}")
    
    def get_ai_enhanced_issues(self, filename):
        """Main method to get AI-enhanced issues from a Word document."""
        print("🤖 Starting AI-powered document analysis...")
        
        if not self.is_available():
            raise Exception("AI analysis is not available. Please configure OpenAI API key in config.py")
        
        try:
            # Extract images first if available
            extracted_images = []
            if IMAGE_EXTRACTION_AVAILABLE:
                try:
                    print("📸 Extracting images from document...")
                    extracted_images = extract_images_from_docx(filename)
                    print(f"📸 Found {len(extracted_images)} images in document")
                except Exception as e:
                    print(f"⚠️  Image extraction failed: {e}")
            
            # Extract text from document
            print("📄 Extracting text from document...")
            document_text = self.extract_text_from_docx(filename)
            
            if not document_text.strip():
                raise Exception("Document appears to be empty or contains no readable text")
            
            print(f"📊 Document contains {len(document_text)} characters")
            
            # Analyze with AI
            print("🔍 Analyzing document with AI...")
            ai_tasks = self.analyze_document_with_ai(document_text)
            
            if not ai_tasks:
                raise Exception("AI analysis returned no tasks")
            
            # Convert AI tasks to our standard format and distribute images
            enhanced_issues = []
            
            # Simple distribution: give each task roughly equal number of images
            for i, task in enumerate(ai_tasks):
                # Calculate which images belong to this task
                task_images = []
                if extracted_images:
                    images_per_task = len(extracted_images) // len(ai_tasks)
                    remaining_images = len(extracted_images) % len(ai_tasks)
                    
                    start_idx = i * images_per_task
                    end_idx = start_idx + images_per_task
                    
                    # Give extra images to the first few tasks
                    if i < remaining_images:
                        start_idx += i
                        end_idx += i + 1
                    else:
                        start_idx += remaining_images
                        end_idx += remaining_images
                    
                    task_images = extracted_images[start_idx:end_idx]
                
                issue = {
                    'title': task.get('title', 'Untitled Task'),
                    'description': self.format_description(task, task_images),
                    'priority': task.get('priority', 'Medium'),
                    'complexity': task.get('complexity', 'Medium'),
                    'category': task.get('category', 'Task'),
                    'images': task_images
                }
                enhanced_issues.append(issue)
            
            print(f"✅ AI analysis complete! Found {len(enhanced_issues)} tasks")
            if extracted_images:
                print(f"📸 Distributed {len(extracted_images)} images across tasks")
            
            return enhanced_issues
            
        except Exception as e:
            print(f"❌ AI analysis failed: {e}")
            raise
    
    def format_description(self, task, images=None):
        """Format task description with additional metadata."""
        description = task.get('description', 'No description provided')
        priority = task.get('priority', 'Medium')
        complexity = task.get('complexity', 'Medium')
        category = task.get('category', 'Task')
        
        formatted_description = f"{description}\n\n"
        formatted_description += f"**AI Analysis:**\n"
        formatted_description += f"• Priority: {priority}\n"
        formatted_description += f"• Complexity: {complexity}\n"
        formatted_description += f"• Category: {category}\n"

        if images:
            formatted_description += f"\n**Images:**\n"
            for i, img in enumerate(images, 1):
                formatted_description += f"• Image {i}: {img['filename']} ({img['size']} bytes)\n"
        
        return formatted_description

# Global instance for easy access
ai_analyzer = AIDocumentAnalyzer()

def get_ai_enhanced_issues(filename):
    """Convenience function to get AI-enhanced issues."""
    return ai_analyzer.get_ai_enhanced_issues(filename)

def is_ai_available():
    """Check if AI analysis is available."""
    return ai_analyzer.is_available() 