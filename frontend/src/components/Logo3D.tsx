
import React, { useState, useRef, useEffect } from 'react';
import { motion, useAnimate } from 'framer-motion';

interface Logo3DProps {
  size?: 'small' | 'large';
  className?: string;
}

const Logo3D = ({ size = 'large', className = '' }: Logo3DProps) => {
  const [isFlipping, setIsFlipping] = useState(false);
  const [scope, animate] = useAnimate();
  const containerRef = useRef<HTMLDivElement>(null);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  const handleFlip = () => {
    if (size === 'large') {
      setIsFlipping(true);
      setTimeout(() => setIsFlipping(false), 1000);
    }
  };

  useEffect(() => {
    if (containerRef.current && size === 'large') {
      const handleMouseMove = (e: MouseEvent) => {
        if (!containerRef.current) return;
        
        const rect = containerRef.current.getBoundingClientRect();
        const x = e.clientX - rect.left - rect.width / 2;
        const y = e.clientY - rect.top - rect.height / 2;
        
        // Convert to degrees with limited rotation
        const xDeg = Math.max(Math.min(y / 10, 15), -15);
        const yDeg = Math.max(Math.min(-x / 10, 15), -15);
        
        setMousePosition({ x: xDeg, y: yDeg });
      };
      
      const handleMouseLeave = () => {
        animate(scope.current, 
          { rotateX: 0, rotateY: 0 }, 
          { duration: 0.5, ease: 'easeOut' }
        );
      };
      
      window.addEventListener('mousemove', handleMouseMove);
      containerRef.current.addEventListener('mouseleave', handleMouseLeave);
      
      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        if (containerRef.current) {
          containerRef.current.removeEventListener('mouseleave', handleMouseLeave);
        }
      };
    }
  }, [size, animate, scope]);

  useEffect(() => {
    if (size === 'large') {
      animate(scope.current, 
        { rotateX: mousePosition.x, rotateY: mousePosition.y }, 
        { duration: 0.2, ease: 'linear' }
      );
    }
  }, [mousePosition, size, animate, scope]);

  return (
    <motion.div 
      ref={containerRef}
      className={`relative flex items-center justify-center ${className}`}
      style={{
        width: size === 'large' ? '120px' : '30px',
        height: size === 'large' ? '120px' : '30px',
        perspective: '1000px',
        transformStyle: 'preserve-3d',
      }}
      whileHover={size === 'large' ? { scale: 1.05 } : {}}
      onClick={handleFlip}
    >
      <motion.div
        ref={scope}
        className="absolute w-full h-full rounded-full shadow-lg"
        style={{
          background: 'linear-gradient(135deg, #9b87f5 0%, #D946EF 50%, #F97316 100%)',
          boxShadow: size === 'large' 
            ? '0 10px 25px rgba(0, 0, 0, 0.2), inset 0 -5px 10px rgba(0, 0, 0, 0.1), inset 0 5px 10px rgba(255, 255, 255, 0.3)' 
            : '0 2px 5px rgba(0, 0, 0, 0.2)',
          transformStyle: 'preserve-3d',
        }}
        animate={{
          rotateY: isFlipping ? 360 : undefined,
        }}
        transition={{
          duration: 1,
          ease: 'easeInOut',
        }}
      >
        {/* Inner glossy highlight */}
        <div className="absolute inset-0 rounded-full bg-gradient-to-br from-white/30 to-transparent opacity-70 pointer-events-none"></div>
      </motion.div>
      
      <motion.div
        className="absolute flex items-center justify-center w-full h-full text-background font-bold"
        style={{
          fontSize: size === 'large' ? '3rem' : '1rem',
          filter: 'drop-shadow(0 2px 5px rgba(0,0,0,0.2))',
          textShadow: '0 2px 5px rgba(0,0,0,0.2)',
          transformStyle: 'preserve-3d',
          transform: 'translateZ(5px)',
        }}
        animate={{
          rotateY: isFlipping ? 360 : undefined,
        }}
        transition={{
          duration: 1,
          ease: 'easeInOut',
        }}
      >
        Y
      </motion.div>

      {size === 'large' && (
        <motion.div
          className="absolute -bottom-2 -right-2 w-8 h-8 rounded-full bg-accent z-10 flex items-center justify-center text-background font-bold text-lg"
          style={{
            background: 'linear-gradient(135deg, #F97316 0%, #D946EF 100%)',
            boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
          }}
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.3, type: 'spring' }}
        >
          o
        </motion.div>
      )}
    </motion.div>
  );
};

export default Logo3D;
