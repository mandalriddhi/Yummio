
import { useState, useEffect } from 'react';
import { Star, MapPin, Clock, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import MainLayout from '@/components/MainLayout';
import RestaurantCard from '@/components/RestaurantCard';
import { useNavigate } from 'react-router-dom';
import { useToast } from '@/hooks/use-toast';

const Restaurants = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userName, setUserName] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();
  const { toast } = useToast();
  
  useEffect(() => {
    // Check if user is logged in
    const loginStatus = localStorage.getItem('isLoggedIn');
    const name = localStorage.getItem('userName');
    
    if (loginStatus !== 'true' || !name) {
      // Redirect to login if not logged in
      toast({
        title: "Authentication Required",
        description: "Please login to view restaurants",
        variant: "destructive",
      });
      navigate('/auth');
      return;
    }
    
    setIsLoggedIn(true);
    setUserName(name);
  }, [navigate, toast]);

  const handleLogout = () => {
    setIsLoggedIn(false);
    localStorage.removeItem('isLoggedIn');
    localStorage.removeItem('userName');
    toast({
      title: "Logged Out",
      description: "You have been successfully logged out",
    });
    navigate('/');
  };

  const handleSearch = () => {
    toast({
      title: "Search initiated",
      description: `Searching for '${searchQuery}'`,
    });
    // In a real app, this would filter the restaurant data based on the search query
  };
  
  return (
    <MainLayout isLoggedIn={isLoggedIn} userName={userName} onLogout={handleLogout}>
      <div className="max-w-6xl mx-auto space-y-6 p-4">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold">Restaurants on Your Route</h1>
          <Button variant="outline">View on Map</Button>
        </div>
        
        <div className="flex w-full items-center gap-2">
          <div className="relative flex-1">
            <Input
              className="pr-10"
              placeholder="Search restaurants by name, cuisine, or location..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground">
              <Search className="h-4 w-4" />
            </div>
          </div>
          <Button onClick={handleSearch}>
            <Search className="mr-2 h-4 w-4" />
            Search
          </Button>
        </div>
        
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <RestaurantCard />
          <RestaurantCard />
          <RestaurantCard />
        </div>
      </div>
    </MainLayout>
  );
};

export default Restaurants;
