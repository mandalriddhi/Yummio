import { useState, useEffect } from 'react';
import { Search, Map } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import MainLayout from '@/components/MainLayout';
import { useNavigate, useLocation } from 'react-router-dom';
import { useToast } from '@/hooks/use-toast';
import bLogo from '../assets/b.jpeg';
import '../styles/glow.css';

const Index = () => {
  const [source, setSource] = useState<string>('');
  const [destination, setDestination] = useState<string>('');
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [userName, setUserName] = useState<string>('');
  const [isSearching, setIsSearching] = useState<boolean>(false); // Debounce flag
  const navigate = useNavigate();
  const location = useLocation();
  const { toast } = useToast();

  const checkAuthStatus = () => {
    const token = localStorage.getItem('token');
    const name = localStorage.getItem('userName');
    const loginStatus = localStorage.getItem('isLoggedIn');
    return token && name && loginStatus === 'true';
  };

  useEffect(() => {
    const authStatus = checkAuthStatus();
    if (authStatus) {
      setIsLoggedIn(true);
      setUserName(localStorage.getItem('userName') || 'User');
    } else {
      setIsLoggedIn(false);
      setUserName('');
    }

    if (location.state?.isLoggedIn) {
      setIsLoggedIn(true);
      const newUserName = location.state.userName || 'User';
      setUserName(newUserName);
      localStorage.setItem('isLoggedIn', 'true');
      localStorage.setItem('userName', newUserName);
      if (!localStorage.getItem('token')) {
        console.warn('Token missing after login redirect');
      }
    }
  }, [location]);

  const clearAuthData = async () => {
    const token = localStorage.getItem('token');
    localStorage.removeItem('token');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('userName');
    localStorage.removeItem('isLoggedIn');
    setIsLoggedIn(false);
    setUserName('');

    if (token) {
      try {
        await fetch("http://localhost:8000/api/logout/", {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        });
      } catch (error) {
        console.error("Logout API error:", error);
      }
    }
  };

  const handleSearch = async () => {
    if (isSearching) return; // Prevent multiple clicks
    setIsSearching(true);

    if (!source || !destination) {
      toast({
        title: "Missing Information",
        description: "Please enter both source and destination",
        variant: "destructive",
      });
      setIsSearching(false);
      return;
    }

    if (!checkAuthStatus()) {
      toast({
        title: "Login Required",
        description: "Please login to search for restaurants",
        variant: "destructive",
      });
      navigate('/auth');
      setIsSearching(false);
      return;
    }

    const token = localStorage.getItem('token');
    if (!token) {
      toast({
        title: "Authentication Error",
        description: "No authentication token found. Please login again.",
        variant: "destructive",
      });
      await clearAuthData();
      navigate('/auth');
      setIsSearching(false);
      return;
    }

    try {
      const response = await fetch("http://localhost:8000/api/restaurants/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({
          source,
          destination,
          sort_choice: "3",
          food_preference: "",
        }),
      });

      if (response.status === 401) {
        throw new Error("Unauthorized: Invalid or expired token");
      }

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Search failed");
      }

      navigate('/restaurants', { 
        state: { 
          restaurants: data.restaurants,
          isLoggedIn: true,
          userName: localStorage.getItem('userName') || 'User'
        } 
      });
    } catch (error) {
      console.error("Search error:", error);
      if (error.message.includes("Unauthorized")) {
        toast({
          title: "Session Expired",
          description: "Your session has expired. Please login again.",
          variant: "destructive",
        });
        await clearAuthData();
        navigate('/auth');
      } else {
        toast({
          title: "Search Failed",
          description: error instanceof Error ? error.message : "An error occurred",
          variant: "destructive",
        });
      }
    } finally {
      setTimeout(() => setIsSearching(false), 1000); // Re-enable after 1s
    }
  };

  const handleLogout = async () => {
    try {
      await clearAuthData();
      navigate('/', { replace: true });
      window.location.reload();
      
      toast({
        title: "Logged Out",
        description: "You have been successfully logged out",
      });
    } catch (error) {
      toast({
        title: "Logout Failed",
        description: "There was an error logging out",
        variant: "destructive",
      });
    }
  };

  return (
    <MainLayout 
      isLoggedIn={isLoggedIn} 
      userName={userName} 
      onLogout={handleLogout}
    >
      <div className="max-w-2xl mx-auto space-y-8">
        <div className="flex flex-col items-center mb-8">
          <div className="mb-8">
            <img 
              src={bLogo} 
              alt="Yummi logo with a fork, knife, food illustration, and a smiling emoji" 
              className="h-24 w-24 rounded-full glow-effect twinkle-effect" 
            />
          </div>
        </div>
      
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-display font-bold">Find Your Perfect Meal</h1>
          <p className="text-muted-foreground">
            Discover restaurants along your route, optimized for both your taste and traffic conditions
          </p>
        </div>

        <div className="space-y-4 p-6 rounded-xl bg-card">
          <div className="space-y-2">
            <label htmlFor="source" className="text-sm font-medium">
              Starting Point
            </label>
            <Input
              id="source"
              placeholder="Enter starting location"
              value={source}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSource(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="destination" className="text-sm font-medium">
              Destination
            </label>
            <Input
              id="destination"
              placeholder="Enter destination"
              value={destination}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setDestination(e.target.value)}
            />
          </div>

          <div className="flex gap-2">
            <Button onClick={handleSearch} className="flex-1 gap-2" disabled={isSearching}>
              <Search className="h-4 w-4" />
              Find Restaurants
            </Button>
            <Button 
              variant="outline" 
              onClick={() => {
                if (!isLoggedIn) {
                  toast({
                    title: "Login Required",
                    description: "Please login to use the map feature",
                    variant: "destructive",
                  });
                  navigate('/auth');
                  return;
                }
                navigate('/map');
              }} 
              className="gap-2"
            >
              <Map className="h-4 w-4" />
              Find from Map
            </Button>
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default Index;