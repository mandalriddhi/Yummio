
import React from 'react';
import { motion } from 'framer-motion';

const foodImages = [
  'https://images.unsplash.com/photo-1504674900247-0877df9cc836',
  'https://images.unsplash.com/photo-1498837167922-ddd27525d352',
  'https://images.unsplash.com/photo-1540189549336-e6e99c3679fe',
  'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38',
  'https://images.unsplash.com/photo-1565958011703-44f9829ba187',
  'https://images.unsplash.com/photo-1512621776951-a57141f2eefd',
];

interface FoodLoaderProps {
  message?: string;
}

const FoodLoader = ({ message = "Loading..." }: FoodLoaderProps) => {
  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex flex-col items-center justify-center gap-6">
      <div className="relative h-40 w-40">
        {foodImages.map((img, index) => (
          <motion.div
            key={index}
            className="absolute top-0 left-0 w-20 h-20"
            initial={{ 
              opacity: 0,
              x: -50, 
              y: -50,
              scale: 0.5
            }}
            animate={{ 
              opacity: [0, 1, 0],
              x: [
                -50 + Math.cos(index * (Math.PI / 3)) * 50,
                Math.cos((index + 1) * (Math.PI / 3)) * 50,
                Math.cos((index + 2) * (Math.PI / 3)) * 50
              ],
              y: [
                -50 + Math.sin(index * (Math.PI / 3)) * 50,
                Math.sin((index + 1) * (Math.PI / 3)) * 50,
                Math.sin((index + 2) * (Math.PI / 3)) * 50
              ],
              scale: [0.5, 1, 0.5],
              rotate: [0, 360]
            }}
            transition={{
              repeat: Infinity,
              repeatType: "loop",
              duration: 3,
              delay: index * 0.5,
              ease: "easeInOut",
            }}
            style={{
              zIndex: 10 - index
            }}
          >
            <img
              src={img}
              alt="Food"
              className="w-full h-full object-cover rounded-full shadow-lg"
            />
          </motion.div>
        ))}
        
        <motion.div 
          className="absolute -top-4 left-0 right-0 text-center text-xl font-medium text-primary"
          initial={{ opacity: 0, y: 10 }}
          animate={{ 
            opacity: [0, 1, 0],
            y: [10, 0, 10] 
          }}
          transition={{
            repeat: Infinity,
            duration: 2,
            ease: "easeInOut"
          }}
        >
          <span className="bg-background/70 px-4 py-1 rounded-full backdrop-blur-sm">
            {message}
          </span>
        </motion.div>
      </div>
      
      {/* Pulsing gradient circle under the animation */}
      <motion.div 
        className="absolute w-40 h-40 rounded-full"
        style={{
          background: 'radial-gradient(circle, rgba(249,115,22,0.3) 0%, rgba(217,70,239,0.3) 50%, rgba(155,135,245,0.2) 100%)',
        }}
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.2, 0.5, 0.2],
        }}
        transition={{
          repeat: Infinity,
          duration: 3,
          ease: "easeInOut"
        }}
      />
    </div>
  );
};

export default FoodLoader;
