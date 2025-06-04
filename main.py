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

# Use the Mistral Large model instead of LLaMA
MODEL_ID = os.getenv("MODEL_ID", "mistral.mistral-large-2402-v1:0")

# New: load AWS access/secret key
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is missing. Ensure it is set in the .env file.")
if not AWS_REGION:
    raise RuntimeError("AWS_REGION is missing. Ensure it is set in the .env file.")
if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
    raise RuntimeError("AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be set in the .env file.")

# Initialize AWS Bedrock client with explicit credentials
try:
    bedrock_client = boto3.client(
        "bedrock-runtime",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
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
    "Which class are you in and where do you study?",
    "What job or career do you dream of? Why do you like it?",
    "How do you learn new things about your favorite subject or career?"
]

right_questions = [
    "When you have to learn something or make a choice, what do you usually do? (Like ask someone, search online, or try it yourself?)",
    "Can you share one thing that changed how you think or helped you see something in a new way? (Like a story, movie, person, or event)"
]


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    request.session.clear()
    request.session['left_question_index'] = 0
    request.session['right_question_index'] = 0
    request.session['user_responses'] = []
    request.session['current_phase'] = "left"  # Start with left questions
    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "intro_message": "Hi I am Naavi, your personal coach and navigator for higher education...😊"
        }
    )

@app.post("/process_chat")
async def process_chat(request: Request, user_input: str = Form(...)):
    user_responses = request.session.get('user_responses', [])
    current_phase = request.session.get('current_phase', "left")

    if current_phase == "left":
        question_index = request.session.get('left_question_index', 0)
        if question_index > 0:
            user_responses.append({
                "container": "left",
                "question": left_questions[question_index - 1],
                "response": user_input
            })
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
            user_responses.append({
                "container": "right",
                "question": right_questions[question_index - 1],
                "response": user_input
            })
        if question_index < len(right_questions):
            next_question = right_questions[question_index]
            request.session['right_question_index'] = question_index + 1
            return JSONResponse({'question': next_question, 'container': 'right'})
        else:
            # All questions answered: persist and show “Create Pathway” button
            request.session['user_responses'] = user_responses
            return JSONResponse({
                'response': "Thank you for providing the information. Please click the 'Create a Pathway' button to proceed.",
                'show_pathway_button': True
            })

@app.get("/generate_pathway", response_class=HTMLResponse)
async def generate_pathway(request: Request):
    user_responses = request.session.get('user_responses', [])
    if not user_responses:
        return templates.TemplateResponse(
            "pathway.html", {"request": request, "pathway_response": "No user responses provided."}
        )
    
    try:
        raw_response = await get_ai_response(user_responses)
        pathways = format_response(raw_response)
        return templates.TemplateResponse(
            "pathway.html", {"request": request, "pathway_response": pathways}
        )
    except Exception as e:
        return templates.TemplateResponse(
            "pathway.html", {"request": request, "pathway_response": f"Error generating pathways: {e}"}
        )

async def get_ai_response(user_responses):
    # Build a simple “User information” block instead of embedding “user\n” tags.
    user_info_lines = []
    for r in user_responses:
        # We know r["question"] is the question text, and r["response"] is what the user replied
        user_info_lines.append(f"- {r['question']}\n  -> {r['response']}")
    user_info = "\n".join(user_info_lines)

    # Core instruction that asks for three distinct pathways
    final_prompt = """
Based on the following user information, generate three distinct pathways for achieving the user's educational and career goals. Each pathway should be clearly separated and include step-by-step guidance. The output must follow exactly this structure:

Pathway 1: [Title]
Step 1
Step 2
Step 3
Step 4
Step 5
Step 6
Step 7
Step 8

Pathway 2: [Title]
Step 1
Step 2
Step 3
Step 4
Step 5
Step 6
Step 7
Step 8

Pathway 3: [Title]
Step 1
Step 2
Step 3
Step 4
Step 5
Step 6
Step 7
Step 8
""".strip()

    # Combine “User information” + instruction inside Mistral’s <s>[INST] … [/INST] wrapper
    # Note: do NOT prefix with "user\n"; simply present the user_info as plain text.
    mistral_prompt = (
        "<s>[INST] "
        "User information:\n"
        f"{user_info}\n\n"
        f"{final_prompt} "
        "[/INST]"
    )

    try:
        request_body = {
            "prompt": mistral_prompt,
            "max_tokens": 8192,
            "temperature": 0.7,
            "top_p": 0.9
        }
        response = bedrock_client.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(request_body)
        )
        model_response = json.loads(response["body"].read())
        # Mistral’s generated text is at outputs[0]["text"]
        return model_response["outputs"][0]["text"]
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Error generating AI response: {e}")

def format_response(raw_response):
    if not raw_response:
        return "No response from the AI model."
    
    lines = raw_response.split('\n')
    formatted_response = []
    current_pathway = None

    for line in lines:
        if line.strip().startswith("Pathway "):
            # If we were already collecting a previous block, append it now
            if current_pathway is not None:
                formatted_response.append(current_pathway)

            # Create a new pathway object
            current_pathway = {
                "title": line.strip(),
                "steps": []
            }

        elif line.strip() and current_pathway is not None:
            current_pathway["steps"].append(line.strip())

    # Append the final pathway (even if it has zero steps)
    if current_pathway is not None:
        formatted_response.append(current_pathway)

    return formatted_response

    if not raw_response:
        return "No response from the AI model."
    
    lines = raw_response.split('\n')
    formatted_response = []
    current_pathway = {"title": "", "steps": []}
    
    for line in lines:
        if line.startswith("Pathway "):
            # If we were collecting the previous block, append it (only if it has steps)
            if current_pathway["title"] and current_pathway["steps"]:
                formatted_response.append(current_pathway)
            current_pathway = {"title": line.strip(), "steps": []}
        elif line.strip():
            # Anything non-blank after a "Pathway X:" line is considered a step
            current_pathway["steps"].append(line.strip())
    
    # Append the last pathway if it has at least one step
    if current_pathway["title"] and current_pathway["steps"]:
        formatted_response.append(current_pathway)
    
    return formatted_response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
