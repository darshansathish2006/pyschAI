from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import SignupForm
from .models import Assessment

import pickle
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

model_path = os.path.join(BASE_DIR, 'survey', 'model.pkl')
vectorizer_path = os.path.join(BASE_DIR, 'survey', 'vectorizer.pkl')

with open(model_path, 'rb') as f:
    model = pickle.load(f)

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
    return render(request,'home.html')

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
            ml_prediction=model.predict(text_vector)[0]
            

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
        

        return render(request, "result.html", {
            "score": total_score,
              "level": level,
              "ml_prediction":ml_prediction
              })
        
        
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

        responses = {
            f"q{i}": int(request.POST.get(f"q{i}", 0))
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
            test_type="BDI",
            responses=responses,
            total_score=total_score,
            severity=level
        )
        return render(request, "result.html", {"score": total_score, "level": level})
        
        
    # If GET request, show the survey form
    return render(request, "bdiform.html")

