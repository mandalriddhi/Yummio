
import { Star, MapPin, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface RestaurantCardProps {
  name: string;
  address: string;
  rating: string | number;
  distance_to_road?: number;
  travel_time?: string;
  total_traffic_status?: string;
  total_traffic_minutes?: number;
  internal_traffic_status?: string;
  internal_traffic_value?: number;
  road?: string;
  place_id: string;
  isFiltered?: boolean;
  onDetailsClick?: (place_id: string) => void;
  main_photo?: string;  // Add this
  photos?: string[]; 
}

const RestaurantCard = ({
  name,
  address,
  rating = 'Not rated',
  distance_to_road = 0,
  travel_time = 'N/A',
  total_traffic_status = 'UNKNOWN',
  total_traffic_minutes = 0,
  internal_traffic_status = 'UNKNOWN',
  internal_traffic_value = 0,
  road = 'Main road',
  place_id,
  isFiltered = false,
  onDetailsClick,
  main_photo,  // Add this
  photos = [], // Add this with default empty array
}: RestaurantCardProps) => {
  // Determine traffic color based on status
  const getTrafficColor = (status?: string) => {
    if (!status) return 'text-gray-500';
    switch (status.toUpperCase()) {
      case 'LOW':
        return 'text-green-500';
      case 'MEDIUM':
      case 'MODERATE':
        return 'text-yellow-500';
      case 'HIGH':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  };

  const placeholderImage = 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxzZWFyY2h8Mnx8cmVzdGF1cmFudHxlbnwwfHwwfHw%3D&w=1000&q=80';
  // Format distance for display
  const formatDistance = (meters: number) => {
    if (meters >= 1000) return `${(meters / 1000).toFixed(1)} km`;
    return `${meters} m`;
  };

  // Format rating display
  const formatRating = (rating: string | number) => {
    if (rating === 'Not rated') return rating;
    return typeof rating === 'number' ? rating.toFixed(1) : rating;
  };

  // Get restaurant image with fallback
  const getRestaurantImage = () => {
    const baseUrl = 'https://source.unsplash.com/random/400x300/?';
    const tags = ['food', 'restaurant', 'dining', 'meal', 'cuisine'];
    const randomTag = tags[Math.floor(Math.random() * tags.length)];
    return `${baseUrl}${randomTag},${encodeURIComponent(name)}&${Date.now()}`;
  };

  const handleDetailsClick = () => {
    if (onDetailsClick) {
      onDetailsClick(place_id);
    }
  };

  return (
    <div className={`rounded-lg border bg-card text-card-foreground shadow hover:shadow-lg transition-shadow ${isFiltered ? 'ring-2 ring-primary border-primary' : ''}`}>
      <div className="relative h-48">
        <img
          src={main_photo || placeholderImage}
          alt={name}
          className="w-full h-full object-cover rounded-t-lg"
          loading="lazy"
          onError={(e) => {
            if (photos.length > 0) {
              (e.target as HTMLImageElement).src = photos[0];
            } else {
              // Fall back to placeholder if no photos available
              (e.target as HTMLImageElement).src = placeholderImage;
            }          }}
        />
        <div className="absolute top-2 right-2 bg-background/90 px-2 py-1 rounded-full text-sm flex items-center gap-1">
          <Star className="h-4 w-4 text-yellow-400" />
          <span>{formatRating(rating)}</span>
        </div>
      </div>

      <div className="p-4 space-y-3">
        <h3 className="text-lg font-semibold line-clamp-1" title={name}>
          {name}
        </h3>

        <div className="space-y-2 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <MapPin className="h-4 w-4 flex-shrink-0" />
            <span className="line-clamp-1" title={address}>
              {address}
            </span>
          </div>
          {distance_to_road !== undefined && (
            <div className="flex items-center gap-2">
              <MapPin className="h-4 w-4 flex-shrink-0" />
              <span>{formatDistance(distance_to_road)} from {road}</span>
            </div>
          )}
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 flex-shrink-0" />
            <span>({total_traffic_minutes} min with traffic)</span>
          </div>
        </div>

        <div className="pt-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className={`text-sm ${getTrafficColor(total_traffic_status)}`}>
              Route traffic: {total_traffic_status}
            </span>
            {internal_traffic_status && internal_traffic_status !== 'UNKNOWN' && (
              <span className={`text-xs ${getTrafficColor(internal_traffic_status)}`}>
                (Local: {internal_traffic_status} {internal_traffic_value !== undefined ? `${internal_traffic_value}%` : ''})
              </span>
            )}
          </div>
          {/* <Button 
            size="sm" 
            onClick={handleDetailsClick}
            variant="outline"
          >
            Details
          </Button> */}
        </div>
      </div>
    </div>
  );
};

export default RestaurantCard;