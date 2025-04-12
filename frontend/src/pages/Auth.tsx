import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useState, useEffect, useRef } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";
import Logo3D from "@/components/Logo3D";
import { ArrowLeft } from "lucide-react";

const Auth = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [name, setName] = useState("");
  const [identifier, setIdentifier] = useState(""); // Can be email or phone
  const [password, setPassword] = useState("");
  const [activeTab, setActiveTab] = useState("login");
  const [isEmail, setIsEmail] = useState(true); // Track if identifier is email
  const navigate = useNavigate();
  const { toast } = useToast();
  const identifierInputRef = useRef<HTMLInputElement>(null);

  // Auto-focus identifier field when switching tabs
  useEffect(() => {
    if (identifierInputRef.current) {
      identifierInputRef.current.focus();
    }
  }, [activeTab]);

  // Detect if identifier is email or phone
  useEffect(() => {
    setIsEmail(identifier.includes("@"));
  }, [identifier]);

  const validateIdentifier = (): boolean => {
    if (!identifier) {
      toast({
        title: "Missing Information",
        description: "Please enter email or phone number",
        variant: "destructive",
      });
      return false;
    }

    if (isEmail) {
      // Basic email validation
      if (!identifier.includes("@") || !identifier.includes(".")) {
        toast({
          title: "Invalid Email",
          description: "Please enter a valid email address",
          variant: "destructive",
        });
        return false;
      }
    } else {
      // Basic phone validation (adjust as needed)
      if (!/^\d{10,}$/.test(identifier)) {
        toast({
          title: "Invalid Phone",
          description: "Please enter a valid phone number (at least 10 digits)",
          variant: "destructive",
        });
        return false;
      }
    }
    return true;
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateIdentifier() || !password) {
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:8000/api/login/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ identifier, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Login failed");
      }

      // Store the JWT token and user data
      localStorage.setItem("token", data.token);
      localStorage.setItem("userIdentifier", identifier);
      localStorage.setItem("userName", data.user?.name || identifier.split('@')[0]);
      localStorage.setItem("isLoggedIn", "true");

      // Navigate to dashboard
      navigate('/', { 
        state: { 
          fromAuth: true,
          isLoggedIn: true,
          userIdentifier: identifier,
          userName: data.user?.name || identifier.split('@')[0]
        } 
      });
      
      toast({
        title: "Login Successful",
        description: `Welcome back, ${data.user?.name || (isEmail ? identifier.split('@')[0] : identifier)}!`,
      });
    } catch (error) {
      toast({
        title: "Login Failed",
        description: error instanceof Error ? error.message : "An error occurred",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateIdentifier() || !password) {
      return;
    }

    if (password.length < 6) {
      toast({
        title: "Password too short",
        description: "Password must be at least 6 characters",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    
    try {
      const response = await fetch("http://localhost:8000/api/signup/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ identifier, password, name }),
      });

      const data = await response.json();

      if (!response.ok) {
        if (response.status === 400 && data.error?.includes("already exists")) {
          toast({
            title: "Already Registered",
            description: "Please login or use a different email/phone",
            variant: "destructive",
          });
          setActiveTab("login");
          return;
        }
        throw new Error(data.error || "Registration failed");
      }

      // Clear form and switch to login tab
      setName("");
      setIdentifier("");
      setPassword("");
      
      toast({
        title: "Registration Successful",
        description: "Please login with your credentials",
      });
      setActiveTab("login");
    } catch (error) {
      toast({
        title: "Registration Failed",
        description: error instanceof Error ? error.message : "An error occurred",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container relative min-h-screen flex-col items-center justify-center grid lg:max-w-none lg:grid-cols-2 lg:px-0">
      <div className="relative hidden h-full flex-col bg-muted p-10 text-white lg:flex dark:border-r">
        <div className="absolute inset-0 bg-zinc-900" />
        <div className="relative z-20 flex items-center text-lg font-medium">
          <Logo3D size="small" className="mr-2" />
          <span className="font-display text-2xl">Yummi</span>
          <span className="text-2xl">o</span>
        </div>
        <div className="relative z-20 mt-auto">
          <blockquote className="space-y-2">
            <p className="text-lg">
              "Find the perfect restaurant along your journey, avoiding traffic and discovering great food."
            </p>
          </blockquote>
        </div>
      </div>
      <div className="lg:p-8">
        <div className="mx-auto flex w-full flex-col justify-center space-y-6 sm:w-[350px]">
          <div className="flex flex-col space-y-2 text-center">
            <div className="flex items-center justify-center mb-4">
              <Button 
                variant="ghost" 
                size="icon" 
                asChild 
                className="absolute left-4 top-4"
              >
                <Link to="/">
                  <ArrowLeft className="h-5 w-5" />
                </Link>
              </Button>
            </div>
            <h1 className="text-2xl font-semibold tracking-tight">
              Welcome to Yummio
            </h1>
            <p className="text-sm text-muted-foreground">
              {isLoading ? "Processing..." : "Enter your details to continue"}
            </p>
          </div>
          <Tabs 
            value={activeTab} 
            onValueChange={setActiveTab}
            className="w-full"
          >
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="login">Login</TabsTrigger>
              <TabsTrigger value="register">Register</TabsTrigger>
            </TabsList>
            <TabsContent value="login">
              <form onSubmit={handleLogin} className="space-y-4">
                <Input
                  type={isEmail ? "email" : "tel"}
                  placeholder="Email or Phone Number"
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  disabled={isLoading}
                  ref={identifierInputRef}
                  autoFocus
                />
                <Input
                  type="password"
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={isLoading}
                />
                <Button className="w-full" disabled={isLoading}>
                  {isLoading ? "Logging in..." : "Login"}
                </Button>
              </form>
            </TabsContent>
            <TabsContent value="register">
              <form onSubmit={handleRegister} className="space-y-4">
                <Input
                  type="text"
                  placeholder="Name (optional)"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  disabled={isLoading}
                />
                <Input
                  type={isEmail ? "email" : "tel"}
                  placeholder="Email or Phone Number"
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  disabled={isLoading}
                />
                <Input
                  type="password"
                  placeholder="Password (min 6 characters)"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={isLoading}
                />
                <Button className="w-full" disabled={isLoading}>
                  {isLoading ? "Registering..." : "Register"}
                </Button>
              </form>
            </TabsContent>
          </Tabs>
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-background px-2 text-muted-foreground">
                Or continue with
              </span>
            </div>
          </div>
          <Button variant="outline" disabled={isLoading}>
            Continue with Google
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Auth;