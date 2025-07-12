# Uncomment the required imports before adding the code

from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import logout
from django.contrib import messages
from datetime import datetime

from django.http import JsonResponse
from django.contrib.auth import login, authenticate
import logging
import json
from django.views.decorators.csrf import csrf_exempt
from .populate import initiate
from .models import CarMake, CarModel
from .restapis import get_request, analyze_review_sentiments


# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.

# Create a `login_request` view to handle sign in request
@csrf_exempt
def login_user(request):
    # Get username and password from request.POST dictionary
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    # Try to check if provide credential can be authenticated
    user = authenticate(username=username, password=password)
    data = {"userName": username}
    if user is not None:
        # If user is valid, call login method to login current user
        login(request, user)
        data = {"userName": username, "status": "Authenticated"}
    return JsonResponse(data)


def logout_request(request):
    logout(request) # Terminate user session
    data = {"userName":""} # Return empty username
    return JsonResponse(data)

@csrf_exempt
def registration(request):
    context = {}

    # Load JSON data from the request body
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    first_name = data['firstName']
    last_name = data['lastName']
    email = data['email']
    username_exist = False
    email_exist = False
    try:
        # Check if user already exists
        User.objects.get(username=username)
        username_exist = True
    except:
        # If not, simply log this is a new user
        logger.debug("{} is new user".format(username))

    # If it is a new user
    if not username_exist:
        # Create user in auth_user table
        user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,password=password, email=email)
        # Login the user and redirect to list page
        login(request, user)
        data = {"userName":username,"status":"Authenticated"}
        return JsonResponse(data)
    else :
        data = {"userName":username,"error":"Already Registered"}
        return JsonResponse(data)

def get_cars(request):
    # First check if we need to populate the database
    if CarMake.objects.count() == 0 or CarModel.objects.count() == 0:
        initiate()  # This will populate both makes and models
        
    # Get all car models with their related makes
    car_models = CarModel.objects.select_related('car_make').all()
    
    # Prepare the response data
    cars = []
    for car_model in car_models:
        cars.append({
            "CarModel": car_model.name,
            "CarMake": car_model.car_make.name,
            "Year": car_model.year,
            "Type": car_model.get_type_display(),
            "DealerId": car_model.dealer_id
        })
    
    return JsonResponse({"CarModels": cars})


# Update the `get_dealerships` view to render list of dealerships
def get_dealerships(request, state="All"):
    try:
        if state == "All":
            endpoint = "/fetchDealers"
        else:
            endpoint = f"/fetchDealers/{state}"
        
        dealerships = get_request(endpoint)
        
        if isinstance(dealerships, list):
            return JsonResponse({"status": 200, "dealers": dealerships})
        else:
            return JsonResponse({"status": 404, "message": "No dealerships found"}, status=404)
            
    except Exception as e:
        logger.error(f"Error fetching dealerships: {str(e)}")
        return JsonResponse({"status": 500, "message": str(e)}, status=500)

# Create a `get_dealer_details` view to render dealer details
def get_dealer_details(request, dealer_id):
    try:
        endpoint = f"/fetchDealer/{dealer_id}"
        dealer = get_request(endpoint)
        
        if dealer:
            return JsonResponse({"status": 200, "dealer": dealer})
        else:
            return JsonResponse({"status": 404, "message": "Dealer not found"}, status=404)
            
    except Exception as e:
        logger.error(f"Error fetching dealer details: {str(e)}")
        return JsonResponse({"status": 500, "message": str(e)}, status=500)

# Create a `get_dealer_reviews` view to render reviews of a dealer
def get_dealer_reviews(request, dealer_id):
    try:
        endpoint = f"/fetchReviews/dealer/{dealer_id}"
        reviews = get_request(endpoint)
        
        if isinstance(reviews, list):
            for review in reviews:
                if 'review' in review:
                    sentiment = analyze_review_sentiments(review['review'])
                    review['sentiment'] = sentiment.get('sentiment', 'neutral')
                else:
                    review['sentiment'] = 'neutral'
                    
            return JsonResponse({"status": 200, "reviews": reviews})
        else:
            return JsonResponse({"status": 404, "message": "No reviews found"}, status=404)
            
    except Exception as e:
        logger.error(f"Error fetching dealer reviews: {str(e)}")
        return JsonResponse({"status": 500, "message": str(e)}, status=500)

# Create a `add_review` view to submit a review
@csrf_exempt
def add_review(request):
    if request.method != "POST":
        return JsonResponse({"status": 405, "message": "Method not allowed"}, status=405)
    
    try:
        if not request.user.is_authenticated:
            return JsonResponse({"status": 401, "message": "Unauthorized"}, status=401)
        
        data = json.loads(request.body)
        required_fields = ['dealership', 'review', 'purchase']
        
        if not all(field in data for field in required_fields):
            return JsonResponse({"status": 400, "message": "Missing required fields"}, status=400)
        
        # Prepare review data
        review_data = {
            "id": data.get('id', ""),  # Will be generated by backend if not provided
            "name": f"{request.user.first_name} {request.user.last_name}",
            "dealership": data['dealership'],
            "review": data['review'],
            "purchase": data['purchase'],
            "purchase_date": data.get('purchase_date', ""),
            "car_make": data.get('car_make', ""),
            "car_model": data.get('car_model', ""),
            "car_year": data.get('car_year', ""),
        }
        
        # Call the API to add review
        response = post_request("/insert_review", review_data)
        
        if response.get('status') == 200:
            return JsonResponse({"status": 200, "message": "Review added successfully"})
        else:
            return JsonResponse({"status": 400, "message": response.get('error', 'Failed to add review')}, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({"status": 400, "message": "Invalid JSON data"}, status=400)
    except Exception as e:
        logger.error(f"Error adding review: {str(e)}")
        return JsonResponse({"status": 500, "message": str(e)}, status=500)