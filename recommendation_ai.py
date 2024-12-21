import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import webbrowser
import base64
import pandas as pd
import re

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    """Authenticates with Gmail API and returns the Gmail service object."""
    creds = None

    # Load token if it exists
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If no token is present, get new authentication
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
               'credentials.json', SCOPES)

            auth_url, _ = flow.authorization_url(prompt='consent')
            print("Please visit this URL in your browser: {}".format(auth_url))
            webbrowser.open(auth_url, new=2) # Open the URL in the browser

            code = input('Enter the authorization code: ')
            flow.fetch_token(code=code)
            creds = flow.credentials
        # Save the credentials for future runs
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)
    return service


def get_message_content(service, message_id, user_id='me'):
    message = service.users().messages().get(userId=user_id, id=message_id, format='full').execute()
    payload = message['payload']

    content = "no text content"

    if 'parts' in payload:
      parts = payload['parts']
      for part in parts:
          if part['mimeType'] == 'text/plain':
              # Check if 'data' key exists before accessing it
              if 'data' in part['body']:
                  data = part['body']['data']
                  decoded_data = base64.urlsafe_b64decode(data).decode('utf-8')
                  content = decoded_data
                  break  # Exit loop after finding text/plain content
    # Check if 'body' key exists and then check for 'data' key within 'body' # This line is added
    elif 'body' in payload and 'data' in payload['body']:
      data = payload['body']['data']
      decoded_data = base64.urlsafe_b64decode(data).decode('utf-8')
      content = decoded_data

    headers = {}
    if 'headers' in payload:
      for header in payload['headers']:
         headers[header['name']] = header['value']

    subject = headers.get('Subject',"")
    sender = headers.get('From',"")

    return  {'message_id': message_id, 'subject': subject, 'sender':sender, 'content': content}


def fetch_all_emails(service, user_id='me', max_results=100):
    """Fetches all emails from the inbox, ordered from newest to oldest."""

    email_list = []
    results = service.users().messages().list(userId=user_id, maxResults=max_results).execute()
    messages = results.get('messages', [])

    for message in messages:
      email_data = get_message_content(service,message['id'],user_id)
      email_list.append(email_data)

    return email_list

job_names = [
    "Software Engineer",
    "Data Scientist",
    "Product Manager",
    "UI/UX Designer",
    "Cloud Architect",
    "AI/ML Engineer",
    "Full-Stack Developer",
    "DevOps Engineer",
    "Cybersecurity Analyst",
    "Business Analyst",
    "Digital Marketing Specialist",
    "Sales Executive",
    "Human Resources Manager",
    "Mechanical Engineer",
    "Electrical Engineer",
    "Civil Engineer",
    "Content Writer",
    "Graphic Designer",
    "Project Manager",
    "Data Analyst",
    "Customer Support Representative",
    "Network Administrator",
    "Quality Assurance Engineer",
    "Financial Analyst",
    "Research Scientist",
    "Operations Manager",
    "Game Developer",
    "Database Administrator",
    "SEO Specialist",
    "Marketing Manager"
]


def extract_insights(text):
    job_history_keywords = [
        "previous role", "past experience", "employment history", "worked at", "responsibilities included",
        "managed", "led", "achieved", "past job", "former position", "roles at", "job position", "employment", "experience",
        "during the time", "in the role of", "before this", "after that", "prior to that", "during my tenure at","fresher"
    ]
    skills_keywords = [
        "proficient in", "experienced with", "knowledge of", "familiar with", "expertise in", "ability to", "skills in", "skill set includes",
        "strong in", "competent in", "versed in", "trained in", "adept at", "mastery of", "specialized in",
        "technical skill", "management skill", "interpersonal skill" , "soft skill", "hard skill"
    ]
    training_keywords = [
        "training program", "certification", "coursework", "workshop", "seminar", "online course", "training in", "training on",
        "certified in", "completed", "attended", "bootcamp", "learning program", "educational program", "studied", "degree in", "certificate in"
    ]
    feedback_keywords = [
        "feedback on", "performance review", "client satisfaction", "positive review", "negative review", "constructive criticism",
        "improvement area", "areas for development", "comments on", "evaluation of", "rated as", "scored", "recommendation", "testimonial",
        "praise for", "critique of", "input on", "suggested that" , "response to feedback"
    ]

    job_history_pattern = r"(?:(?:previous|past|former)\s+role:|employment(?:ed)?\s+history:|worked\s+at|responsibilities\s+included|managed|led|achieved|during\s+my\s+tenure\s+at|in\s+the\s+role\s+of|before\s+this|after\s+that|prior\s+to\s+that)(.*?\.)(?=\s*(?:(?:previous|past|former)\s+role:|employment(?:ed)?\s+history:|worked\s+at|responsibilities\s+included|managed|led|achieved|during\s+my\s+tenure\s+at|in\s+the\s+role\s+of|before\s+this|after\s+that|prior\s+to\s+that)|$)"

    skills_pattern = r"(?:(?:proficient|experienced|knowledge|familiar|expertise)\s+in|ability\s+to|skills\s+in|strong\s+in|competent\s+in|versed\s+in|trained\s+in|adept\s+at|mastery\s+of|specialized\s+in)(.*?)(?=\s*(?:(?:proficient|experienced|knowledge|familiar|expertise)\s+in|ability\s+to|skills\s+in|strong\s+in|competent\s+in|versed\s+in|trained\s+in|adept\s+at|mastery\s+of|specialized\s+in)|$)"

    training_pattern = r"(?:(?:training|certification|coursework|workshop|seminar|online course)\s+in|certified\s+in|completed|attended|bootcamp|learning\s+program|educational\s+program|studied|degree\s+in|certificate\s+in)(.*?)(?=\s*(?:(?:training|certification|coursework|workshop|seminar|online course)\s+in|certified\s+in|completed|attended|bootcamp|learning\s+program|educational\s+program|studied|degree\s+in|certificate\s+in)|$)"

    feedback_pattern = r"(?:(?:feedback|review|client satisfaction|positive review|negative review|constructive criticism)\s+on|improvement\s+area|areas\s+for\s+development|comments\s+on|evaluation\s+of|rated\s+as|scored|recommendation|testimonial|praise\s+for|critique\s+of|input\s+on|suggested\s+that|response\s+to\s+feedback)(.*?)(?=\s*(?:(?:feedback|review|client satisfaction|positive review|negative review|constructive criticism)\s+on|improvement\s+area|areas\s+for\s+development|comments\s+on|evaluation\s+of|rated\s+as|scored|recommendation|testimonial|praise\s+for|critique\s+of|input\s+on|suggested\s+that|response\s+to\s+feedback)|$)"

    extracted_jobs = []
    for job in job_names:
       if re.search(r'\b' + re.escape(job) + r'\b',text, re.IGNORECASE):
          extracted_jobs.append(job)

    job_history = re.findall(job_history_pattern, text, re.IGNORECASE)
    skills = re.findall(skills_pattern, text, re.IGNORECASE)
    training = re.findall(training_pattern, text, re.IGNORECASE)
    feedback = re.findall(feedback_pattern, text, re.IGNORECASE)

    return {
        "jobs": extracted_jobs,
        "job_history": job_history,
        "skills": skills,
        "training": training,
        "feedback": feedback,
    }

# Simple database of resources (can be improved for real application)
online_resources = {
    "Software Engineer": {
         "courses": [
             {"name": "Software Engineering Master Track", "link":"https://www.coursera.org/professional-certificates/software-engineering-master-track", "platform":"Coursera"},
             {"name": "CS50's Introduction to Computer Science", "link":"https://www.edx.org/course/introduction-computer-science-harvardx-cs50x", "platform":"edX"},
             ],
         "videos":[
             {"name":"Software Engineering Playlist","link":"https://www.youtube.com/playlist?list=PLWKjhJtqVnxf9N2EwU76v72Vw01d3h11J","platform":"YouTube"}
         ]
    },
     "Data Scientist": {
        "courses": [
            {"name": "Data Science Specialization", "link": "https://www.coursera.org/specializations/jhu-data-science", "platform": "Coursera"},
            {"name": "Python for Data Science", "link": "https://www.edx.org/professional-certificate/uc-berkeleyx-python-for-data-science", "platform": "edX"}
        ],
        "videos": [
            {"name": "Data Science with Python", "link": "https://www.youtube.com/watch?v=5qS-j0Yw49k", "platform": "YouTube"}
        ]
    },
    "AI/ML Engineer": {
        "courses": [
            {"name": "Machine Learning Specialization", "link": "https://www.coursera.org/specializations/machine-learning", "platform": "Coursera"},
            {"name": "Deep Learning Specialization", "link": "https://www.coursera.org/specializations/deep-learning", "platform": "Coursera"}
        ],
        "videos": [
             {"name": "Machine Learning Fundamentals", "link":"https://www.youtube.com/watch?v=GIsg-Zp4mXU","platform":"YouTube"}
        ]
    },
     "UI/UX Designer": {
        "courses": [
            {"name": "Google UX Design Professional Certificate", "link": "https://www.coursera.org/professional-certificates/google-ux-design", "platform": "Coursera"},
            {"name": "UI/UX Design Specialization", "link": "https://www.coursera.org/specializations/ui-ux-design", "platform": "Coursera"}
        ],
        "videos": [
            {"name": "UI/UX Design Fundamentals", "link": "https://www.youtube.com/watch?v=cT1-kK1_h58", "platform": "YouTube"}
        ]
    }
}
job_openings = {
    "Software Engineer": [
         {"title": "Software Engineer", "link":"https://www.example.com/software-engineer1", "company":"Acme Corp"},
         {"title": "Senior Software Engineer", "link":"https://www.example.com/software-engineer2", "company":"Beta Co"}
    ],
    "Data Scientist":[
      {"title":"Data Scientist","link":"https://www.example.com/data-scientist1", "company": "Gamma Inc"},
      {"title":"Senior Data Scientist","link":"https://www.example.com/data-scientist2", "company":"Delta Co"}
    ]
}

def recommend_resources(user_profile, language):
    recommendations = {"courses": [], "videos": [], "jobs":[]}

    combined_skills = user_profile["skills"] + user_profile["jobs"]

    if user_profile.get('current_role'):
       combined_skills.append(user_profile["current_role"])

    if user_profile.get('skill_gaps'):
       combined_skills.append(user_profile["skill_gaps"])

    if user_profile.get('career_ambitions'):
       combined_skills.append(user_profile["career_ambitions"])

    for skill in combined_skills:
        if skill in online_resources:
          recommendations["courses"].extend(online_resources[skill].get("courses",[]))
          recommendations["videos"].extend(online_resources[skill].get("videos",[]))

    for job_title in user_profile["jobs"]:
      if job_title in job_openings:
          recommendations["jobs"].extend(job_openings[job_title])
      if job_title in job_openings:
         recommendations["jobs"].extend(job_openings[job_title])
    if user_profile.get("career_ambitions") and  user_profile.get("career_ambitions") in job_openings:
         recommendations["jobs"].extend(job_openings[user_profile.get("career_ambitions")])


    print(f"\nRecommendations (in {language}):")

    if recommendations['courses']:
      print("\nRecommended Courses:")
      for course in recommendations['courses']:
         print(f"- {course['name']} (link: {course['link']}, platform: {course['platform']})")

    if recommendations['videos']:
      print("\nRecommended Videos:")
      for video in recommendations['videos']:
         print(f"- {video['name']} (link: {video['link']}, platform: {video['platform']})")

    if recommendations['jobs']:
      print("\nJob Opportunities:")
      for job in recommendations['jobs']:
          print(f"- {job['title']} at {job['company']} (link: {job['link']})")


def prompt_user_and_recommend(user_profile):

    language = input("Please enter your preferred language (English, Bengali, Hindi, Spanish, French, etc.): ")
    print("Now let's ask some questions to better understand your needs:")

    current_role = input("What is your current role or job title? ")
    skill_gaps = input("What are the skill gaps you'd like to address? ")
    career_ambitions = input("What are your career ambitions? ")

    updated_profile = {
        "jobs":  user_profile["jobs"],
        "job_history": user_profile["job_history"],
        "skills": user_profile["skills"],
        "training": user_profile["training"],
        "feedback": user_profile["feedback"],
         "current_role": current_role,
         "skill_gaps": skill_gaps,
         "career_ambitions":career_ambitions
    }

    recommend_resources(updated_profile, language)


def should_continue():
    while True:
        choice = input("Do you want to continue with another email? (y/n): ").lower()
        if choice in ['y', 'n']:
            return choice == 'y'
        else:
            print("Invalid input. Please enter 'y' or 'n'.")


if __name__ == '__main__':
    gmail_service = get_gmail_service()
    email_data = fetch_all_emails(gmail_service, max_results=5) # You can change the max results
    df = pd.DataFrame(email_data)

    df[['jobs','job_history','skills','training','feedback']] = df['content'].apply(lambda content: pd.Series(extract_insights(content)))

    for index, row in df.iterrows():
        print(f"Message ID: {row['message_id']}")
        print(f"Jobs: {row['jobs']}")
        print(f"Job History: {row['job_history']}")
        print(f"Skills: {row['skills']}")
        print(f"Training: {row['training']}")
        print(f"Feedback: {row['feedback']}")
        print("-" * 30)

        user_profile = row[['jobs','job_history','skills','training','feedback']].to_dict()
        prompt_user_and_recommend(user_profile)
        if not should_continue():
            print("Exiting the program.")
            break