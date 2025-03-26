
import { Filter, History, ChevronDown, Save } from 'lucide-react';
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from '@/components/ui/sidebar';
import { useToast } from '@/hooks/use-toast';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface AppSidebarProps {
  isLoggedIn: boolean;
}

const AppSidebar = ({ isLoggedIn }: AppSidebarProps) => {
  const { toast } = useToast();
  const navigate = useNavigate();

  const handleRestrictedAction = () => {
    if (!isLoggedIn) {
      toast({
        title: "Login Required",
        description: "Please login to access this feature",
        variant: "destructive",
      });
      navigate('/auth');
    }
  };

  const handleSaveFilters = () => {
    toast({
      title: "Filters Saved",
      description: "Your filter preferences have been saved",
      variant: "success",
    });
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
                    <SidebarMenuButton onClick={handleRestrictedAction} tooltip="Filter restaurants">
                      <Filter />
                      <span>Filters</span>
                    </SidebarMenuButton>
                  </PopoverTrigger>
                  {isLoggedIn && (
                    <PopoverContent side="right" align="start" className="w-80 p-4">
                      <div className="space-y-6">
                        <div className="space-y-4">
                          <h3 className="text-sm font-medium">Sort By</h3>
                          <Select>
                            <SelectTrigger className="w-full">
                              <SelectValue placeholder="Select sorting option" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="rating">Sort by Rating</SelectItem>
                              <SelectItem value="traffic">Sort by Traffic</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>

                        <div className="space-y-4">
                          <h3 className="text-sm font-medium">Food Specific</h3>
                          <Select>
                            <SelectTrigger className="w-full">
                              <SelectValue placeholder="Select food category" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="biryani">Biryani</SelectItem>
                              <SelectItem value="combo">Combo Meals</SelectItem>
                              <SelectItem value="desserts">Desserts</SelectItem>
                              <SelectItem value="burgers">Burgers</SelectItem>
                              <SelectItem value="pizza">Pizza</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>

                        <div className="space-y-4">
                          <h3 className="text-sm font-medium">Type of Food</h3>
                          <Select>
                            <SelectTrigger className="w-full">
                              <SelectValue placeholder="Select cuisine" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="indian">Indian</SelectItem>
                              <SelectItem value="chinese">Chinese</SelectItem>
                              <SelectItem value="mughlai">Mughlai</SelectItem>
                              <SelectItem value="italian">Italian</SelectItem>
                              <SelectItem value="mexican">Mexican</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>

                        <div className="space-y-4">
                          <h3 className="text-sm font-medium">Minimum Rating</h3>
                          <div className="flex flex-col space-y-2">
                            <Slider defaultValue={[3]} min={1} max={5} step={0.5} />
                            <div className="flex justify-between text-xs text-muted-foreground">
                              <span>1</span>
                              <span>3</span>
                              <span>5</span>
                            </div>
                          </div>
                        </div>

                        <div className="space-y-4">
                          <h3 className="text-sm font-medium">Traffic Time Constraint (minutes)</h3>
                          <div className="flex flex-col space-y-2">
                            <Slider defaultValue={[30]} min={5} max={60} step={5} />
                            <div className="flex justify-between text-xs text-muted-foreground">
                              <span>5</span>
                              <span>30</span>
                              <span>60</span>
                            </div>
                          </div>
                        </div>

                        <div className="space-y-4">
                          <h3 className="text-sm font-medium">Estimated Price Range</h3>
                          <div className="flex flex-col space-y-2">
                            <Slider defaultValue={[300, 800]} min={100} max={2000} step={100} />
                            <div className="flex justify-between text-xs text-muted-foreground">
                              <span>$</span>
                              <span>$$</span>
                              <span>$$$</span>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center justify-between">
                          <Label htmlFor="veg">Vegetarian Only</Label>
                          <Switch id="veg" />
                        </div>
                        <div className="flex items-center justify-between">
                          <Label htmlFor="open">Open Now</Label>
                          <Switch id="open" />
                        </div>
                        <div className="flex items-center justify-between">
                          <Label htmlFor="delivery">Delivery Available</Label>
                          <Switch id="delivery" />
                        </div>

                        <div className="pt-4">
                          <Button 
                            onClick={handleSaveFilters} 
                            className="w-full flex items-center justify-center gap-2"
                          >
                            <Save className="h-4 w-4" />
                            Save Filters
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
                    <SidebarMenuButton onClick={handleRestrictedAction} tooltip="View history">
                      <History />
                      <span>History</span>
                    </SidebarMenuButton>
                  </PopoverTrigger>
                  {isLoggedIn && (
                    <PopoverContent side="right" align="start" className="w-64 p-4">
                      <p className="text-sm text-muted-foreground">Your recent searches will appear here</p>
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
