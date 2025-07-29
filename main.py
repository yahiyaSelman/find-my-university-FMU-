from flask import Flask, render_template, request, jsonify, session,redirect
import os
from openai import OpenAI
import json
import supabase
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "your-secret-key")  # Change in production

# Initialize Supabase client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Warning: Supabase credentials not found in environment variables.")
    print("Please set SUPABASE_URL and SUPABASE_KEY environment variables.")
    print("For now, will proceed with empty values but Supabase connection will fail.")

supabase_client = supabase.create_client(
    SUPABASE_URL or "",
    SUPABASE_KEY or ""
)

def validate_student_id(student_id):
    try:
        response = supabase_client.table('students').select('student_id').eq('student_id', student_id).execute()
        if response.data:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error validating student ID: {e}")
        return False


def fetch_universities_from_supabase():
    """
    Fetch university data from Supabase
    """
    try:
        # Assuming you have a 'universities' table in Supabase
        response = supabase_client.table('universities').select('*').execute()
        
        if hasattr(response, 'data') and response.data:
            return response.data
        else:
            print("Warning: No data returned from Supabase. Using backup data.")
            return get_backup_universities_data()
    except Exception as e:
        print(f"Error fetching data from Supabase: {e}")
        print("Using backup university data instead.")
        return get_backup_universities_data()

def get_backup_universities_data():
    """
    Return backup university data in case Supabase connection fails
    """
    return [
        {
            "name": "Kuwait University",
            "type": "Public",
            "min_gpa": 2.67,
            "phone": "+965 2463 3333",
            "email": "info@ku.edu.kw",
            "location": "Kuwait City, various campuses including Khaldiya, Kaifan, and Shuwaikh",
            "required_documents": [
                "High school certificate",
                "Passport copy",
                "Civil ID",
                "Passport-sized photographs",
                "English proficiency test (TOEFL/IELTS)"
            ]
        },
        {
            "name": "American University of Kuwait (AUK)",
            "type": "Private",
            "min_gpa": 2.0,
            "phone": "+965 2224 8399",
            "email": "admissions@auk.edu.kw",
            "location": "Salmiya, Kuwait",
            "required_documents": [
                "High school certificate",
                "Equivalency certificate (for non-Kuwaiti certificates)",
                "English proficiency scores",
                "Passport copy",
                "Civil ID",
                "Passport-sized photographs"
            ]
        },
        {
            "name": "Gulf University for Science and Technology (GUST)",
            "type": "Private",
            "min_gpa": 2.0,
            "phone": "+965 2530 7000",
            "email": "admissions@gust.edu.kw",
            "location": "Mubarak Al-Abdullah area, West Mishref",
            "required_documents": [
                "High school certificate",
                "English proficiency test scores",
                "Passport copy",
                "Civil ID",
                "Passport-sized photographs"
            ]
        },
        {
            "name": "Australian College of Kuwait (ACK)",
            "type": "Private",
            "min_gpa": 2.0,
            "phone": "+965 1828 225",
            "email": "admissions@ack.edu.kw",
            "location": "West Mishref, Kuwait",
            "required_documents": [
                "High school certificate",
                "English proficiency test scores",
                "Passport copy",
                "Civil ID",
                "Passport-sized photographs"
            ]
        },
        {
            "name": "American University of the Middle East (AUM)",
            "type": "Private",
            "min_gpa": 2.0,
            "phone": "+965 2225 1400",
            "email": "admissions@aum.edu.kw",
            "location": "Egaila, Kuwait",
            "required_documents": [
                "High school certificate",
                "English proficiency test scores",
                "Passport copy",
                "Civil ID",
                "Passport-sized photographs"
            ]
        },
        {
            "name": "Kuwait College of Science and Technology (KCST)",
            "type": "Private",
            "min_gpa": 2.0,
            "phone": "+965 2227 5270",
            "email": "info@kcst.edu.kw",
            "location": "Doha District, Kuwait",
            "required_documents": [
                "High school certificate",
                "English proficiency test scores",
                "Passport copy",
                "Civil ID",
                "Passport-sized photographs"
            ]
        },
        {
            "name": "Box Hill College Kuwait (BHCK)",
            "type": "Private",
            "min_gpa": 2.0,
            "phone": "+965 2573 7039",
            "email": "info@bhck.edu.kw",
            "location": "Abu Halifa, Kuwait",
            "required_documents": [
                "High school certificate",
                "English proficiency test scores",
                "Passport copy",
                "Civil ID",
                "Passport-sized photographs"
            ]
        },
        {
            "name": "Kuwait Technical College (KTC)",
            "type": "Private",
            "min_gpa": 2.0,
            "phone": "+965 1825 425",
            "email": "info@ktc.edu.kw",
            "location": "Shuwaikh, Kuwait",
            "required_documents": [
                "High school certificate",
                "English proficiency test (if applicable)",
                "Passport copy",
                "Civil ID",
                "Passport-sized photographs"
            ]
        }
    ]

def initialize_openai_client():
    """
    Initialize the OpenAI client with API key from environment variable
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Warning: OpenAI API key not found in environment variables.")
        return None
    
    return OpenAI(api_key=api_key)

def get_university_info(query, universities_data):
    """
    Process the user query and return relevant university information
    """
    client = initialize_openai_client()
    
    if not client:
        return "Error: OpenAI API key not found in environment variables. Please check your .env file."
    
    # Updated system message with structured formatting instructions
    system_message = """
    You are a helpful assistant that provides information about universities in Kuwait.
    Use only the information provided in the university database to answer questions.
    If the information is not available in the database, politely mention that.
    
    IMPORTANT FORMATTING INSTRUCTIONS:
    1. Never mention the database or refer to "the provided database" in your responses
    2. Format your responses in clearly structured sections with headings using the following format:
       
       UNIVERSITY NAME
       
       OVERVIEW
       [General information about the university]
       
       ADMISSION REQUIREMENTS
       - GPA: [Minimum GPA requirements]
       - Required Documents:
         - [Document 1]
         - [Document 2]
         - etc.
       
       CONTACT INFORMATION
       - Phone: [phone number]
       - Email: [email address]
       - Location: [location description]
       - Map: [map_link] (if available)
    
    3. Do not use HTML tags or markdown formatting in your response
    4. Keep responses concise and focused on what the user is asking
    5. Use clear section headings with line breaks between sections
    6. Format phone numbers, email addresses, and map links as plain text
    
    You are directly talking to a student looking for university information, so keep your tone friendly and helpful.
    """
    
    # Convert our database to a string for the context
    universities_context = json.dumps(universities_data, indent=2)
    
    try:
        # Create the conversation with OpenAI
        response = client.chat.completions.create(
            model="gpt-4-turbo",  # Or use a different model as needed
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Here is the Kuwait universities database: {universities_context}"},
                {"role": "user", "content": query}
            ],
            temperature=0.2  # Lower temperature for more factual responses
        )
        
        # Get the raw response
        raw_response = response.choices[0].message.content
        
        # Apply post-processing to format the response properly
        # This function will be defined separately to handle the formatting
        formatted_response = format_university_response(raw_response)
        
        return formatted_response
    except Exception as e:
        return f"Error: {str(e)}. Please check your OpenAI API key in the .env file."

def format_university_response(text):
    """
    Format the university response with proper sections and contact information
    """
    # Replace any remaining HTML or markdown that might have come through
    formatted_text = text.replace("<ul>", "").replace("</ul>", "")
    formatted_text = formatted_text.replace("<li>", "- ").replace("</li>", "\n")
    
    # Clean up any references to the database
    database_refs = [
        "from the database", 
        "in the database", 
        "from the provided database", 
        "based on the database", 
        "according to the database"
    ]
    for ref in database_refs:
        formatted_text = formatted_text.replace(ref, "")
    
    # Replace generic list phrases
    formatted_text = formatted_text.replace("Here is a list of universities in Kuwait from the provided database", 
                                          "Here is a list of universities in Kuwait")
    
    # Format contact information more clearly
    # Phone numbers
    formatted_text = formatted_text.replace("Phone:", "\nPhone:")
    # Email addresses
    formatted_text = formatted_text.replace("Email:", "\nEmail:")
    
    # Format map links
    # Look for map links in the format [text](url) and convert them to a clean format
    import re
    map_link_pattern = r'\[map link\]\((https?://[^\s\)]+)\)'
    map_links = re.findall(map_link_pattern, formatted_text)
    
    if map_links:
        for link in map_links:
            formatted_text = formatted_text.replace(f"[map link]({link})", f"\nMap: {link}")
    
    # Make headings stand out
    formatted_text = formatted_text.replace("OVERVIEW", "\nOVERVIEW\n")
    formatted_text = formatted_text.replace("ADMISSION REQUIREMENTS", "\nADMISSION REQUIREMENTS\n")
    formatted_text = formatted_text.replace("CONTACT INFORMATION", "\nCONTACT INFORMATION\n")
    
    # Ensure document list has proper formatting
    formatted_text = formatted_text.replace("Required Documents:", "\nRequired Documents:")
    
    return formatted_text


@app.route('/')
def splash():
    return render_template('splash.html')

@app.route('/student')
def student_login():
    return render_template('student_id.html')

@app.route('/enter-name', methods=['POST'])
def enter_name():
    data = request.json
    name = data.get('name', '').strip()

    if name:  # No validation, just check if not empty
        session['student_name'] = name
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Name cannot be empty'})

    
@app.route('/chat')
def chat_page():
    if 'student_name' not in session:
        return redirect('/student')  # Still redirect to the input page if name not set
    return render_template('index.html', student_name=session['student_name'])


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'response': 'Please provide a message'})
    
    # Fetch universities data from Supabase
    universities_data = fetch_universities_from_supabase()
    
    # Get response from the university info function
    bot_response = get_university_info(user_message, universities_data)
    
    # Convert newlines to <br> tags for proper display in HTML
    # (This allows preserving the formatting while displaying in a web browser)
    bot_response = bot_response.replace('\n', '<br>')
    
    # Format contact information for better visibility:
    # Make email addresses clickable
    import re
    email_pattern = r'Email:\s*([\w\.-]+@[\w\.-]+)'
    email_matches = re.findall(email_pattern, bot_response)
    for email in email_matches:
        bot_response = bot_response.replace(f"Email: {email}", f"Email: <a href='mailto:{email}'>{email}</a>")
    
    # Make phone numbers clickable
    phone_pattern = r'Phone:\s*(\+?\d[\d\s-]+)'
    phone_matches = re.findall(phone_pattern, bot_response)
    for phone in phone_matches:
        # Clean phone number for href
        clean_phone = phone.replace(" ", "").replace("-", "")
        bot_response = bot_response.replace(f"Phone: {phone}", f"Phone: <a href='tel:{clean_phone}'>{phone}</a>")
    
    # Make map links clickable
    map_pattern = r'Map:\s*(https?://[^\s<]+)'
    map_matches = re.findall(map_pattern, bot_response)
    for map_url in map_matches:
        bot_response = bot_response.replace(f"Map: {map_url}", f"Map: <a href='{map_url}' target='_blank'>Open in Google Maps</a>")
    
    # Format headings with stronger styling
    heading_tags = ["OVERVIEW", "ADMISSION REQUIREMENTS", "CONTACT INFORMATION"]
    for tag in heading_tags:
        bot_response = bot_response.replace(f"<br>{tag}<br>", f"<br><strong>{tag}</strong><br>")
    
    return jsonify({'response': bot_response})

if __name__ == '__main__':
    # Make sure the templates directory exists
    if not os.path.exists('templates'):
        os.makedirs('templates')
        
    # Start the Flask app
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))