import googlemaps
from datetime import datetime
import folium
from googlemaps.convert import decode_polyline
import time
import re
from geopy.distance import geodesic  # For accurate distance calculation

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
best_coordinates = [(point['lat'], point['lng']) for point in decoded_best_points]  # Main road coordinates
folium.PolyLine(best_coordinates, color='purple', weight=6, opacity=1, dash_array='5, 5').add_to(m)

# Add markers for source and destination
folium.Marker([source_location['lat'], source_location['lng']], tooltip='Source', icon=folium.Icon(color='blue')).add_to(m)
folium.Marker([destination_location['lat'], destination_location['lng']], tooltip='Destination', icon=folium.Icon(color='red')).add_to(m)

# --------- IMPROVED RESTAURANT SEARCH FUNCTIONALITY -----------

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

# Process each step to extract coordinates
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

# Function to calculate distance from a point to the nearest point on the main road
def calculate_distance_to_road(restaurant_coords, road_coords):
    min_distance = float('inf')
    restaurant_point = (restaurant_coords['lat'], restaurant_coords['lng'])
    
    for road_point in road_coords:
        distance = geodesic(restaurant_point, road_point).meters
        if distance < min_distance:
            min_distance = distance
    
    return round(min_distance, 2)  # Return distance in meters, rounded to 2 decimal places

# Function to fetch all pages of nearby restaurants
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

# Search for restaurants at each segment point
for i, segment in enumerate(road_segments):
    print(f"Searching location {i+1}/{len(road_segments)}...")
    
    nearby_restaurants = fetch_all_nearby_restaurants(segment['coords'], radius=250)
    
    for place in nearby_restaurants:
        road_name = segment['road_name'] if segment['road_name'] else "Unnamed Road"
        distance_to_road = calculate_distance_to_road(place['geometry']['location'], best_coordinates)
        
        restaurant_list.append({
            'name': place['name'],
            'address': place.get('vicinity', 'Address not available'),
            'rating': place.get('rating', 'Not rated'),
            'road': road_name,
            'location': place['geometry']['location'],
            'place_id': place['place_id'],
            'distance_to_road': distance_to_road
        })
        
        folium.Marker(
            location=[place['geometry']['location']['lat'], place['geometry']['location']['lng']],
            popup=f"""<b>{place['name']}</b><br>
                   Rating: {place.get('rating', 'Not rated')}<br>
                   Road: {road_name}<br>
                   Distance from Main Road: {distance_to_road} meters<br>
                   {place.get('vicinity', 'Address not available')}""",
            tooltip=place['name'],
            icon=folium.Icon(color='darkpurple', icon='cutlery', prefix='fa')
        ).add_to(m)
    
    time.sleep(0.2)

# Additional text-based search for named roads
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
                    
                    restaurant_list.append({
                        'name': place['name'],
                        'address': place.get('vicinity', place.get('formatted_address', 'Address not available')),
                        'rating': place.get('rating', 'Not rated'),
                        'road': road_name,
                        'location': place['geometry']['location'],
                        'place_id': place['place_id'],
                        'distance_to_road': distance_to_road
                    })
                    
                    folium.Marker(
                        location=[place['geometry']['location']['lat'], place['geometry']['location']['lng']],
                        popup=f"""<b>{place['name']}</b><br>
                               Rating: {place.get('rating', 'Not rated')}<br>
                               Road: {road_name}<br>
                               Distance from Main Road: {distance_to_road} meters<br>
                               {place.get('vicinity', place.get('formatted_address', 'Address not available'))}""",
                        tooltip=place['name'],
                        icon=folium.Icon(color='darkpurple', icon='cutlery', prefix='fa')
                    ).add_to(m)
            
            next_token = results.get('next_page_token')
            if not next_token:
                break
            
            time.sleep(2)
            
    except Exception as e:
        print(f"Error searching for restaurants on {road_name}: {str(e)}")
        continue

# Save map to file
map_filename = "traffic_map.html"
m.save(map_filename)

# Print grouped restaurant list
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

print(f"\nTotal restaurants found: {len(restaurant_list)}")
print(f"Map saved as {map_filename}. Open this file in a browser to view the routes and restaurants.")