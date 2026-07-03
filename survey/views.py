from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import SignupForm
from .models import Assessment

import pickle
import os

from groq import Groq
from django.conf import settings
from django.db.models import Avg
from django.http import JsonResponse

def get_client():

    api_key = settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY")

    if not api_key:
        raise Exception("GROQ_API_KEY environment variable not found.")

    return Groq(api_key=api_key)



BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

depression_model_path = os.path.join(BASE_DIR, 'survey', 'model.pkl')
vectorizer_path = os.path.join(BASE_DIR, 'survey', 'vectorizer.pkl')

with open(depression_model_path, 'rb') as f:
    ml_model = pickle.load(f)

with open(vectorizer_path, 'rb') as f:
    vectorizer = pickle.load(f)


def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('login')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})
    
def login_view(request):
    if request.method == 'POST':
        # Get username and password from the POST data
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home') # Redirect to survey after successful login
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password'})
            
    return render(request, 'login.html')


@login_required
def home(request):

    assessments = Assessment.objects.filter(
        user=request.user
    ).order_by('-created_at')

    latest = assessments.first()

    return render(
        request,
        'home.html',
        {
            'latest': latest,
            'assessments': assessments[:5]
        }
    )

def generate_support_message(
    test_type,
    score,
    severity,
    user_text=""
):
    try:

        prompt = f"""
        You are a compassionate AI mental wellness companion.

        Assessment Type: {test_type}
        Score: {score}
        Severity Category: {severity}

        User Reflections:
        {user_text}

        Rules:
        - Do NOT diagnose any mental illness.
        - Do NOT provide medical advice.
        - Do NOT prescribe medication.
        - Do NOT claim the user has a disorder.
        - Do NOT recommend medication or treatment plans.

        Your role:
        - Acknowledge the user's effort.
        - Provide emotional support.
        - Offer encouragement.
        - Suggest self-reflection.
        - Remind them support is available if needed.

        Keep the response warm, supportive, and under 200 words.
        """

        client = get_client()

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        print("AI SUPPORT ERROR:", e)

        return (
            "Thank you for completing the assessment. "
            "Taking time to reflect on your wellbeing is an important step. "
            "Be kind to yourself and remember that support is always available."
        )

def survey(request):
    if request.method == "POST":

        if request.POST.get("q10") != "0":
            # Send them back to the form with an error message
            return render(request, "surveyform.html", {"error": "You must agree to the terms to see results."})


        total_score = 0
        # Calculate score from q1 through q9
        for i in range(1, 10):
            total_score += int(request.POST.get(f"q{i}", 0))

        text_input=" ".join([
            request.POST.get(f"q{i}_text","") for i in range(1,10)
        ]).strip()

        print("TEXT INPUT",text_input)
    
        if text_input.strip()=="":
            ml_prediction="no text input provided"
        else:
            text_vector=vectorizer.transform([text_input])
            ml_prediction=ml_model.predict(text_vector)[0]
            

        responses={
            f"q{i}":{
                "score":int(request.POST.get(f"q{i}",0)),
                "text":request.POST.get(f"q{i}_text","")
            }
            for i in range(1,10)
        }

        
        # Determine level based on score
        if total_score <= 4:
            level = "Minimal"
        elif total_score <= 9:
            level = "Mild"
        elif total_score <= 14:
            level = "Moderate"
        elif total_score <= 19:
            level = "Moderately Severe"
        else:
            level = "Severe"

        # Save to database
        # SurveyResult.objects.create(
        #     user=request.user,
        #     score=total_score,
        #     level=level
        # )

        Assessment.objects.create(
            user=request.user,
            test_type="PHQ9",
            responses=responses,
            total_score=total_score,
            severity=level
        )
       

        ai_message = generate_support_message(
            "PHQ9",
            total_score,
            level,
            text_input
        )
                

        return render(
            request,
            "result.html",
            {
                "score": total_score,
                "level": level,
                "ml_prediction": ml_prediction,
                "ai_message": ai_message
            }
        )
                
        
    # If GET request, show the survey form
    return render(request, "surveyform.html")

def bdisurvey(request):
    if request.method == "POST":

        if request.POST.get("q22") != "0":
            # Send them back to the form with an error message
            return render(request, "bdiform.html", {"error": "You must agree to the terms to see results."})


        total_score = 0
        # Calculate score from q1 through q9
        for i in range(1, 21):
            total_score += int(request.POST.get(f"q{i}", 0))

        text_input=" ".join([
            request.POST.get(f"q{i}_text","") for i in range(1,21)
        ]).strip()

        print("TEXT INPUT",text_input)

        if text_input.strip()=="":
            ml_prediction="no text input provided"
        else:
            text_vector=vectorizer.transform([text_input])
            ml_prediction=ml_model.predict(text_vector)[0]
            

        responses = {
            f"q{i}":{ 
                "score":int(request.POST.get(f"q{i}", 0)),
                "text":request.POST.get(f"q{i}_text","")
            }
            for i in range(1, 21)
        }
                
        # Determine level based on score
        if total_score>=1 and total_score <= 10:
            level = "These ups and downs are considered normal "
        elif total_score>=11 and total_score <= 16:
            level = "Mild mood disturbance  "
        elif total_score>=17 and total_score <=20:
            level = "Borderline clinical depression"
        elif total_score>=21 and total_score <= 30:
            level = "Moderate depression "
        elif total_score>=31 and total_score <=40:
            level = "Severe depression   "
        else:
            level = "Extreme depression "

        # Save to database
        Assessment.objects.create(
            user=request.user,
            test_type="BDI",
            responses=responses,
            total_score=total_score,
            severity=level
        )
        ai_message = generate_support_message(
            "BDI",
            total_score,
            level,
            text_input
        )
        return render(
            request,
            "result.html", 
            {
                "score": total_score, 
                "level": level,
                "ml_prediction":ml_prediction,
                "ai_message": ai_message
                }
            
            )
        
        
    # If GET request, show the survey form
    return render(request, "bdiform.html")

from django.http import JsonResponse
from django.shortcuts import render
@login_required
def chatbot(request):
    # Initialize chat history once
    if "chat_history" not in request.session:
        request.session["chat_history"] = []

    if request.method == "POST":

        # Read message from form
        user_message = request.POST.get("message", "").strip()

        if not user_message:
            return JsonResponse({
                "reply": "Please type a message."
            })

        conversation = request.session["chat_history"]

        # Save user message
        conversation.append({
            "role": "user",
            "content": user_message
        })

        # Keep only last 20 messages (10 exchanges)
        conversation = conversation[-20:]

        messages = [
            {
                "role": "system",
                "content": """
You are Serenity, an empathetic AI mental wellness companion.

Rules:
- Never diagnose mental illnesses.
- Never claim the user has a disorder.
- Never prescribe medication.
- Never replace psychologists or psychiatrists.
- Be warm, supportive and conversational.
- Remember previous conversation in this session.
- Ask thoughtful follow-up questions.
- Avoid repeating greetings.
- If the user mentions self-harm or suicide, encourage immediate professional or emergency support.
"""
            }
        ]

        messages.extend(conversation)

        try:

            client = get_client()

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.7,
                max_tokens=300
            )

            bot_reply = response.choices[0].message.content

            # Save assistant reply
            conversation.append({
                "role": "assistant",
                "content": bot_reply
            })

            request.session["chat_history"] = conversation
            request.session.modified = True

            return JsonResponse({
                "reply": bot_reply
            })

        except Exception as e:
            import traceback
            traceback.print_exc()

            return JsonResponse({
                "reply": f"Groq Error: {str(e)}"
            })

    return render(request, "chatbot.html")

def consultation(request):
    return render(request, "consultation.html")

@login_required
def analytics(request):

    assessments = Assessment.objects.filter(
        user=request.user
    ).order_by('-created_at')

    total_assessments = assessments.count()

    latest = assessments.first()

    average_score = assessments.aggregate(
        Avg('total_score')
    )['total_score__avg']

    severity_counts = {}

    for assessment in assessments:
        severity = assessment.severity

        if severity in severity_counts:
            severity_counts[severity] += 1
        else:
            severity_counts[severity] = 1

    context = {
        'total_assessments': total_assessments,
        'latest': latest,
        'average_score': round(average_score, 2) if average_score else 0,
        'severity_counts': severity_counts,
        'assessments': assessments,
    }

    return render(
        request,
        "analytics.html",
        context
    )