import json
import logging
import re
import googlemaps
from datetime import datetime
import hashlib 
import folium
from django.shortcuts import render
from pymongo import MongoClient
from django.conf import settings
from .utils import hash_password, verify_password, create_jwt_token, verify_jwt_token, require_auth
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import User, Item, AuthToken
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from googlemaps.convert import decode_polyline
import pandas as pd
import random
from geopy.distance import geodesic
import time
import atexit

gmaps = googlemaps.Client(key='AIzaSyDXRT50QvC6eu54VSj2mcaVF4VFUeoQx5Y')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# MongoDB connection with proper cleanup
try:
    client = MongoClient(settings.MONGO_URI)
    client.server_info()
    db = client[settings.MONGO_DB_NAME]
    logger.info("MongoDB connection successful")
    MONGO_AVAILABLE = True
except Exception as e:
    logger.error(f"MongoDB connection failed: {str(e)}")
    db = None
    MONGO_AVAILABLE = False

def cleanup_mongo():
    """Ensure MongoDB client closes cleanly on shutdown"""
    if 'client' in globals() and client:
        logger.info("Closing MongoDB connection...")
        client.close()

atexit.register(cleanup_mongo)  # Register cleanup function

def check_mongo_availability():
    if not MONGO_AVAILABLE:
        return JsonResponse({"error": "Database unavailable"}, status=503)
    return None

@csrf_exempt
def validate_identifier(identifier: str) -> tuple[bool, str]:
    identifier = identifier.strip()
    if not identifier:
        return False, "Email or phone number is required"
    if "@" in identifier:
        if not re.match(r"[^@]+@[^@]+\.[^@]+", identifier):
            return False, "Invalid email format"
        return True, ""
    if identifier.isdigit() and len(identifier) >= 10:
        return True, ""
    return False, "Invalid email or phone number format"

@csrf_exempt
def validate_password(password: str) -> tuple[bool, str]:
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters"
    return True, ""

@csrf_exempt
def require_auth(view_func):
    def wrapper(request, *args, **kwargs):
        token = request.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            return JsonResponse({"error": "Authentication required"}, status=401)
        token = token.split(" ")[1]
        payload = AuthToken.verify_token(token)
        if not payload:
            return JsonResponse({"error": "Invalid or expired token"}, status=401)
        request.user_identifier = payload["email"]
        return view_func(request, *args, **kwargs)
    return wrapper

@csrf_exempt
def signup(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    try:
        mongo_error = check_mongo_availability()
        if mongo_error:
            return mongo_error
        data = json.loads(request.body)
        identifier = data.get("identifier", "").strip()
        password = data.get("password", "").strip()
        name = data.get("name", "").strip()
        is_valid, error = validate_identifier(identifier)
        if not is_valid:
            return JsonResponse({"error": error}, status=400)
        is_valid, error = validate_password(password)
        if not is_valid:
            return JsonResponse({"error": error}, status=400)
        if User.find_by_identifier(identifier):
            return JsonResponse({"error": "User already exists"}, status=400)
        user = User.create(identifier=identifier, password=password, name=name if name else None)
        return JsonResponse({
            "message": "Signup successful",
            "user": {"identifier": user.identifier, "name": user.name}
        }, status=201)
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)

@csrf_exempt
def login(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    try:
        mongo_error = check_mongo_availability()
        if mongo_error:
            return mongo_error
        data = json.loads(request.body)
        identifier = data.get("identifier", "").strip()
        password = data.get("password", "").strip()
        if not identifier or not password:
            return JsonResponse({"error": "Identifier and password required"}, status=400)
        user = User.find_by_identifier(identifier)
        if not user or not user.verify_password(password):
            return JsonResponse({"error": "Invalid credentials"}, status=401)
        token = AuthToken.create_token(identifier)
        return JsonResponse({
            "message": "Login successful",
            "token": token,
            "user": {"identifier": user.identifier, "name": user.name}
        }, status=200)
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)

@csrf_exempt
def logout(request):
    if request.method == "POST":
        return JsonResponse({"message": "Logout successful"}, status=200)
    return JsonResponse({"error": "Method not allowed"}, status=405)

@require_auth
@csrf_exempt
def history(request):
    mongo_error = check_mongo_availability()
    if mongo_error:
        return mongo_error
        
    if request.method == "GET":
        try:
            # Get the user_identifier from the request (set by require_auth decorator)
            user_identifier = request.user_identifier
            
            # Find the user in database
            user = User.find_by_identifier(user_identifier)
            if not user:
                return JsonResponse({"error": "User not found"}, status=404)
                
            # Get last 10 history entries, sorted by timestamp (newest first)
            history_entries = user.history[-10:][::-1]  # Get last 10 and reverse order
            
            # Format the response with only necessary fields
            formatted_history = [
                {
                    "source": entry.get("source", "Unknown"),
                    "destination": entry.get("destination", "Unknown"),
                    "timestamp": entry.get("timestamp"),
                    "restaurants_count": len(entry.get("full_restaurants", []))
                }
                for entry in history_entries
            ]
            
            return JsonResponse({
                "history": formatted_history,
                "message": "History retrieved successfully"
            }, status=200)
            
        except Exception as e:
            logger.error(f"History error: {str(e)}")
            return JsonResponse({"error": "Internal server error"}, status=500)
            
    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            source = data.get("source", "").strip()
            destination = data.get("destination", "").strip()
            
            if not source or not destination:
                return JsonResponse({"error": "Source and destination required"}, status=400)
                
            user = User.find_by_identifier(request.user_identifier)
            if not user:
                return JsonResponse({"error": "User not found"}, status=404)
                
            # Add to history with current timestamp
            user.add_history(source, destination)
            
            return JsonResponse({
                "message": "History updated successfully",
                "source": source,
                "destination": destination
            }, status=201)
            
        except Exception as e:
            logger.error(f"History update error: {str(e)}")
            return JsonResponse({"error": "Internal server error"}, status=500)
        
    elif request.method == "DELETE":
        try:
            user = User.find_by_identifier(request.user_identifier)
            if not user:
                return JsonResponse({"error": "User not found"}, status=404)

            data = json.loads(request.body) if request.body else {}
            timestamp = data.get("timestamp")

            if timestamp:  # Delete specific history entry
                result = user.collection.update_one(
                    {"identifier": request.user_identifier},
                    {"$pull": {"history": {"timestamp": timestamp}}}
                )
                if result.modified_count == 0:
                    return JsonResponse({"error": "History entry not found"}, status=404)
                return JsonResponse({"message": "History entry deleted successfully"}, status=200)
            else:  # Delete all history
                result = user.collection.update_one(
                    {"identifier": request.user_identifier},
                    {"$set": {"history": []}}
                )
                if result.modified_count == 0 and user.history:
                    return JsonResponse({"error": "No history to delete or update failed"}, status=400)
                return JsonResponse({"message": "All history deleted successfully"}, status=200)

        except Exception as e:
            logger.error(f"History delete error: {str(e)}")
            return JsonResponse({"error": "Internal server error"}, status=500)
            
    return JsonResponse({"error": "Method not allowed"}, status=405)

@require_auth
@csrf_exempt
def items(request):
    mongo_error = check_mongo_availability()
    if mongo_error:
        return mongo_error
    if request.method == "GET":
        try:
            items = Item.find_all()
            return JsonResponse({"items": items}, status=200)
        except Exception as e:
            logger.error(f"Items error: {str(e)}")
            return JsonResponse({"error": "Internal server error"}, status=500)
    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            name = data.get("name", "").strip()
            description = data.get("description", "").strip()
            if not name or not description:
                return JsonResponse({"error": "Name and description required"}, status=400)
            item = Item.create(name=name, description=description, created_by=request.user_identifier)
            return JsonResponse({
                "message": "Item created",
                "item": {"name": item.name, "description": item.description, "created_at": item.created_at, "created_by": item.created_by}
            }, status=201)
        except Exception as e:
            logger.error(f"Items error: {str(e)}")
            return JsonResponse({"error": "Internal server error"}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@require_auth
@csrf_exempt
@cache_page(60 * 5)
def find_restaurants(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    try:
        logger.info("Starting find_restaurants request")
        mongo_error = check_mongo_availability()
        if mongo_error:
            logger.error("MongoDB unavailable")
            return mongo_error
        data = json.loads(request.body)
        source = data.get("source")
        destination = data.get("destination")
        sort_choice = data.get("sort_choice", "3")
        food_preference = data.get("food_preference", "").strip().lower()
        logger.info(f"Processing request: source={source}, destination={destination}")

        if not source or not destination:
            logger.error("Source or destination missing")
            return JsonResponse({"error": "Source and destination required"}, status=400)

        # Geocode source and destination
        logger.info("Geocoding source and destination")
        source_result = gmaps.geocode(source)
        destination_result = gmaps.geocode(destination)
        if not isinstance(source_result, list) or len(source_result) == 0:
            return JsonResponse({"error": "Invalid source location response"}, status=400)
        if not isinstance(destination_result, list) or len(destination_result) == 0:
            return JsonResponse({"error": "Invalid destination location response"}, status=400)
        if not source_result or not destination_result:
            logger.error("Invalid source or destination")
            return JsonResponse({"error": "Invalid source or destination"}, status=400)
        source_location = source_result[0]['geometry']['location']
        destination_location = destination_result[0]['geometry']['location']
        logger.info(f"Source location: {source_location}, Destination location: {destination_location}")

        # Get directions with traffic
        logger.info("Fetching directions")
        directions_result = gmaps.directions(
            origin=source,
            destination=destination,
            mode="driving",
            departure_time=datetime.now(),
            traffic_model='best_guess',
            alternatives=True
        )
        logger.info(f"Directions result: {len(directions_result)} routes found")
        best_route_index = 0
        min_duration = float('inf')
        for i, route in enumerate(directions_result):
            duration = route['legs'][0]['duration_in_traffic']['value']
            if duration < min_duration:
                min_duration = duration
                best_route_index = i
                
        if not isinstance(directions_result, list) or len(directions_result) == 0:
            return JsonResponse({"error": "No routes found"}, status=400)
        
        best_route = directions_result[best_route_index]
        best_route_steps = best_route['legs'][0]['steps']
        restaurant_list = []
        seen_place_ids = set()
        try:
          polyline_points = decode_polyline(best_route['overview_polyline']['points'])
          best_coordinates = [(point['lat'], point['lng']) for point in polyline_points]
        except (KeyError, TypeError) as e:
          logger.error(f"Error decoding polyline: {str(e)}")
          return JsonResponse({"error": "Could not decode route path"}, status=400)
      
        logger.info(f"Best route selected with {len(best_route_steps)} steps")

        def extract_road_names(instruction):
            clean_text = re.sub('<[^<]+?>', ' ', instruction).strip()
            patterns = [r"onto ([^<]+?)(?: toward| for| \.)", r"on ([^<]+?)(?: toward| for| \.)", r"Continue on ([^<]+?)(?: toward| for| \.)", r"Take ([^<]+?)(?: toward| for| \.)"]
            for pattern in patterns:
                match = re.search(pattern, clean_text)
                if match:
                    return match.group(1).strip()
            words = clean_text.split()
            for i in range(len(words)-1):
                if words[i].lower() in ['on', 'onto'] and i+1 < len(words):
                    potential_road = words[i+1]
                    if len(potential_road) > 2 and potential_road[0].isupper():
                        return potential_road
            return None

        road_segments = []
        for step in best_route_steps:
            road_name = extract_road_names(step['html_instructions']) if 'html_instructions' in step else None
            points = decode_polyline(step['polyline']['points'])
            coords = [(point['lat'], point['lng']) for point in points]
            distance = step.get('distance', {}).get('value', 0)
            num_points = max(1, int(distance / 100000))
            step_size = max(1, len(coords) // num_points)
            # In the road_segments creation loop:
            for i in range(0, len(coords), step_size):
                road_segments.append({
                'coords': {'lat': coords[i][0], 'lng': coords[i][1]},  # Ensure dictionary format
                'road_name': road_name
              })
        logger.info(f"Generated {len(road_segments)} search points along the route")

        def calculate_distance_to_road(restaurant_coords, road_coords):
            min_distance = float('inf')
            restaurant_point = (restaurant_coords['lat'], restaurant_coords['lng'])
            for road_point in road_coords:
                distance = geodesic(restaurant_point, road_point).meters
                if distance < min_distance:
                    min_distance = distance
            return round(min_distance, 2)

        def calculate_travel_time_to_restaurant(gmaps_client, main_road_point, restaurant_location):
            try:
                directions = gmaps_client.directions(
                    origin=main_road_point,
                    destination=restaurant_location,
                    mode="driving",
                    departure_time=datetime.now(),
                    traffic_model='best_guess'
                )
                if directions and 'legs' in directions[0]:
                    duration = directions[0]['legs'][0]['duration_in_traffic']
                    return {
                        'text': duration['text'],
                        'value': duration['value']
                    }
                return {
                    'text': "Unknown",
                    'value': 0
                }
            except Exception as e:
                logger.error(f"Error calculating travel time: {str(e)}")
                return {
                    'text': "Error",
                    'value': 0
                }

        def find_nearest_road_point(restaurant_location, road_coordinates):
            min_distance = float('inf')
            nearest_point = None
            restaurant_point = (restaurant_location['lat'], restaurant_location['lng'])
            for road_point in road_coordinates:
                distance = geodesic(restaurant_point, road_point).meters
                if distance < min_distance:
                    min_distance = distance
                    nearest_point = road_point
            return nearest_point

        def get_restaurant_internal_traffic(gmaps_client, restaurant_id, restaurant_name):
            try:
                cache_key = f"internal_traffic_{restaurant_id}"
                cached_traffic = cache.get(cache_key)
                if cached_traffic:
                    logger.info(f"Using cached internal traffic for {restaurant_name}")
                    return cached_traffic

                place_details = gmaps_client.place(place_id=restaurant_id, fields=['name', 'place_id', 'current_opening_hours'])
                now = datetime.now()
                hour = now.hour
                day = now.weekday()
                is_open = False
                if 'current_opening_hours' in place_details['result']:
                    is_open = place_details['result']['current_opening_hours'].get('open_now', False)
                if not is_open:
                    result = (0, "CLOSED", "gray")
                else:
                    peak_hours = {
                        0: [(11, 14), (17, 20)], 1: [(11, 14), (17, 20)], 2: [(11, 14), (17, 20)],
                        3: [(11, 14), (17, 21)], 4: [(11, 15), (17, 22)], 5: [(10, 15), (17, 22)],
                        6: [(10, 15), (17, 21)]
                    }
                    in_peak = False
                    for start, end in peak_hours.get(day, []):
                        if start <= hour < end:
                            in_peak = True
                            break
                    if in_peak:
                        traffic_value = random.randint(70, 100)
                        status = "HIGH"
                        color = "red"
                    elif 6 <= hour <= 22:
                        traffic_value = random.randint(30, 69)
                        status = "MEDIUM"
                        color = "orange"
                    else:
                        traffic_value = random.randint(0, 29)
                        status = "LOW"
                        color = "green"
                    result = (traffic_value, status, color)

                cache.set(cache_key, result, 60 * 5)
                return result
            except Exception as e:
                logger.error(f"Error getting internal traffic for {restaurant_name}: {str(e)}")
                hour = datetime.now().hour
                if 11 <= hour <= 14 or 18 <= hour <= 21:
                    return random.randint(70, 100), "HIGH", "red"
                elif 6 <= hour <= 22:
                    return random.randint(30, 69), "MEDIUM", "orange"
                else:
                    return random.randint(0, 29), "LOW", "green"

        def calculate_total_traffic_score(road_traffic_seconds, internal_traffic_value):
            internal_traffic_seconds = internal_traffic_value * 10
            total_traffic_seconds = road_traffic_seconds + internal_traffic_seconds
            if total_traffic_seconds < 600:
                return total_traffic_seconds, "LOW", "green"
            elif total_traffic_seconds < 1200:
                return total_traffic_seconds, "MEDIUM", "orange"
            else:
                return total_traffic_seconds, "HIGH", "red"
            
        def fetch_restaurant_photos(place_id, max_photos=1):
             try:
                cache_key = f"restaurant_photos_{place_id}"
                cached_photos = cache.get(cache_key)
                if cached_photos:
                  return cached_photos
                place_details = gmaps.place(
                place_id=place_id,
                 fields=['photo']
                )
                photos = place_details.get('result', {}).get('photos', [])
                cache.set(cache_key, photos[:max_photos], 60 * 60 * 24)
                return photos[:max_photos]
             except Exception as e:
                logger.error(f"Error fetching photos for place {place_id}: {str(e)}")
                return []                   
        

        def fetch_all_nearby_restaurants(location, radius=200):
            restaurants = []
            next_token = None
            attempt = 0
            max_attempts = 3
            
            
            if isinstance(location, tuple):
                location = {'lat': location[0], 'lng': location[1]}
            cache_key = f"nearby_restaurants_{location['lat']}_{location['lng']}_{radius}"
            cached_results = cache.get(cache_key)
            if cached_results:
                logger.info(f"Using cached nearby restaurants for location {location}")
                return cached_results

            while attempt < max_attempts:
                try:
                    attempt += 1
                    results = gmaps.places_nearby(
                        location=location,
                        radius=radius,
                        type='restaurant',
                        page_token=next_token if next_token else None
                    )
                    logger.info(f"API call at {location}, attempt {attempt}: Found {len(results.get('results', []))} restaurants")
                    for place in results.get('results', []):
                        if place.get('place_id') not in seen_place_ids:
                            seen_place_ids.add(place['place_id'])
                            restaurants.append(place)
                    next_token = results.get('next_page_token')
                    if not next_token:
                        break
                    time.sleep(2)
                except Exception as e:
                    logger.error(f"Error fetching nearby restaurants at {location}, attempt {attempt}: {str(e)}")
                    if "OVER_QUERY_LIMIT" in str(e):
                        wait_time = 5 * (2 ** attempt)
                        logger.info(f"Rate limit hit, retrying after {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    break

            cache.set(cache_key, restaurants, 60 * 5)
            return restaurants

        logger.info("Starting to fetch nearby restaurants")
        for i, segment in enumerate(road_segments):
            if len(restaurant_list) >= 100:  # Early exit if we have enough restaurants
                break
            logger.info(f"Searching location {i+1}/{len(road_segments)} at {segment['coords']}...")
            nearby_restaurants = fetch_all_nearby_restaurants(segment['coords'], radius=200)
            logger.info(f"Found {len(nearby_restaurants)} restaurants at segment {i+1}")
            for place in nearby_restaurants[:5]:
                if len(restaurant_list) >= 100:  # Early exit
                    break
                photos = fetch_restaurant_photos(place['place_id'], max_photos=2)
                photo_urls = []
                
                for photo in photos:
                  try:
                    photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo['photo_reference']}&key=AIzaSyDXRT50QvC6eu54VSj2mcaVF4VFUeoQx5Y"
                    photo_urls.append(photo_url)
                  except Exception as e:
                    logger.error(f"Error generating photo URL: {str(e)}")
    
                road_name = segment['road_name'] if segment['road_name'] else "Main Road"
                distance_to_road = calculate_distance_to_road(place['geometry']['location'], best_coordinates)
                nearest_point = find_nearest_road_point(place['geometry']['location'], best_coordinates)
                travel_time = calculate_travel_time_to_restaurant(gmaps, nearest_point, place['geometry']['location'])
                internal_traffic_value, internal_traffic_status, _ = get_restaurant_internal_traffic(gmaps, place['place_id'], place['name'])
                total_traffic_seconds, total_traffic_status, _ = calculate_total_traffic_score(travel_time['value'], internal_traffic_value)
                total_traffic_minutes = round(total_traffic_seconds / 60, 1)
                restaurant_list.append({
                    'name': place['name'],
                    'address': place.get('vicinity', 'Address not available'),
                    'rating': place.get('rating', 'Not rated'),
                    'distance_to_road': distance_to_road,
                    'travel_time': travel_time['text'],
                    'total_traffic_status': total_traffic_status,
                    'place_id': place['place_id'],
                    'total_traffic_minutes': total_traffic_minutes,
                    'internal_traffic_status': internal_traffic_status,
                    'internal_traffic_value': internal_traffic_value,
                    'road': road_name,
                    'photos': photo_urls,  # Add the photo URLs to the restaurant data
                    'main_photo': photo_urls[0] if photo_urls else None
                })
            time.sleep(0.2)

        road_names = set(segment['road_name'] for segment in road_segments if segment['road_name'])
        logger.info(f"Searching additional restaurants on {len(road_names)} named roads...")
        for road_name in road_names:
            if len(restaurant_list) >= 100:  # Early exit if we have enough restaurants
                break
            try:
                next_token = None
                attempt = 0
                max_attempts = 3
                cache_key = f"places_restaurants_{road_name}_{source}_{destination}"
                cached_results = cache.get(cache_key)
                if cached_results:
                    logger.info(f"Using cached places results for road {road_name}")
                    for place in cached_results:
                        if place.get('place_id') not in seen_place_ids:
                            seen_place_ids.add(place['place_id'])
                            distance_to_road = calculate_distance_to_road(place['geometry']['location'], best_coordinates)
                            nearest_point = find_nearest_road_point(place['geometry']['location'], best_coordinates)
                            travel_time = calculate_travel_time_to_restaurant(gmaps, nearest_point, place['geometry']['location'])
                            internal_traffic_value, internal_traffic_status, _ = get_restaurant_internal_traffic(gmaps, place['place_id'], place['name'])
                            total_traffic_seconds, total_traffic_status, _ = calculate_total_traffic_score(travel_time['value'], internal_traffic_value)
                            total_traffic_minutes = round(total_traffic_seconds / 60, 1)
                            restaurant_list.append({
                                'name': place['name'],
                                'address': place.get('vicinity', place.get('formatted_address', 'Address not available')),
                                'rating': place.get('rating', 'Not rated'),
                                'distance_to_road': distance_to_road,
                                'travel_time': travel_time['text'],
                                'total_traffic_status': total_traffic_status,
                                'place_id': place['place_id'],
                                'total_traffic_minutes': total_traffic_minutes,
                                'internal_traffic_status': internal_traffic_status,
                                'internal_traffic_value': internal_traffic_value,
                                'road': road_name
                            })
                    continue

                restaurants_on_road = []
                while attempt < max_attempts:
                    try:
                        results = gmaps.places(
                            query=f"restaurants on {road_name} between {source} and {destination}",
                            location=source_location,
                            radius=5000,
                            page_token=next_token if next_token else None
                        )
                        for place in results.get('results', []):
                            if place.get('place_id') not in seen_place_ids:
                                restaurants_on_road.append(place)
                        next_token = results.get('next_page_token')
                        if not next_token:
                            break
                        attempt += 1
                        time.sleep(2)
                    except Exception as e:
                        logger.error(f"Error searching for restaurants on {road_name}, attempt {attempt}: {str(e)}")
                        if "OVER_QUERY_LIMIT" in str(e):
                            wait_time = 5 * (2 ** attempt)
                            logger.info(f"Rate limit hit, retrying after {wait_time} seconds...")
                            time.sleep(wait_time)
                            continue
                        break

                cache.set(cache_key, restaurants_on_road, 60 * 5)

                for place in restaurants_on_road[:5]:
                    if len(restaurant_list) >= 100:  # Early exit
                        break
                    seen_place_ids.add(place['place_id'])
                    distance_to_road = calculate_distance_to_road(place['geometry']['location'], best_coordinates)
                    nearest_point = find_nearest_road_point(place['geometry']['location'], best_coordinates)
                    travel_time = calculate_travel_time_to_restaurant(gmaps, nearest_point, place['geometry']['location'])
                    internal_traffic_value, internal_traffic_status, _ = get_restaurant_internal_traffic(gmaps, place['place_id'], place['name'])
                    total_traffic_seconds, total_traffic_status, _ = calculate_total_traffic_score(travel_time['value'], internal_traffic_value)
                    total_traffic_minutes = round(total_traffic_seconds / 60, 1)
                    restaurant_list.append({
                        'name': place['name'],
                        'address': place.get('vicinity', place.get('formatted_address', 'Address not available')),
                        'rating': place.get('rating', 'Not rated'),
                        'distance_to_road': distance_to_road,
                        'travel_time': travel_time['text'],
                        'total_traffic_status': total_traffic_status,
                        'place_id': place['place_id'],
                        'total_traffic_minutes': total_traffic_minutes,
                        'internal_traffic_status': internal_traffic_status,
                        'internal_traffic_value': internal_traffic_value,
                        'road': road_name
                    })
            except Exception as e:
                logger.error(f"Error searching for restaurants on {road_name}: {str(e)}")
                continue

        logger.info(f"Total restaurants before sorting: {len(restaurant_list)}")

        if food_preference:
            def check_food_match(restaurant):
                try:
                    place_details = gmaps.place(place_id=restaurant['place_id'], fields=['name', 'types'])
                    types = place_details['result'].get('types', [])
                    name = place_details['result'].get('name', '').lower()
                    return food_preference in name or any(food_preference in t.lower() for t in types)
                except Exception as e:
                    logger.error(f"Error checking food preference for {restaurant['name']}: {str(e)}")
                    return False
            restaurant_list = [r for r in restaurant_list if check_food_match(r)]

        logger.info(f"Total restaurants after filtering: {len(restaurant_list)}")

        user = User.find_by_identifier(request.user_identifier)
        if user:
            logger.info("Updating user history in MongoDB")
            user.collection.update_one(
                {"identifier": request.user_identifier},
                {"$push": {
                    "history": {
                        "source": source,
                        "destination": destination,
                        "timestamp": datetime.now().isoformat(),
                        "restaurants": [r['name'] for r in restaurant_list[:5]],
                        "full_restaurants": restaurant_list
                    }
                }}
            )

        logger.info(f"Returning {len(restaurant_list)} restaurants to the frontend")
        return JsonResponse({
            "restaurants": restaurant_list[:100],
            "message": "Restaurants found successfully",
            "total_found": len(restaurant_list)
        }, status=200)
    except Exception as e:
        logger.error(f"Restaurant search error: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)
    
    
    
@require_auth
@csrf_exempt
def apply_filters(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    try:
        mongo_error = check_mongo_availability()
        if mongo_error:
            return mongo_error
        data = json.loads(request.body)
        sort_option = data.get("sortOption", "rating")
        min_rating = float(data.get("minRating", 0))
        max_traffic_time = int(data.get("maxTrafficTime", 60))
        vegetarian_only = bool(data.get("vegetarianOnly", False))
        open_now = bool(data.get("openNow", True))
        food_categories = [fc.lower() for fc in data.get("foodCategories", [])]
        cuisine_types = [ct.lower() for ct in data.get("cuisineTypes", [])]

        user = User.find_by_identifier(request.user_identifier)
        if not user:
            return JsonResponse({"error": "User not found"}, status=404)
        if not user.history:
            return JsonResponse({"error": "No restaurant search history found"}, status=400)
        last_search = next((search for search in reversed(user.history) if 'full_restaurants' in search), None)
        if not last_search:
            return JsonResponse({"error": "No restaurant data available for filtering"}, status=400)
        
        restaurant_list = last_search['full_restaurants']
        filtered_restaurants = []

        def check_food_match(restaurant):
            try:
                # Cache key for place details
                cache_key = f"place_details_{restaurant['place_id']}"
                cached_details = cache.get(cache_key)
                if cached_details:
                    place_details = cached_details
                else:
                    # Fetch detailed data including name, types, and reviews
                    place_details = gmaps.place(
                        place_id=restaurant['place_id'],
                        fields=['name', 'types', 'formatted_address', 'rating', 'reviews']
                    ).get('result', {})
                    cache.set(cache_key, place_details, 60 * 60)  # Cache for 1 hour

                name = place_details.get('name', '').lower()
                types = [t.lower() for t in place_details.get('types', [])]
                reviews = place_details.get('reviews', [])
                review_text = ' '.join([review.get('text', '').lower() for review in reviews]) if reviews else ''

                # Check food categories (e.g., "pizza", "burgers")
                food_match = True
                if food_categories:
                    food_match = any(
                        fc in name or fc in review_text or any(fc in t for t in types)
                        for fc in food_categories
                    )

                # Check cuisine types (e.g., "indian", "italian")
                cuisine_match = True
                if cuisine_types:
                    cuisine_match = any(
                        ct in name or ct in review_text or any(ct in t for t in types)
                        for ct in cuisine_types
                    )

                return food_match and cuisine_match
            except Exception as e:
                logger.error(f"Error checking food match for {restaurant.get('name', 'unknown')}: {str(e)}")
                return False  # Default to excluding if API fails

        for restaurant in restaurant_list:
            # Apply existing filters
            if min_rating > 0:
                if restaurant.get('rating', 0) == 'Not rated' or float(restaurant.get('rating', 0)) < min_rating:
                    continue
            if restaurant.get('total_traffic_minutes', 0) > max_traffic_time:
                continue
            if vegetarian_only and "vegetarian" not in restaurant.get('name', '').lower():
                continue
            if open_now and restaurant.get('internal_traffic_status') == "CLOSED":
                continue

            # Apply food category and cuisine type filters
            if (food_categories or cuisine_types) and not check_food_match(restaurant):
                continue

            filtered_restaurants.append(restaurant)

        # Sorting logic
        def sort_by_traffic_then_rating(restaurants):
            def get_sort_key(r):
                rating = float(r['rating']) if r['rating'] != 'Not rated' else 0
                return (r.get('total_traffic_minutes', 0), -rating)
            return sorted(restaurants, key=get_sort_key)

        def sort_by_rating_then_traffic(restaurants):
            def get_sort_key(r):
                rating = float(r['rating']) if r['rating'] != 'Not rated' else 0
                return (-rating, r.get('total_traffic_minutes', 0))
            return sorted(restaurants, key=get_sort_key)

        if sort_option == "traffic":
            filtered_restaurants = sort_by_traffic_then_rating(filtered_restaurants)
        elif sort_option == "rating":
            filtered_restaurants = sort_by_rating_then_traffic(filtered_restaurants)

        return JsonResponse({
            "message": "Filters applied successfully",
            "filtered_restaurants": filtered_restaurants[:60],
            "filters_applied": {
                "sortOption": sort_option,
                "minRating": min_rating,
                "maxTrafficTime": max_traffic_time,
                "vegetarianOnly": vegetarian_only,
                "openNow": open_now,
                "foodCategories": food_categories,
                "cuisineTypes": cuisine_types,
            },
            "total_filtered": len(filtered_restaurants)
        }, status=200)
    except Exception as e:
        logger.error(f"Filter application error: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def index_view(request):
    return render(request, 'home.html')

@csrf_exempt
def root(request):
    return render(request, 'home.html', {})




