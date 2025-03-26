import googlemaps
from datetime import datetime

# Replace with your actual API key
API_KEY = "AIzaSyBRBeH0AcfEEg-hzaaORkDAcuaFfObTzMA"

# Initialize the Google Maps client
gmaps = googlemaps.Client(key=API_KEY)

country = input("Enter the country name: ")

city = input("Enter the city name: ")

# Input Source and Destination Addresses
source_local = input("Enter the source address (within the city): ")
destination_local = input("Enter the destination address: ")

source = f"{source_local}, {city}, {country}"
destination = f"{destination_local}, {city}, {country}"

# directions considering real-time traffic
now = datetime.now()
try:
    directions_result = gmaps.directions(
        source,
        destination,
        mode="driving",
        departure_time=now,  # Real-time traffic data
        traffic_model="best_guess"
    )

    if not directions_result:
        print("No routes found. Please check the addresses and try again.")
    else:
        # Extract the fastest route based on duration in traffic
        best_route = directions_result[0]  # First route is usually the best one
        route_summary = best_route['legs'][0]

        print("\nRecommended Route based on Real-Time Traffic:\n")
        print(f"Source: {route_summary['start_address']}")
        print(f"Destination: {route_summary['end_address']}")
        print(f"Estimated Duration (with traffic): {route_summary['duration_in_traffic']['text']}")
        print(f"Distance: {route_summary['distance']['text']}")
        print("\nDirections:\n")
        
        for step in route_summary['steps']:
            instruction = step['html_instructions']
            # Clean HTML tags from instructions
            clean_instruction = instruction.replace('<b>', '').replace('</b>', '').replace('<div style="font-size:0.9em">', ' ').replace('</div>', '')
            print(f"- {clean_instruction} ({step['distance']['text']})")
            
except Exception as e:
    print("An error occurred:", e)
