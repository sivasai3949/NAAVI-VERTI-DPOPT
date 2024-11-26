from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
import boto3
import json
import os
from botocore.exceptions import ClientError

app = FastAPI()

# Load environment variables from .env file
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
MODEL_ID = os.getenv("MODEL_ID", "meta.llama3-70b-instruct-v1:0")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is missing. Ensure it is set in the .env file.")
if not AWS_REGION:
    raise RuntimeError("AWS_REGION is missing. Ensure it is set in the .env file.")

# Initialize AWS Bedrock client
try:
    bedrock_client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
except Exception as e:
    raise RuntimeError(f"Failed to initialize AWS Bedrock client: {e}")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Enable session handling
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Left and Right questions
left_questions = [
    "Could you provide a comprehensive overview of your education, highlighting what inspires your choices?",
    "Which specific disciplines or career dreams ignite your passion along with the skills or competencies you aim for in the future?",
    "How do you stay informed about emerging trends and advancements in the fields of your interest?"
]

right_questions = [
    "Describe your key personality traits that best describe and influence your learning style and decision-making process?",
    "What is your perspective or understanding of a viewpoint? Specify any experience or an impactful moment that broadened your understanding."
]

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    request.session.clear()
    request.session['left_question_index'] = 0
    request.session['right_question_index'] = 0
    request.session['user_responses'] = []
    request.session['current_phase'] = "left"  # Start with left questions
    return templates.TemplateResponse("chat.html", {"request": request, "intro_message": "Hi I am Naavi, your personal coach and navigator for higher education...😊"})

@app.post("/process_chat")
async def process_chat(request: Request, user_input: str = Form(...)):
    user_responses = request.session.get('user_responses', [])
    current_phase = request.session.get('current_phase', "left")

    if current_phase == "left":
        question_index = request.session.get('left_question_index', 0)
        if question_index > 0:
            user_responses.append({"container": "left", "question": left_questions[question_index - 1], "response": user_input})
        if question_index < len(left_questions):
            next_question = left_questions[question_index]
            request.session['left_question_index'] = question_index + 1
            return JSONResponse({'question': next_question, 'container': 'left'})
        else:
            request.session['current_phase'] = "right"  # Switch to right questions
            question_index = request.session.get('right_question_index', 0)
            next_question = right_questions[question_index]
            request.session['right_question_index'] = question_index + 1
            return JSONResponse({'question': next_question, 'container': 'right'})

    elif current_phase == "right":
        question_index = request.session.get('right_question_index', 0)
        if question_index > 0:
            user_responses.append({"container": "right", "question": right_questions[question_index - 1], "response": user_input})
        if question_index < len(right_questions):
            next_question = right_questions[question_index]
            request.session['right_question_index'] = question_index + 1
            return JSONResponse({'question': next_question, 'container': 'right'})
        else:
            request.session['user_responses'] = user_responses
            return JSONResponse({'response': "Thank you for providing the information. Please click the 'Create a Pathway' button to proceed.", 'show_pathway_button': True})

@app.get("/generate_pathway", response_class=HTMLResponse)
async def generate_pathway(request: Request):
    user_responses = request.session.get('user_responses', [])
    if not user_responses:
        return templates.TemplateResponse("pathway.html", {"request": request, "pathway_response": "No user responses provided."})
    
    try:
        raw_response = await get_ai_response(user_responses)
        pathways = format_response(raw_response)
        return templates.TemplateResponse("pathway.html", {"request": request, "pathway_response": pathways})
    except Exception as e:
        return templates.TemplateResponse("pathway.html", {"request": request, "pathway_response": f"Error generating pathways: {e}"})

async def get_ai_response(user_responses):
    messages = "\n".join([f"user\n{response['response']}\n" for response in user_responses])
    final_prompt = """ Based on the information provided, generate three distinct pathways for achieving the user's educational and career goals. Each pathway should be clearly separated and include step-by-step guidance. The output should be structured as follows: 
    Pathway 1: [Title] 
    Step 1 
    Step 2 
    Step 3 
    Step 4 
    Step 5 
    Pathway 2: [Title] 
    Step 1 
    Step 2 
    Step 3 
    Step 4 
    Step 5 
    Pathway 3: [Title] 
    Step 1 
    Step 2 
    Step 3 
    Step 4 
    Step 5 """
    messages += f"assistant\n{final_prompt}\n"
    
    try:
        native_request = {
            "prompt": messages,
            "max_gen_len": 2048,
            "temperature": 0.6,
        }
        response = bedrock_client.invoke_model(modelId=MODEL_ID, body=json.dumps(native_request))
        model_response = json.loads(response["body"].read())
        return model_response["generation"]
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Error generating AI response: {e}")

def format_response(raw_response):
    if not raw_response:
        return "No response from the AI model."
    
    lines = raw_response.split('\n')
    formatted_response = []
    current_pathway = {"title": "", "steps": []}
    
    for line in lines:
        if line.startswith("Pathway "):
            if current_pathway["steps"]:
                formatted_response.append(current_pathway)
            current_pathway = {"title": line, "steps": []}
        elif line.strip():
            current_pathway["steps"].append(line.strip())
    
    if current_pathway["steps"]:
        formatted_response.append(current_pathway)
    
    return formatted_response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
