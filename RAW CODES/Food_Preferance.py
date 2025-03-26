import googlemaps
from datetime import datetime
import folium
from googlemaps.convert import decode_polyline
import time
import re
from geopy.distance import geodesic
import pandas as pd
import random

# Initialize Google Maps client with your API key
gmaps = googlemaps.Client(key='AIzaSyBRBeH0AcfEEg-hzaaORkDAcuaFfObTzMA')  # Replace with your actual API key

# Get user input for source and destination
source = input("Enter the source address: ")
destination = input("Enter the destination address: ")

# Get user input for sorting preference
print("\nChoose sorting option:")
print("1: Sort by Total Traffic, then by Customer Rating")
print("2: Sort by Customer Rating, then by Total Traffic")
print("3: No sorting (random order)")
sort_choice = input("Enter 1, 2, or 3: ")

if sort_choice not in ['1', '2', '3']:
    print("Invalid choice. Defaulting to no sorting (option 3).")
    sort_choice = '3'

# Get user input for food preference
food_preference = input("\nEnter your preferred food type (e.g., biriyani, pizza, sushi) or press Enter for no preference: ").strip().lower()

# Geocode the source and destination addresses
source_result = gmaps.geocode(source)
if not source_result:
    print(f"Error: Could not find location for '{source}'. Try a more specific address.")
    exit()
source_location = source_result[0]['geometry']['location']

destination_result = gmaps.geocode(destination)
if not destination_result:
    print(f"Error: Could not find location for '{destination}'. Try a more specific address.")
    exit()
destination_location = destination_result[0]['geometry']['location']

# Get real-time traffic-based directions
directions_result = gmaps.directions(
    origin=source,
    destination=destination,
    mode="driving",
    departure_time=datetime.now(),
    traffic_model='best_guess',
    alternatives=True
)

# Initialize map at source location
m = folium.Map(location=[source_location['lat'], source_location['lng']], zoom_start=12)

def get_traffic_color(traffic_value):
    if traffic_value < 10:
        return "green"
    elif traffic_value < 20:
        return "yellow"
    return "red"

best_route_index = 0
min_duration = float('inf')

for i, route in enumerate(directions_result):
    leg = route['legs'][0]
    duration = leg['duration_in_traffic']['value']
    route_color = get_traffic_color(duration // 60)
    
    if duration < min_duration:
        min_duration = duration
        best_route_index = i
    
    polyline = route['overview_polyline']['points']
    decoded_points = decode_polyline(polyline)
    coordinates = [(point['lat'], point['lng']) for point in decoded_points]
    
    folium.PolyLine(coordinates, color=route_color, weight=5, opacity=0.7).add_to(m)
    midpoint = coordinates[len(coordinates) // 2]
    folium.Marker(midpoint, icon=folium.DivIcon(html=f'<div style="font-size: 12px; color: black; background: white; padding: 3px;">{leg["duration_in_traffic"]["text"]}</div>')).add_to(m)

best_route = directions_result[best_route_index]
best_polyline = best_route['overview_polyline']['points']
decoded_best_points = decode_polyline(best_polyline)
best_coordinates = [(point['lat'], point['lng']) for point in decoded_best_points]
folium.PolyLine(best_coordinates, color='purple', weight=6, opacity=1, dash_array='5, 5').add_to(m)

folium.Marker([source_location['lat'], source_location['lng']], tooltip='Source', icon=folium.Icon(color='blue')).add_to(m)
folium.Marker([destination_location['lat'], destination_location['lng']], tooltip='Destination', icon=folium.Icon(color='red')).add_to(m)

# Restaurant Search Functionality
best_route_steps = best_route['legs'][0]['steps']
restaurant_list = []
seen_place_ids = set()

def extract_road_names(instruction):
    clean_text = re.sub('<[^<]+?>', ' ', instruction).strip()
    patterns = [
        r"onto ([^<]+?)(?: toward| for| \.)",
        r"on ([^<]+?)(?: toward| for| \.)",
        r"Continue on ([^<]+?)(?: toward| for| \.)",
        r"Take ([^<]+?)(?: toward| for| \.)"
    ]
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
    num_points = max(1, int(distance / 200))
    step_size = max(1, len(coords) // num_points)
    
    for i in range(0, len(coords), step_size):
        road_segments.append({
            'coords': coords[i],
            'road_name': road_name
        })

print(f"Identified {len(road_segments)} search points along the route.")

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
            duration = directions[0]['legs'][0]['duration_in_traffic']['text']
            duration_value = directions[0]['legs'][0]['duration_in_traffic']['value']
            return duration, duration_value
        return "Unknown", 0
    except Exception as e:
        print(f"Error calculating travel time: {str(e)}")
        return "Error", 0

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
        place_details = gmaps_client.place(
            place_id=restaurant_id,
            fields=['name', 'place_id', 'current_opening_hours']
        )
        now = datetime.now()
        hour = now.hour
        day = now.weekday()
        
        is_open = False
        if 'current_opening_hours' in place_details['result']:
            is_open = place_details['result']['current_opening_hours'].get('open_now', False)
        
        if not is_open:
            return 0, "CLOSED", "gray"
        
        peak_hours = {
            0: [(11, 14), (17, 20)],
            1: [(11, 14), (17, 20)],
            2: [(11, 14), (17, 20)],
            3: [(11, 14), (17, 21)],
            4: [(11, 15), (17, 22)],
            5: [(10, 15), (17, 22)],
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
        
        print(f"Simulated internal traffic for {restaurant_name}: {status} ({traffic_value}%)")
        return traffic_value, status, color
    except Exception as e:
        print(f"Error getting internal traffic for {restaurant_name}: {str(e)}")
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

def sort_by_traffic_then_rating(restaurants):
    def get_sort_key(restaurant):
        rating = float(restaurant['rating']) if restaurant['rating'] != 'Not rated' else 0
        return (restaurant['total_traffic_seconds'], -rating)
    return sorted(restaurants, key=get_sort_key)

def sort_by_rating_then_traffic(restaurants):
    def get_sort_key(restaurant):
        rating = float(restaurant['rating']) if restaurant['rating'] != 'Not rated' else 0
        return (-rating, restaurant['total_traffic_seconds'])
    return sorted(restaurants, key=get_sort_key)

# New Function: Filter and sort by food preference
def sort_by_food_preference(restaurants, preference):
    if not preference:
        return restaurants  # Return as is if no preference
    
    def check_food_match(restaurant):
        try:
            # Fetch place details including types or name that might indicate cuisine
            place_details = gmaps.place(
                place_id=restaurant['place_id'],
                fields=['name', 'types']
            )
            types = place_details['result'].get('types', [])
            name = place_details['result'].get('name', '').lower()
            
            # Basic check: does the name or type suggest the preferred food?
            food_related = preference in name or any(preference in t.lower() for t in types)
            return 1 if food_related else 0  # 1 for match, 0 for no match
        except Exception as e:
            print(f"Error checking food preference for {restaurant['name']}: {str(e)}")
            return 0  # Assume no match if error occurs
    
    # Add food match score to each restaurant
    for restaurant in restaurants:
        restaurant['food_match'] = check_food_match(restaurant)
    
    # Sort by food match (descending), keeping previous sorting intact within each group
    return sorted(restaurants, key=lambda x: x['food_match'], reverse=True)

def fetch_all_nearby_restaurants(location, radius=250):
    restaurants = []
    next_token = None
    while True:
        try:
            results = gmaps.places_nearby(
                location=location,
                radius=radius,
                type='restaurant',
                page_token=next_token if next_token else None
            )
            for place in results.get('results', []):
                if place.get('place_id') not in seen_place_ids:
                    seen_place_ids.add(place['place_id'])
                    restaurants.append(place)
            next_token = results.get('next_page_token')
            if not next_token:
                break
            time.sleep(2)
        except Exception as e:
            print(f"Error fetching nearby restaurants: {str(e)}")
            break
    return restaurants

for i, segment in enumerate(road_segments):
    print(f"Searching location {i+1}/{len(road_segments)}...")
    nearby_restaurants = fetch_all_nearby_restaurants(segment['coords'], radius=250)
    
    for place in nearby_restaurants:
        road_name = segment['road_name'] if segment['road_name'] else "Unnamed Road"
        distance_to_road = calculate_distance_to_road(place['geometry']['location'], best_coordinates)
        
        nearest_point = find_nearest_road_point(place['geometry']['location'], best_coordinates)
        travel_time_text, travel_time_seconds = calculate_travel_time_to_restaurant(
            gmaps, nearest_point, place['geometry']['location']
        )
        
        internal_traffic_value, internal_traffic_status, internal_traffic_color = get_restaurant_internal_traffic(
            gmaps, place['place_id'], place['name']
        )
        
        total_traffic_seconds, total_traffic_status, total_traffic_color = calculate_total_traffic_score(
            travel_time_seconds, internal_traffic_value
        )
        
        total_traffic_minutes = round(total_traffic_seconds / 60, 1)
        
        restaurant_list.append({
            'name': place['name'],
            'address': place.get('vicinity', 'Address not available'),
            'rating': place.get('rating', 'Not rated'),
            'road': road_name,
            'location': place['geometry']['location'],
            'place_id': place['place_id'],
            'distance_to_road': distance_to_road,
            'travel_time': travel_time_text,
            'travel_time_seconds': travel_time_seconds,
            'internal_traffic_value': internal_traffic_value,
            'internal_traffic_status': internal_traffic_status,
            'total_traffic_seconds': total_traffic_seconds,
            'total_traffic_minutes': total_traffic_minutes,
            'total_traffic_status': total_traffic_status
        })
        
        folium.Marker(
            location=[place['geometry']['location']['lat'], place['geometry']['location']['lng']],
            popup=f"""<b>{place['name']}</b><br>
                   Rating: {place.get('rating', 'Not rated')}<br>
                   Road: {road_name}<br>
                   Distance from Main Road: {distance_to_road} meters<br>
                   Travel Time: {travel_time_text}<br>
                   Internal Traffic: {internal_traffic_status} ({internal_traffic_value}%)<br>
                   Total Traffic: {total_traffic_status} ({total_traffic_minutes} mins)<br>
                   {place.get('vicinity', 'Address not available')}""",
            tooltip=place['name'],
            icon=folium.Icon(color=total_traffic_color, icon='cutlery', prefix='fa')
        ).add_to(m)
    
    time.sleep(0.2)

road_names = set(segment['road_name'] for segment in road_segments if segment['road_name'])
print(f"Searching for additional restaurants on {len(road_names)} named roads...")

for road_name in road_names:
    try:
        next_token = None
        while True:
            results = gmaps.places(
                query=f"restaurants on {road_name} between {source} and {destination}",
                location=source_location,
                radius=5000,
                page_token=next_token if next_token else None
            )
            for place in results.get('results', []):
                if place.get('place_id') not in seen_place_ids:
                    seen_place_ids.add(place['place_id'])
                    distance_to_road = calculate_distance_to_road(place['geometry']['location'], best_coordinates)
                    nearest_point = find_nearest_road_point(place['geometry']['location'], best_coordinates)
                    travel_time_text, travel_time_seconds = calculate_travel_time_to_restaurant(
                        gmaps, nearest_point, place['geometry']['location']
                    )
                    internal_traffic_value, internal_traffic_status, internal_traffic_color = get_restaurant_internal_traffic(
                        gmaps, place['place_id'], place['name']
                    )
                    total_traffic_seconds, total_traffic_status, total_traffic_color = calculate_total_traffic_score(
                        travel_time_seconds, internal_traffic_value
                    )
                    total_traffic_minutes = round(total_traffic_seconds / 60, 1)
                    
                    restaurant_list.append({
                        'name': place['name'],
                        'address': place.get('vicinity', place.get('formatted_address', 'Address not available')),
                        'rating': place.get('rating', 'Not rated'),
                        'road': road_name,
                        'location': place['geometry']['location'],
                        'place_id': place['place_id'],
                        'distance_to_road': distance_to_road,
                        'travel_time': travel_time_text,
                        'travel_time_seconds': travel_time_seconds,
                        'internal_traffic_value': internal_traffic_value,
                        'internal_traffic_status': internal_traffic_status,
                        'total_traffic_seconds': total_traffic_seconds,
                        'total_traffic_minutes': total_traffic_minutes,
                        'total_traffic_status': total_traffic_status
                    })
                    
                    folium.Marker(
                        location=[place['geometry']['location']['lat'], place['geometry']['location']['lng']],
                        popup=f"""<b>{place['name']}</b><br>
                               Rating: {place.get('rating', 'Not rated')}<br>
                               Road: {road_name}<br>
                               Distance from Main Road: {distance_to_road} meters<br>
                               Travel Time: {travel_time_text}<br>
                               Internal Traffic: {internal_traffic_status} ({internal_traffic_value}%)<br>
                               Total Traffic: {total_traffic_status} ({total_traffic_minutes} mins)<br>
                               {place.get('vicinity', place.get('formatted_address', 'Address not available'))}""",
                        tooltip=place['name'],
                        icon=folium.Icon(color=total_traffic_color, icon='cutlery', prefix='fa')
                    ).add_to(m)
            
            next_token = results.get('next_page_token')
            if not next_token:
                break
            time.sleep(2)
    except Exception as e:
        print(f"Error searching for restaurants on {road_name}: {str(e)}")
        continue

map_filename = "traffic_map.html"
m.save(map_filename)

# Apply initial two-phase sorting based on user choice
if sort_choice == '1':
    sorted_restaurants = sort_by_traffic_then_rating(restaurant_list)
    sort_method = "Sorted by Total Traffic, then by Customer Rating"
elif sort_choice == '2':
    sorted_restaurants = sort_by_rating_then_traffic(restaurant_list)
    sort_method = "Sorted by Customer Rating, then by Total Traffic"
else:
    sorted_restaurants = restaurant_list
    sort_method = "No sorting (random order)"

# Apply third phase: sort by food preference
sorted_restaurants = sort_by_food_preference(sorted_restaurants, food_preference)
food_filter_text = f" and filtered by '{food_preference}' preference" if food_preference else ""

# Print grouped restaurant list
print(f"\nRestaurants along the preferred route ({sort_method}{food_filter_text}):")
print("=======================================================")

restaurants_by_road = {}
for restaurant in sorted_restaurants:
    road = restaurant['road']
    if road not in restaurants_by_road:
        restaurants_by_road[road] = []
    restaurants_by_road[road].append(restaurant)

for road, restaurants in restaurants_by_road.items():
    print(f"\n{road}:")
    print("-" * len(road) + "--")
    for i, restaurant in enumerate(restaurants, 1):
        food_match_text = " (Matches preference)" if restaurant.get('food_match', 0) == 1 else ""
        print(f"  {i}. {restaurant['name']}{food_match_text}")
        print(f"     Rating: {restaurant['rating']}")
        print(f"     Address: {restaurant['address']}")
        print(f"     Distance from Main Road: {restaurant['distance_to_road']} meters")
        print(f"     Travel Time from Main Road: {restaurant['travel_time']}")
        print(f"     Internal Traffic: {restaurant['internal_traffic_status']} ({restaurant['internal_traffic_value']}%)")
        print(f"     Total Traffic: {restaurant['total_traffic_status']} ({restaurant['total_traffic_minutes']} mins)")

# Export to Excel
excel_data = []
for restaurant in sorted_restaurants:
    excel_data.append({
        'Name': restaurant['name'],
        'Road': restaurant['road'],
        'Address': restaurant['address'],
        'Rating': restaurant['rating'],
        'Distance from Main Road (meters)': restaurant['distance_to_road'],
        'Travel Time from Main Road': restaurant['travel_time'],
        'Travel Time (seconds)': restaurant['travel_time_seconds'],
        'Internal Traffic (%)': restaurant['internal_traffic_value'],
        'Internal Traffic Status': restaurant['internal_traffic_status'],
        'Total Traffic (seconds)': restaurant['total_traffic_seconds'],
        'Total Traffic (minutes)': restaurant['total_traffic_minutes'],
        'Total Traffic Status': restaurant['total_traffic_status'],
        'Matches Food Preference': 'Yes' if restaurant.get('food_match', 0) == 1 else 'No',
        'Latitude': restaurant['location']['lat'],
        'Longitude': restaurant['location']['lng']
    })

df = pd.DataFrame(excel_data)
excel_filename = "sorted_restaurants_with_traffic_ratings_and_food.xlsx"
df.to_excel(excel_filename, index=False)

print(f"\nTotal restaurants found: {len(restaurant_list)}")
print(f"Map saved as {map_filename}. Open this file in a browser to view the routes and restaurants.")
print(f"Restaurant data saved to {excel_filename}")