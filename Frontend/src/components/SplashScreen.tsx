
import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

const foodImages = [
  'https://images.unsplash.com/photo-1504674900247-0877df9cc836',
  'https://images.unsplash.com/photo-1498837167922-ddd27525d352',
  'https://images.unsplash.com/photo-1540189549336-e6e99c3679fe',
  'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38',
];

const SplashScreen = ({ onComplete }: { onComplete: () => void }) => {
  const [show, setShow] = useState(true);
  const [typedText, setTypedText] = useState('');
  const [showO, setShowO] = useState(false);
  const [typingComplete, setTypingComplete] = useState(false);
  const welcomeText = "Welcome";
  const toText = "to";
  const yummiText = "Yummi";

  useEffect(() => {
    const fullText = welcomeText + " " + toText + " " + yummiText;
    let currentIndex = 0;
    
    // Start typing animation
    const typingInterval = setInterval(() => {
      if (currentIndex < fullText.length) {
        setTypedText(fullText.substring(0, currentIndex + 1));
        currentIndex++;
      } else {
        clearInterval(typingInterval);
        setTypingComplete(true);
        
        // Show the "o" after typing is complete
        setTimeout(() => {
          setShowO(true);
          
          // Complete the splash screen after all animations
          setTimeout(() => {
            setShow(false);
            onComplete();
          }, 1500);
        }, 300);
      }
    }, 100);

    return () => {
      clearInterval(typingInterval);
    };
  }, [onComplete]);

  if (!show) return null;

  return (
    <motion.div 
      className="fixed inset-0 bg-background z-50 flex items-center justify-center overflow-hidden"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <div className="relative w-full h-full">
        {foodImages.map((img, index) => (
          <motion.div
            key={index}
            className="absolute"
            style={{
              top: `${Math.random() * 70}%`,
              left: `${Math.random() * 70}%`,
              width: '200px',
              height: '200px',
            }}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 0.3, scale: 1 }}
            transition={{ delay: index * 0.2 }}
          >
            <img
              src={img}
              alt="Food"
              className="w-full h-full object-cover rounded-full blur-sm"
            />
          </motion.div>
        ))}
      </div>
      
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="flex flex-col items-center gap-2">
          {typedText.includes("Welcome") && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-6xl font-display font-bold"
            >
              {typedText.substring(0, Math.min(typedText.length, welcomeText.length))}
            </motion.div>
          )}
          
          {typedText.includes(" to") && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-6xl font-display font-bold"
            >
              {typedText.substring(welcomeText.length + 1, Math.min(typedText.length, welcomeText.length + 1 + toText.length))}
            </motion.div>
          )}
          
          {typedText.includes(" Yummi") && (
            <motion.div className="flex items-baseline">
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-6xl font-display font-bold"
              >
                {typedText.substring(welcomeText.length + 1 + toText.length + 1)}
              </motion.div>
              
              {showO && (
                <motion.span
                  className="text-6xl font-display font-bold"
                  initial={{ 
                    opacity: 0, 
                    y: -120,
                    rotate: 15,
                    scale: 1.5
                  }}
                  animate={{ 
                    opacity: 1, 
                    y: 0,
                    rotate: 0,
                    scale: 1
                  }}
                  transition={{ 
                    type: "spring",
                    stiffness: 300,
                    damping: 10,
                    mass: 0.8,
                    bounce: 0.7,
                  }}
                >
                  o
                </motion.span>
              )}
            </motion.div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default SplashScreen;
