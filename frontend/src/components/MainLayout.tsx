import React, { useState } from 'react';
import { Moon, Sun, LogIn, LogOut, Home } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useTheme } from './ThemeProvider';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar';
import AppSidebar from './AppSidebar';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import bLogo from '../assets/b.jpeg';
import LogoutConfirmDialog from './LogoutConfirmDialog';

interface MainLayoutProps {
  children: React.ReactNode;
  isLoggedIn?: boolean;
  userName?: string;
  onLogout?: () => void;
  onFiltersApplied?: (filters: any) => void; // Added this line
  sidebar?: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ 
  children, 
  isLoggedIn = false, 
  userName = '', 
  onLogout,
  onFiltersApplied,
  sidebar, // Added this prop to destructuring
}) => {
  const { theme, setTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const isHomePage = location.pathname === '/';

  const handleLogoutClick = () => {
    setShowLogoutConfirm(true);
  };

  const handleConfirmLogout = () => {
    setShowLogoutConfirm(false);
    if (onLogout) {
      onLogout();
    }
  };

  return (
    <SidebarProvider>
      <div className="min-h-screen flex flex-col w-full bg-background">
        <header className="border-b z-20 sticky top-0 bg-background">
          <div className="container mx-auto px-4 h-16 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <SidebarTrigger />
              <div className="flex items-center gap-2">
                <img 
                  src={bLogo} 
                  alt="Yummi logo with a fork, knife, food illustration, and a smiling emoji" 
                  className="h-6 w-6 rounded-full"
                />
                <div className="flex items-baseline">
                  <span className="text-2xl font-display">Yummi</span>
                  <span className="text-2xl">o</span>
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              {!isHomePage && (
                <Button
                  variant="ghost"
                  size="icon"
                  asChild
                  className="mr-2"
                  title="Back to Home"
                >
                  <Link to="/">
                    <Home className="h-5 w-5" />
                  </Link>
                </Button>
              )}
              
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setTheme(theme === "light" ? "dark" : "light")}
              >
                {theme === "light" ? (
                  <Moon className="h-5 w-5" />
                ) : (
                  <Sun className="h-5 w-5" />
                )}
              </Button>
              
              {isLoggedIn ? (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" className="gap-2 pl-2 pr-3 py-1">
                      <Avatar className="h-7 w-7 mr-1">
                        <AvatarFallback className="text-xs">
                          {userName?.charAt(0)?.toUpperCase() || 'U'}
                        </AvatarFallback>
                      </Avatar>
                      <span className="font-medium">{userName || 'User'}</span>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-48">
                    <DropdownMenuItem 
                      className="cursor-pointer flex items-center" 
                      onClick={handleLogoutClick}
                    >
                      <LogOut className="h-4 w-4 mr-2" />
                      Logout
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              ) : (
                <Button variant="outline" className="gap-2" asChild>
                  <Link to="/auth">
                    <LogIn className="h-5 w-5" />
                    Login
                  </Link>
                </Button>
              )}
            </div>
          </div>
        </header>
        <div className="flex flex-1">
          {/* Render the passed sidebar if provided, otherwise fall back to default AppSidebar */}
          {sidebar ? sidebar : <AppSidebar isLoggedIn={isLoggedIn} onFiltersApplied={onFiltersApplied} />}
          <main className="flex-1">
            <div className="container mx-auto px-4 py-8">{children}</div>
          </main>
        </div>
        
        <LogoutConfirmDialog 
          isOpen={showLogoutConfirm}
          onClose={() => setShowLogoutConfirm(false)}
          onConfirm={handleConfirmLogout}
        />
      </div>
    </SidebarProvider>
  );
};

export default MainLayout;