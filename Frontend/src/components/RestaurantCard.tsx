
import { Star, MapPin, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';

const RestaurantCard = () => {
  return (
    <div className="rounded-lg border bg-card text-card-foreground shadow">
      <div className="relative h-48">
        <img
          src="https://source.unsplash.com/random/400x300/?restaurant"
          alt="Restaurant"
          className="w-full h-full object-cover rounded-t-lg"
        />
        <div className="absolute top-2 right-2 bg-background/90 px-2 py-1 rounded-full text-sm flex items-center gap-1">
          <Star className="h-4 w-4 text-yellow-400" />
          <span>4.5</span>
        </div>
      </div>
      
      <div className="p-4 space-y-3">
        <h3 className="text-lg font-semibold">Restaurant Name</h3>
        
        <div className="space-y-2 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <MapPin className="h-4 w-4" />
            <span>2.5 km away</span>
          </div>
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4" />
            <span>~15 min travel time</span>
          </div>
        </div>
        
        <div className="pt-3 flex items-center justify-between">
          <span className="text-sm">Traffic: Low</span>
          <Button size="sm">View Details</Button>
        </div>
      </div>
    </div>
  );
};

export default RestaurantCard;
