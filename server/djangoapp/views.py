from django.contrib.auth import logout
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import logging
import json
from .populate import initiate
from .models import CarMake, CarModel
from .restapis import get_request, post_review, analyze_review_sentiments


logger = logging.getLogger(__name__)


@csrf_exempt
def login_user(request):
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    user = authenticate(username=username, password=password)
    data = {"userName": username}
    if user is not None:
        login(request, user)
        data = {"userName": username, "status": "Authenticated"}
    return JsonResponse(data)


def logout_request(request):
    logout(request)
    data = {"userName": ""}
    return JsonResponse(data)


@csrf_exempt
def registration(request):
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    first_name = data['firstName']
    last_name = data['lastName']
    email = data['email']
    username_exist = False

    try:
        User.objects.get(username=username)
        username_exist = True
    except Exception:
        logger.debug("%s is new user", username)

    if not username_exist:
        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password,
            email=email
        )
        login(request, user)
        data = {"userName": username, "status": "Authenticated"}
        return JsonResponse(data)
    else:
        data = {"userName": username, "error": "Already Registered"}
        return JsonResponse(data)


def get_cars(request):
    if CarMake.objects.count() == 0 or CarModel.objects.count() == 0:
        initiate()

    car_models = CarModel.objects.select_related('car_make').all()
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


def get_dealerships(request, state="All"):
    try:
        endpoint = (
                        "/fetchDealers"
                        if state == "All"
                        else f"/fetchDealers/{state}"
                    )
        dealerships = get_request(endpoint)

        if isinstance(dealerships, list):
            return JsonResponse({"status": 200, "dealers": dealerships})
        return JsonResponse(
            {"status": 404, "message": "No dealerships found"}, status=404)
    except Exception as e:
        logger.error("Error fetching dealerships: %s", str(e))
        return JsonResponse({"status": 500, "message": str(e)}, status=500)


def get_dealer_details(request, dealer_id):
    try:
        endpoint = f"/fetchDealer/{dealer_id}"
        dealer = get_request(endpoint)

        if dealer:
            return JsonResponse({"status": 200, "dealer": dealer})
        return JsonResponse(
            {"status": 404, "message": "Dealer not found"}, status=404)
    except Exception as e:
        logger.error("Error fetching dealer details: %s", str(e))
        return JsonResponse({"status": 500, "message": str(e)}, status=500)


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
        return JsonResponse(
            {"status": 404, "message": "No reviews found"}, status=404)
    except Exception as e:
        logger.error("Error fetching dealer reviews: %s", str(e))
        return JsonResponse({"status": 500, "message": str(e)}, status=500)


@csrf_exempt
def add_review(request):
    if request.method != "POST":
        return JsonResponse(
            {"status": 405, "message": "Method not allowed"}, status=405)

    try:
        if not request.user.is_authenticated:
            return JsonResponse(
                {"status": 401, "message": "Unauthorized"}, status=401)

        data = json.loads(request.body)
        required_fields = ['dealership', 'review', 'purchase']

        if not all(field in data for field in required_fields):
            return JsonResponse(
                {
                    "status": 400,
                    "message": "Missing required fields"
                },
                status=400)

        name = {
                    request.user.get_full_name().strip()
                    or request.user.username
                }

        review_data = {
            "id": data.get('id', ""),
            "name": name,
            "dealership": data['dealership'],
            "review": data['review'],
            "purchase": data['purchase'],
            "purchase_date": data.get('purchase_date', ""),
            "car_make": data.get('car_make', ""),
            "car_model": data.get('car_model', ""),
            "car_year": data.get('car_year', ""),
        }

        response = post_review(review_data)

        if response and '_id' in response:
            return JsonResponse({
                "status": 200,
                "message": "Review added successfully",
                "review_id": str(response['_id'])
            })
        error_msg = {
                        response.get('error', 'Failed to add review') 
                        if response else 'No response'
                    }
        return JsonResponse(
            {"status": 400, "message": error_msg}, status=400)
    except json.JSONDecodeError:
        return JsonResponse(
            {"status": 400, "message": "Invalid JSON data"}, status=400)
    except Exception as e:
        logger.error("Error adding review: %s", str(e))
        return JsonResponse({"status": 500, "message": str(e)}, status=500)
