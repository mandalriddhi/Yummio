import {
  Filter,
  History,
  ChevronDown,
  Save,
  Check,
  Clock,
  MapPin,
  ArrowRight,
  Trash2,
} from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { useToast } from "@/hooks/use-toast";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import MultiSelectCheckbox from "./MultiSelectCheckbox.tsx";
import { useEffect } from "react";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useState } from "react";

interface AppSidebarProps {
  isLoggedIn: boolean;
  onFiltersApplied?: (filters: any) => void;
  onHistorySearch?: (source: string, destination: string) => void;
}

const AppSidebar = ({
  isLoggedIn,
  onFiltersApplied,
  onHistorySearch,
}: AppSidebarProps) => {
  const { toast } = useToast();
  const navigate = useNavigate();

  // State for filter values
  const [sortOption, setSortOption] = useState("rating"); // Default to rating
  const [minRating, setMinRating] = useState(3);
  const [maxTrafficTime, setMaxTrafficTime] = useState(30);
  const [vegetarianOnly, setVegetarianOnly] = useState(false);
  const [openNow, setOpenNow] = useState(true);
  const [history, setHistory] = useState<any[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [selectedFoodCategories, setSelectedFoodCategories] = useState<string[]>([]);
  const [selectedCuisineTypes, setSelectedCuisineTypes] = useState<string[]>([]);

  const foodCategories = [
    { value: "biryani", label: "Biryani" },
    { value: "combo", label: "Combo Meals" },
    { value: "desserts", label: "Desserts" },
    { value: "burgers", label: "Burgers" },
    { value: "pizza", label: "Pizza" },
  ];

  const cuisineTypes = [
    { value: "indian", label: "Indian" },
    { value: "chinese", label: "Chinese" },
    { value: "mughlai", label: "Mughlai" },
    { value: "italian", label: "Italian" },
    { value: "mexican", label: "Mexican" },
  ];

  useEffect(() => {
    fetchHistory();
  }, [isLoggedIn]);

  const fetchHistory = async () => {
    if (!isLoggedIn) return;

    setHistoryLoading(true);
    try {
      const token = localStorage.getItem("token");
      if (!token) {
        throw new Error("No authentication token found");
      }

      const response = await fetch("http://localhost:8000/api/history/", {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch history");
      }

      const data = await response.json();
      console.log("History data:", data);
      setHistory(data.history || []);
    } catch (error) {
      console.error("Error fetching history:", error);
      toast({
        title: "Error",
        description: "Failed to load history",
        variant: "destructive",
      });
    } finally {
      setHistoryLoading(false);
    }
  };

  const handleHistorySearch = (source: string, destination: string) => {
    if (onHistorySearch) {
      onHistorySearch(source, destination);
    }
  };

  const handleRestrictedAction = () => {
    if (!isLoggedIn) {
      toast({
        title: "Login Required",
        description: "Please login to access this feature",
        variant: "destructive",
      });
      navigate("/auth");
    }
  };

  const formatDate = (timestamp: string) => {
    if (!timestamp) return "Unknown time";
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const handleSaveFilters = () => {
    toast({
      title: "Filters Saved",
      description: "Your filter preferences have been saved",
    });
  };

  const handleApplyFilters = async () => {
    try {
      const filters = {
        sortOption,
        minRating,
        maxTrafficTime,
        vegetarianOnly,
        openNow,
        foodCategories: selectedFoodCategories, // Include selected food categories
        cuisineTypes: selectedCuisineTypes,
      };

      if (onFiltersApplied) {
        onFiltersApplied(filters);
      }

      toast({
        title: "Filters Applied",
        description: "Restaurants have been filtered and sorted",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to apply filters",
        variant: "destructive",
      });
    }
  };

  const handleDeleteAllHistory = async () => {
    if (!isLoggedIn) return;

    try {
      const token = localStorage.getItem("token");
      if (!token) {
        throw new Error("No authentication token found");
      }

      const response = await fetch("http://localhost:8000/api/history/", {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to delete all history");
      }

      setHistory([]);
      toast({
        title: "History Cleared",
        description: "All search history has been deleted",
      });
    } catch (error) {
      console.error("Error deleting all history:", error);
      toast({
        title: "Error",
        description: "Failed to delete all history",
        variant: "destructive",
      });
    }
  };

  // New function to delete a specific history entry
  const handleDeleteHistoryEntry = async (timestamp: string) => {
    if (!isLoggedIn) return;

    try {
      const token = localStorage.getItem("token");
      if (!token) {
        throw new Error("No authentication token found");
      }

      const response = await fetch("http://localhost:8000/api/history/", {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ timestamp }),
      });

      if (!response.ok) {
        throw new Error("Failed to delete history entry");
      }

      setHistory((prevHistory) =>
        prevHistory.filter((entry) => entry.timestamp !== timestamp)
      );
      toast({
        title: "History Entry Deleted",
        description: "The selected search history has been deleted",
      });
    } catch (error) {
      console.error("Error deleting history entry:", error);
      toast({
        title: "Error",
        description: "Failed to delete history entry",
        variant: "destructive",
      });
    }
  };

  return (
    <Sidebar className="mt-16 pt-0">
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Options</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <Popover>
                  <PopoverTrigger asChild>
                    <SidebarMenuButton
                      onClick={handleRestrictedAction}
                      tooltip="Filter restaurants"
                    >
                      <Filter />
                      <span>Filters</span>
                    </SidebarMenuButton>
                  </PopoverTrigger>
                  {isLoggedIn && (
                    <PopoverContent
                      side="right"
                      align="start"
                      className="w-80 p-4 max-h-[80vh] overflow-y-auto" // Added max-h-[80vh] and overflow-y-auto
                    >
                      <div className="space-y-6">
                        <div className="space-y-4">
                          <h3 className="text-sm font-medium">Sort By</h3>
                          <Select
                            value={sortOption}
                            onValueChange={(value) => setSortOption(value)}
                          >
                            <SelectTrigger className="w-full">
                              <SelectValue placeholder="Select sorting option" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectGroup>
                                <SelectLabel>Sorting Options</SelectLabel>
                                <SelectItem value="rating">
                                  Sort by Rating
                                </SelectItem>
                                <SelectItem value="traffic">
                                  Sort by Traffic
                                </SelectItem>
                              </SelectGroup>
                            </SelectContent>
                          </Select>
                        </div>

                        <div className="space-y-4">
                          <MultiSelectCheckbox
                          label="Food Specific"
                          options={foodCategories}
                          selectedValues={selectedFoodCategories}
                          onValueChange={setSelectedFoodCategories}
                        />
                        </div>

                        <div className="space-y-4">
                          <MultiSelectCheckbox
                          label="Type of Food"
                          options={cuisineTypes}
                          selectedValues={selectedCuisineTypes}
                          onValueChange={setSelectedCuisineTypes}
                        />
                        </div>

                        <div className="space-y-4">
                          <h3 className="text-sm font-medium">
                            Minimum Rating
                          </h3>
                          <div className="flex flex-col space-y-2">
                            <Slider
                              value={[minRating]}
                              min={1}
                              max={5}
                              step={0.5}
                              onValueChange={(value) => setMinRating(value[0])}
                            />
                            <div className="flex justify-between text-xs text-muted-foreground">
                              <span>1</span>
                              <span>3</span>
                              <span>5</span>
                            </div>
                          </div>
                        </div>

                        <div className="space-y-4">
                          <h3 className="text-sm font-medium">
                            Traffic Time Constraint (minutes)
                          </h3>
                          <div className="flex flex-col space-y-2">
                            <Slider
                              value={[maxTrafficTime]}
                              min={5}
                              max={60}
                              step={5}
                              onValueChange={(value) =>
                                setMaxTrafficTime(value[0])
                              }
                            />
                            <div className="flex justify-between text-xs text-muted-foreground">
                              <span>5</span>
                              <span>30</span>
                              <span>60</span>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center justify-between">
                          <Label htmlFor="veg">Vegetarian Only</Label>
                          <Switch
                            id="veg"
                            checked={vegetarianOnly}
                            onCheckedChange={setVegetarianOnly}
                          />
                        </div>
                        <div className="flex items-center justify-between">
                          <Label htmlFor="open">Open Now</Label>
                          <Switch
                            id="open"
                            checked={openNow}
                            onCheckedChange={setOpenNow}
                          />
                        </div>

                        <div className="pt-4 flex gap-2">
                          <Button
                            onClick={handleApplyFilters}
                            className="w-full flex items-center justify-center gap-2"
                          >
                            <Check className="h-4 w-4" />
                            Apply Filters
                          </Button>
                        </div>
                      </div>
                    </PopoverContent>
                  )}
                </Popover>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <Popover>
                  <PopoverTrigger asChild>
                    <SidebarMenuButton
                      onClick={handleRestrictedAction}
                      tooltip="View history"
                    >
                      <History />
                      <span>History</span>
                    </SidebarMenuButton>
                  </PopoverTrigger>
                  {isLoggedIn && (
                    <PopoverContent
                      side="right"
                      align="start"
                      className="w-80 p-4 max-h-[70vh] overflow-y-auto"
                    >
                      <div className="space-y-4">
                        <div className="flex justify-between items-center">
                          <h3 className="text-lg font-semibold">
                            Search History
                          </h3>
                          {history.length > 0 && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={handleDeleteAllHistory}
                              className="text-red-500 border-red-500"
                            >
                              <Trash2 className="h-4 w-4 mr-1" />
                              Delete All
                            </Button>
                          )}
                        </div>

                        {historyLoading ? (
                          <div className="flex justify-center py-4">
                            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary"></div>
                          </div>
                        ) : history.length === 0 ? (
                          <p className="text-sm text-muted-foreground text-center py-4">
                            No search history found
                          </p>
                        ) : (
                          <div className="space-y-3">
                            {history.map((entry, index) => (
                              <div
                                key={index}
                                className="border rounded-lg p-3 flex justify-between items-center hover:bg-accent/50 transition-colors"
                              >
                                <div
                                  className="flex-1 cursor-pointer"
                                  onClick={() =>
                                    handleHistorySearch(
                                      entry.source,
                                      entry.destination
                                    )
                                  }
                                >
                                  <div className="flex items-center space-x-2">
                                    <MapPin className="h-4 w-4 text-primary" />
                                    <span className="text-sm font-medium">
                                      {entry.source}
                                    </span>
                                    <ArrowRight className="h-3 w-3 text-muted-foreground" />
                                    <MapPin className="h-4 w-4 text-primary" />
                                    <span className="text-sm font-medium">
                                      {entry.destination}
                                    </span>
                                  </div>
                                  <div className="flex items-center mt-2 space-x-2 text-xs text-muted-foreground">
                                    <Clock className="h-3 w-3" />
                                    <span>{formatDate(entry.timestamp)}</span>
                                  </div>
                                  {entry.restaurants_count > 0 && (
                                    <div className="mt-1 text-xs text-muted-foreground">
                                      Found {entry.restaurants_count}{" "}
                                      restaurants
                                    </div>
                                  )}
                                </div>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={(e) => {
                                    e.stopPropagation(); // Prevent triggering handleHistorySearch
                                    handleDeleteHistoryEntry(entry.timestamp);
                                  }}
                                  className="text-red-500 hover:text-red-700 ml-2"
                                >
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </PopoverContent>
                  )}
                </Popover>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
};

export default AppSidebar;
