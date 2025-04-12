import { useState, useEffect } from "react";
import { Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import MainLayout from "@/components/MainLayout";
import RestaurantCard from "@/components/RestaurantCard";
import { useNavigate, useLocation } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";
import AppSidebar from "@/components/AppSidebar";

const Restaurants = () => {
  const [restaurants, setRestaurants] = useState([]);
  const [filteredRestaurants, setFilteredRestaurants] = useState([]);
  const [visibleRestaurants, setVisibleRestaurants] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [showAll, setShowAll] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [userName, setUserName] = useState<string>('');
  const [sortOption, setSortOption] = useState("rating");
  const navigate = useNavigate();
  const location = useLocation();
  const { toast } = useToast();

  useEffect(() => {
    const checkAuthStatus = () => {
      const token = localStorage.getItem('token');
      const name = localStorage.getItem('userName');
      const loginStatus = localStorage.getItem('isLoggedIn');
      return token && name && loginStatus === 'true';
    };

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
    }

    const incomingRestaurants = location.state?.restaurants || [];
    console.log("Received from navigation:", incomingRestaurants.length, incomingRestaurants);

    if (!Array.isArray(incomingRestaurants) || incomingRestaurants.length === 0) {
      toast({ title: "No Restaurants", description: "No data received", variant: "destructive" });
      navigate("/");
      return;
    }

  //   setRestaurants(incomingRestaurants);
  //   setFilteredRestaurants(incomingRestaurants);
  //   const initialCount = Math.min(20, incomingRestaurants.length);
  //   setVisibleRestaurants(incomingRestaurants.slice(0, initialCount));
  //   console.log("Initial restaurants set:", initialCount, incomingRestaurants.slice(0, initialCount));
  // }, [location.state, navigate, toast]);

  const sortedByRating = [...incomingRestaurants].sort((a, b) => {
    const ratingA = a.rating === "Not rated" ? 0 : parseFloat(a.rating);
    const ratingB = b.rating === "Not rated" ? 0 : parseFloat(b.rating);
    return ratingB - ratingA;
  });

  setRestaurants(sortedByRating);
  setFilteredRestaurants(sortedByRating);
  const initialCount = Math.min(20, sortedByRating.length);
  setVisibleRestaurants(sortedByRating.slice(0, initialCount));
  console.log("Initial restaurants set (sorted by rating):", initialCount, sortedByRating.slice(0, initialCount));
  }, [location.state, navigate, toast]);


  const handleLogout = async () => {
    try {
      const token = localStorage.getItem('token');
      localStorage.removeItem('token');
      localStorage.removeItem('userEmail');
      localStorage.removeItem('userName');
      localStorage.removeItem('isLoggedIn');
      setIsLoggedIn(false);
      setUserName('');

      if (token) {
        await fetch("http://localhost:8000/api/logout/", {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        });
      }

      navigate('/', { replace: true });
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

  const handleSearch = () => {
    const filtered = restaurants.filter(r =>
      r.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.address.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (r.road && r.road.toLowerCase().includes(searchQuery.toLowerCase()))
    );
    setFilteredRestaurants(filtered);
    setVisibleRestaurants(filtered.slice(0, Math.min(20, filtered.length)));
    setShowAll(false);
    console.log("Filtered restaurants after search:", filtered.length);
  };

  const handleViewAll = () => {
    setVisibleRestaurants(filteredRestaurants);
    setShowAll(true);
    console.log("Showing all:", filteredRestaurants.length);
  };

  const handleViewLess = () => {
    setVisibleRestaurants(filteredRestaurants.slice(0, Math.min(20, filteredRestaurants.length)));
    setShowAll(false);
  };


  const applySortAndFilter = (restaurantsToFilter: any[], newSortOption: string) => {
    let sortedRestaurants = [...restaurantsToFilter];

    if (newSortOption === "rating") {
      sortedRestaurants.sort((a, b) => {
        const ratingA = a.rating === "Not rated" ? 0 : parseFloat(a.rating);
        const ratingB = b.rating === "Not rated" ? 0 : parseFloat(b.rating);
        return ratingB - ratingA; // Descending order
      });
    } else if (newSortOption === "traffic") {
      sortedRestaurants.sort((a, b) => {
        return a.total_traffic_minutes - b.total_traffic_minutes; // Ascending order
      });
    }

    setFilteredRestaurants(sortedRestaurants);
    setVisibleRestaurants(sortedRestaurants.slice(0, Math.min(20, sortedRestaurants.length)));
    setShowAll(false);
  };

  const handleFiltersApplied = (filters: any) => {
    setSortOption(filters.sortOption);
    let filtered = [...restaurants];

    // Apply additional filters if needed (e.g., minRating, maxTrafficTime)
    if (filters.minRating > 0) {
      filtered = filtered.filter(
        (r) => r.rating !== "Not rated" && parseFloat(r.rating) >= filters.minRating
      );
    }
    if (filters.maxTrafficTime) {
      filtered = filtered.filter(
        (r) => r.total_traffic_minutes <= filters.maxTrafficTime
      );
    }
    if (filters.vegetarianOnly) {
      // Assuming a way to determine vegetarian status; adjust as needed
      filtered = filtered.filter((r) => r.name.toLowerCase().includes("vegetarian"));
    }
    if (filters.openNow) {
      // Assuming internal_traffic_status indicates openness; adjust as needed
      filtered = filtered.filter((r) => r.internal_traffic_status !== "CLOSED");
    }

    applySortAndFilter(filtered, filters.sortOption);
  };

  return (
    <MainLayout
      isLoggedIn={isLoggedIn}
      userName={userName}
      onLogout={handleLogout}
      sidebar={<AppSidebar isLoggedIn={isLoggedIn} onFiltersApplied={handleFiltersApplied} />}
    >
      <div className="max-w-6xl mx-auto space-y-6 p-4">
        <h1 className="text-2xl font-bold">Restaurants on Your Route</h1>
        <div className="space-y-2">
          <div className="flex gap-2">
            <Input
              placeholder="Search restaurants..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            />
            <Button onClick={handleSearch}>
              <Search /> Search
            </Button>
          </div>
          <div className="flex justify-end space-x-2">
            {filteredRestaurants.length > 20 && !showAll && (
              <Button
                variant="outline"
                onClick={handleViewAll}
                className="text-orange-500 border-orange-500"
              >
                View All ({filteredRestaurants.length})
              </Button>
            )}
            {showAll && filteredRestaurants.length > 20 && (
              <Button
                variant="outline"
                onClick={handleViewLess}
                className="text-orange-500 border-orange-500"
              >
                View Less
              </Button>
            )}
          </div>
        </div>

        <div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {visibleRestaurants.map((r) => (
              <RestaurantCard
                key={r.place_id}
                name={r.name}
                address={r.address}
                rating={r.rating}
                distance_to_road={r.distance_to_road}
                travel_time={r.travel_time}
                total_traffic_status={r.total_traffic_status}
                total_traffic_minutes={r.total_traffic_minutes}
                internal_traffic_status={r.internal_traffic_status}
                internal_traffic_value={r.internal_traffic_value}
                road={r.road}
                place_id={r.place_id}
                onDetailsClick={() => console.log(r.place_id)}
                main_photo={r.main_photo}
                photos={r.photos}
              />
            ))}
            {visibleRestaurants.length === 0 && <p>No restaurants found</p>}
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default Restaurants;