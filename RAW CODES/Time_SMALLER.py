import googlemaps
from datetime import datetime
import folium
from googlemaps.convert import decode_polyline
import time
import re
from geopy.distance import geodesic
import pandas as pd

# Initialize Google Maps client with your API key
gmaps = googlemaps.Client(key='AIzaSyBRBeH0AcfEEg-hzaaORkDAcuaFfObTzMA')  # Replace with your actual API key

# Get user input for source and destination
source = input("Enter the source address: ")
destination = input("Enter the destination address: ")

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

# Define traffic-based colors
def get_traffic_color(traffic_value):
    if traffic_value < 10:
        return "green"
    elif traffic_value < 20:
        return "yellow"
    return "red"

best_route_index = 0
min_duration = float('inf')

# Iterate through route options
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

# Highlight best route
best_route = directions_result[best_route_index]
best_polyline = best_route['overview_polyline']['points']
decoded_best_points = decode_polyline(best_polyline)
best_coordinates = [(point['lat'], point['lng']) for point in decoded_best_points]
folium.PolyLine(best_coordinates, color='purple', weight=6, opacity=1, dash_array='5, 5').add_to(m)

# Add markers for source and destination
folium.Marker([source_location['lat'], source_location['lng']], tooltip='Source', icon=folium.Icon(color='blue')).add_to(m)
folium.Marker([destination_location['lat'], destination_location['lng']], tooltip='Destination', icon=folium.Icon(color='red')).add_to(m)

# --------- RESTAURANT SEARCH FUNCTIONALITY -----------

# Extract detailed steps from the best route
best_route_steps = best_route['legs'][0]['steps']
restaurant_list = []
seen_place_ids = set()

# Function to extract road names from HTML instructions
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

# Calculate total route distance and determine sampling interval
total_distance = sum(step.get('distance', {}).get('value', 0) for step in best_route_steps)
desired_segments = 15  # Target 15 calls (within 10–20 range)
sampling_interval = max(1000, total_distance // desired_segments)  # At least 1 km, adjusted for route length

# Process each step to extract coordinates with dynamic sampling
road_segments = []
for step in best_route_steps:
    road_name = extract_road_names(step['html_instructions']) if 'html_instructions' in step else None
    points = decode_polyline(step['polyline']['points'])
    coords = [(point['lat'], point['lng']) for point in points]
    
    distance = step.get('distance', {}).get('value', 0)
    num_points = max(1, int(distance / sampling_interval))
    step_size = max(1, len(coords) // num_points)
    
    for i in range(0, len(coords), step_size):
        road_segments.append({
            'coords': coords[i],
            'road_name': road_name
        })

# Cap the number of segments to 20 (max target)
road_segments = road_segments[:20]
print(f"Identified {len(road_segments)} search points along the route (capped at 20).")

# Function to calculate distance from a point to the nearest point on the main road
def calculate_distance_to_road(restaurant_coords, road_coords):
    min_distance = float('inf')
    restaurant_point = (restaurant_coords['lat'], restaurant_coords['lng'])
    
    for road_point in road_coords:
        distance = geodesic(restaurant_point, road_point).meters
        if distance < min_distance:
            min_distance = distance
    
    return round(min_distance, 2)

# Improved function to find the nearest point on the main road
def find_nearest_road_point(restaurant_location, road_coordinates):
    min_distance = float('inf')
    nearest_point = None
    restaurant_point = (restaurant_location['lat'], restaurant_location['lng'])
    
    for i in range(len(road_coordinates) - 1):
        start_point = road_coordinates[i]
        end_point = road_coordinates[i + 1]
        # Calculate the closest point on the line segment
        road_segment_distance = geodesic((start_point[0], start_point[1]), (end_point[0], end_point[1])).meters
        if road_segment_distance > 0:
            t = max(0, min(1, ((restaurant_point[0] - start_point[0]) * (end_point[0] - start_point[0]) + 
                             (restaurant_point[1] - start_point[1]) * (end_point[1] - start_point[1])) / 
                             (road_segment_distance ** 2)))
            projected_point = (
                start_point[0] + t * (end_point[0] - start_point[0]),
                start_point[1] + t * (end_point[1] - start_point[1])
            )
            distance = geodesic(restaurant_point, projected_point).meters
            if distance < min_distance:
                min_distance = distance
                nearest_point = projected_point
    
    return nearest_point if nearest_point else road_coordinates[0]  # Fallback to first point if none found

# Function to calculate travel time
def calculate_travel_time_to_restaurant(gmaps_client, origin, destination):
    try:
        directions = gmaps_client.directions(
            origin=origin,
            destination=destination,
            mode="driving",
            departure_time=datetime.now(),
            traffic_model='best_guess'
        )
        
        if directions and 'legs' in directions[0]:
            duration_text = directions[0]['legs'][0]['duration_in_traffic']['text']
            duration_seconds = directions[0]['legs'][0]['duration_in_traffic']['value']
            # Validate duration is reasonable (e.g., not zero or negative)
            if duration_seconds <= 0:
                return "Unknown", 60  # Minimum 1 minute if invalid
            return duration_text, duration_seconds
        return "Unknown", 60  # Default to 1 minute if no data
    except Exception as e:
        print(f"Error calculating travel time: {str(e)}")
        return "Error", 60  # Default to 1 minute on error

# Function to fetch only the first page of nearby restaurants
def fetch_nearby_restaurants(location, radius=1000):
    try:
        results = gmaps.places_nearby(
            location=location,
            radius=radius,
            type='restaurant'
        )
        restaurants = []
        for place in results.get('results', []):
            if place.get('place_id') not in seen_place_ids:
                seen_place_ids.add(place['place_id'])
                restaurants.append(place)
        return restaurants
    except Exception as e:
        print(f"Error fetching nearby restaurants: {str(e)}")
        return []

# Search for restaurants at each segment point
for i, segment in enumerate(road_segments):
    print(f"Searching location {i+1}/{len(road_segments)}...")
    
    nearby_restaurants = fetch_nearby_restaurants(segment['coords'], radius=1000)
    
    for place in nearby_restaurants:
        road_name = segment['road_name'] if segment['road_name'] else "Unnamed Road"
        distance_to_road = calculate_distance_to_road(place['geometry']['location'], best_coordinates)
        
        # Find the nearest point on the main road with improved accuracy
        nearest_point = find_nearest_road_point(place['geometry']['location'], best_coordinates)
        if nearest_point:
            nearest_point = {'lat': nearest_point[0], 'lng': nearest_point[1]}
        else:
            nearest_point = segment['coords']  # Fallback to segment point
        
        # Travel time from main road to restaurant (detour time)
        travel_time_from_road_text, travel_time_from_road_seconds = calculate_travel_time_to_restaurant(
            gmaps, 
            nearest_point, 
            place['geometry']['location']
        )
        
        # Travel time from source to nearest point on main road
        travel_time_to_nearest_text, travel_time_to_nearest_seconds = calculate_travel_time_to_restaurant(
            gmaps, 
            source_location, 
            nearest_point
        )
        
        # Total travel time from source = time to nearest point + time from nearest point to restaurant
        if travel_time_to_nearest_seconds > 0 and travel_time_from_road_seconds > 0:
            travel_time_from_source_seconds = travel_time_to_nearest_seconds + travel_time_from_road_seconds
            # Convert total seconds to human-readable format with higher precision
            minutes = travel_time_from_source_seconds // 60
            remaining_seconds = travel_time_from_source_seconds % 60
            travel_time_from_source_text = f"{minutes} mins {remaining_seconds} secs" if remaining_seconds > 0 else f"{minutes} mins"
        else:
            travel_time_from_source_text, travel_time_from_source_seconds = travel_time_from_road_text, travel_time_from_road_seconds
        
        # Validate and adjust travel time from main road for accuracy
        if travel_time_from_road_seconds < 30:  # If less than 30 seconds, re-calculate
            print(f"Warning: Travel time from main road too short ({travel_time_from_road_seconds}s) for {place['name']}. Recalculating...")
            travel_time_from_road_text, travel_time_from_road_seconds = calculate_travel_time_to_restaurant(
                gmaps, 
                nearest_point, 
                place['geometry']['location']
            )
        
        restaurant_list.append({
            'name': place['name'],
            'address': place.get('vicinity', place.get('formatted_address', 'Address not available')),
            'rating': place.get('rating', 'Not rated'),
            'road': road_name,
            'location': place['geometry']['location'],
            'place_id': place['place_id'],
            'distance_to_road': distance_to_road,
            'travel_time_from_road': travel_time_from_road_text,
            'travel_time_from_source': travel_time_from_source_text
        })
        
        folium.Marker(
            location=[place['geometry']['location']['lat'], place['geometry']['location']['lng']],
            popup=f"""<b>{place['name']}</b><br>
                   Rating: {place.get('rating', 'Not rated')}<br>
                   Address: {place.get('vicinity', place.get('formatted_address', 'Address not available'))}<br>
                   Road: {road_name}<br>
                   Distance from Main Road: {distance_to_road} meters<br>
                   Travel Time from Main Road: {travel_time_from_road_text}<br>
                   Travel Time from Source: {travel_time_from_source_text}""",
            tooltip=place['name'],
            icon=folium.Icon(color='darkpurple', icon='cutlery', prefix='fa')
        ).add_to(m)
    
    time.sleep(0.2)

# Save map to file
map_filename = "traffic_map.html"
m.save(map_filename)

# Print grouped restaurant list with all fields
print("\nRestaurants along the preferred route (grouped by road):")
print("=======================================================")

restaurants_by_road = {}
for restaurant in restaurant_list:
    road = restaurant['road']
    if road not in restaurants_by_road:
        restaurants_by_road[road] = []
    restaurants_by_road[road].append(restaurant)

for road, restaurants in restaurants_by_road.items():
    print(f"\n{road}:")
    print("-" * len(road) + "--")
    for i, restaurant in enumerate(restaurants, 1):
        print(f"  {i}. {restaurant['name']}")
        print(f"     Rating: {restaurant['rating']}")
        print(f"     Address: {restaurant['address']}")
        print(f"     Distance from Main Road: {restaurant['distance_to_road']} meters")
        print(f"     Travel Time from Main Road: {restaurant['travel_time_from_road']}")
        print(f"     Travel Time from Source: {restaurant['travel_time_from_source']}")

# Export to Excel with all fields
excel_data = []
for restaurant in restaurant_list:
    excel_data.append({
        'Name': restaurant['name'],
        'Road': restaurant['road'],
        'Address': restaurant['address'],
        'Rating': restaurant['rating'],
        'Distance from Main Road (meters)': restaurant['distance_to_road'],
        'Travel Time from Main Road': restaurant['travel_time_from_road'],
        'Travel Time from Source': restaurant['travel_time_from_source'],
        'Latitude': restaurant['location']['lat'],
        'Longitude': restaurant['location']['lng']
    })

df = pd.DataFrame(excel_data)
excel_filename = "restaurants_with_travel_time.xlsx"
df.to_excel(excel_filename, index=False)

print(f"\nTotal restaurants found: {len(restaurant_list)}")
print(f"Map saved as {map_filename}. Open this file in a browser to view the routes and restaurants.")
print(f"Restaurant data saved to {excel_filename}")
print(f"Total Places API calls made: {len(road_segments)}")