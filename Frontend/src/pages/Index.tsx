
// // import { useState, useEffect } from 'react';
// // import { Search, Map } from 'lucide-react';
// // import { Button } from '@/components/ui/button';
// // import { Input } from '@/components/ui/input';
// // import MainLayout from '@/components/MainLayout';
// // import { useNavigate, useLocation } from 'react-router-dom';
// // import { useToast } from '@/hooks/use-toast';
// // import Logo3D from '@/components/Logo3D';

// // const Index = () => {
// //   const [source, setSource] = useState('');
// //   const [destination, setDestination] = useState('');
// //   const [isLoggedIn, setIsLoggedIn] = useState(false);
// //   const [userName, setUserName] = useState('');
// //   const navigate = useNavigate();
// //   const location = useLocation();
// //   const { toast } = useToast();

// //   // Check if user is coming from auth page with login status
// //   useEffect(() => {
// //     const loginStatus = localStorage.getItem('isLoggedIn');
// //     const name = localStorage.getItem('userName');
    
// //     if (loginStatus === 'true' && name) {
// //       setIsLoggedIn(true);
// //       setUserName(name);
// //     }

// //     // If coming from auth with state, update login status
// //     if (location.state?.isLoggedIn) {
// //       setIsLoggedIn(true);
// //       const newUserName = location.state.userName || 'User';
// //       setUserName(newUserName);
      
// //       // Store in localStorage for persistence
// //       localStorage.setItem('isLoggedIn', 'true');
// //       localStorage.setItem('userName', newUserName);
// //     }
// //   }, [location]);

// //   const handleSearch = () => {
// //     if (!source || !destination) {
// //       toast({
// //         title: "Missing Information",
// //         description: "Please enter both source and destination",
// //         variant: "destructive",
// //       });
// //       return;
// //     }

// //     if (!isLoggedIn) {
// //       toast({
// //         title: "Login Required",
// //         description: "Please login to search for restaurants",
// //         variant: "destructive",
// //       });
// //       navigate('/auth');
// //       return;
// //     }

// //     navigate('/restaurants');
// //   };

// //   const handleLogout = () => {
// //     setIsLoggedIn(false);
// //     setUserName('');
// //     localStorage.removeItem('isLoggedIn');
// //     localStorage.removeItem('userName');
// //     toast({
// //       title: "Logged Out",
// //       description: "You have been successfully logged out",
// //     });
// //   };

// //   return (
// //     <MainLayout 
// //       isLoggedIn={isLoggedIn} 
// //       userName={userName} 
// //       onLogout={handleLogout}
// //     >
// //       <div className="max-w-2xl mx-auto space-y-8">
// //         <div className="flex flex-col items-center mb-8">
// //           <div className="mb-8">
// //             <Logo3D size="large" />
// //           </div>
// //         </div>
      
// //         <div className="text-center space-y-4">
// //           <h1 className="text-4xl font-display font-bold">Find Your Perfect Meal</h1>
// //           <p className="text-muted-foreground">
// //             Discover restaurants along your route, optimized for both your taste and traffic conditions
// //           </p>
// //         </div>

// //         <div className="space-y-4 p-6 rounded-xl bg-card">
// //           <div className="space-y-2">
// //             <label htmlFor="source" className="text-sm font-medium">
// //               Starting Point
// //             </label>
// //             <Input
// //               id="source"
// //               placeholder="Enter starting location"
// //               value={source}
// //               onChange={(e) => setSource(e.target.value)}
// //             />
// //           </div>

// //           <div className="space-y-2">
// //             <label htmlFor="destination" className="text-sm font-medium">
// //               Destination
// //             </label>
// //             <Input
// //               id="destination"
// //               placeholder="Enter destination"
// //               value={destination}
// //               onChange={(e) => setDestination(e.target.value)}
// //             />
// //           </div>

// //           <div className="flex gap-2">
// //             <Button onClick={handleSearch} className="flex-1 gap-2">
// //               <Search className="h-4 w-4" />
// //               Find Restaurants
// //             </Button>
// //             <Button 
// //               variant="outline" 
// //               onClick={() => {
// //                 if (!isLoggedIn) {
// //                   toast({
// //                     title: "Login Required",
// //                     description: "Please login to use the map feature",
// //                     variant: "destructive",
// //                   });
// //                   navigate('/auth');
// //                   return;
// //                 }
// //                 navigate('/map');
// //               }} 
// //               className="gap-2"
// //             >
// //               <Map className="h-4 w-4" />
// //               Find from Map
// //             </Button>
// //           </div>
// //         </div>
// //       </div>
// //     </MainLayout>
// //   );
// // };

// // export default Index;


// import { useState, useEffect } from 'react';
// import { Search, Map } from 'lucide-react';
// import { Button } from '@/components/ui/button';
// import { Input } from '@/components/ui/input';
// import MainLayout from '@/components/MainLayout';
// import { useNavigate, useLocation } from 'react-router-dom';
// import { useToast } from '@/hooks/use-toast';
// import YummiLogo from './a.png'; // Import the edited round logo
// import '../styles/glow.css'; // Import the custom CSS for the glowing effect

// const Index = () => {
//   const [source, setSource] = useState<string>('');
//   const [destination, setDestination] = useState<string>('');
//   const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
//   const [userName, setUserName] = useState<string>('');
//   const navigate = useNavigate();
//   const location = useLocation();
//   const { toast } = useToast();

//   // Check if user is coming from auth page with login status
//   useEffect(() => {
//     const loginStatus = localStorage.getItem('isLoggedIn');
//     const name = localStorage.getItem('userName');
    
//     if (loginStatus === 'true' && name) {
//       setIsLoggedIn(true);
//       setUserName(name);
//     }

//     // If coming from auth with state, update login status
//     if (location.state?.isLoggedIn) {
//       setIsLoggedIn(true);
//       const newUserName = location.state.userName || 'User';
//       setUserName(newUserName);
      
//       // Store in localStorage for persistence
//       localStorage.setItem('isLoggedIn', 'true');
//       localStorage.setItem('userName', newUserName);
//     }
//   }, [location]);

//   const handleSearch = () => {
//     if (!source || !destination) {
//       toast({
//         title: "Missing Information",
//         description: "Please enter both source and destination",
//         variant: "destructive",
//       });
//       return;
//     }

//     if (!isLoggedIn) {
//       toast({
//         title: "Login Required",
//         description: "Please login to search for restaurants",
//         variant: "destructive",
//       });
//       navigate('/auth');
//       return;
//     }

//     navigate('/restaurants');
//   };

//   const handleLogout = () => {
//     setIsLoggedIn(false);
//     setUserName('');
//     localStorage.removeItem('isLoggedIn');
//     localStorage.removeItem('userName');
//     toast({
//       title: "Logged Out",
//       description: "You have been successfully logged out",
//     });
//   };

//   return (
//     <MainLayout 
//       isLoggedIn={isLoggedIn} 
//       userName={userName} 
//       onLogout={handleLogout}
//     >
//       <div className="max-w-2xl mx-auto space-y-8">
//         <div className="flex flex-col items-center mb-8">
//           <div className="mb-8">
//             <img 
//               src={YummiLogo} 
//               alt="Yummi logo with a fork, knife, food illustration, and a smiling emoji" 
//               className="h-24 w-24 rounded-full glow-effect" 
//             />
//           </div>
//         </div>
      
//         <div className="text-center space-y-4">
//           <h1 className="text-4xl font-display font-bold">Find Your Perfect Meal</h1>
//           <p className="text-muted-foreground">
//             Discover restaurants along your route, optimized for both your taste and traffic conditions
//           </p>
//         </div>

//         <div className="space-y-4 p-6 rounded-xl bg-card">
//           <div className="space-y-2">
//             <label htmlFor="source" className="text-sm font-medium">
//               Starting Point
//             </label>
//             <Input
//               id="source"
//               placeholder="Enter starting location"
//               value={source}
//               onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSource(e.target.value)}
//             />
//           </div>

//           <div className="space-y-2">
//             <label htmlFor="destination" className="text-sm font-medium">
//               Destination
//             </label>
//             <Input
//               id="destination"
//               placeholder="Enter destination"
//               value={destination}
//               onChange={(e: React.ChangeEvent<HTMLInputElement>) => setDestination(e.target.value)}
//             />
//           </div>

//           <div className="flex gap-2">
//             <Button onClick={handleSearch} className="flex-1 gap-2">
//               <Search className="h-4 w-4" />
//               Find Restaurants
//             </Button>
//             <Button 
//               variant="outline" 
//               onClick={() => {
//                 if (!isLoggedIn) {
//                   toast({
//                     title: "Login Required",
//                     description: "Please login to use the map feature",
//                     variant: "destructive",
//                   });
//                   navigate('/auth');
//                   return;
//                 }
//                 navigate('/map');
//               }} 
//               className="gap-2"
//             >
//               <Map className="h-4 w-4" />
//               Find from Map
//             </Button>
//           </div>
//         </div>
//       </div>
//     </MainLayout>
//   );
// };

// export default Index;


import { useState, useEffect } from 'react';
import { Search, Map } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import MainLayout from '@/components/MainLayout';
import { useNavigate, useLocation } from 'react-router-dom';
import { useToast } from '@/hooks/use-toast';
import bLogo from '../assets/b.jpeg'; // Correct path
import '../styles/glow.css';

const Index = () => {
  const [source, setSource] = useState<string>('');
  const [destination, setDestination] = useState<string>('');
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [userName, setUserName] = useState<string>('');
  const navigate = useNavigate();
  const location = useLocation();
  const { toast } = useToast();

  useEffect(() => {
    const loginStatus = localStorage.getItem('isLoggedIn');
    const name = localStorage.getItem('userName');
    
    if (loginStatus === 'true' && name) {
      setIsLoggedIn(true);
      setUserName(name);
    }

    if (location.state?.isLoggedIn) {
      setIsLoggedIn(true);
      const newUserName = location.state.userName || 'User';
      setUserName(newUserName);
      
      localStorage.setItem('isLoggedIn', 'true');
      localStorage.setItem('userName', newUserName);
    }
  }, [location]);

  const handleSearch = () => {
    if (!source || !destination) {
      toast({
        title: "Missing Information",
        description: "Please enter both source and destination",
        variant: "destructive",
      });
      return;
    }

    if (!isLoggedIn) {
      toast({
        title: "Login Required",
        description: "Please login to search for restaurants",
        variant: "destructive",
      });
      navigate('/auth');
      return;
    }

    navigate('/restaurants');
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setUserName('');
    localStorage.removeItem('isLoggedIn');
    localStorage.removeItem('userName');
    toast({
      title: "Logged Out",
      description: "You have been successfully logged out",
    });
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
            <Button onClick={handleSearch} className="flex-1 gap-2">
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