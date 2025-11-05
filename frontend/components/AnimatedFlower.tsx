'use client';

import { useEffect, useState } from 'react';

interface AnimatedFlowerProps {
  color?: string;
  size?: number;
  className?: string;
}

export function AnimatedFlower({ color = '#FFB3C1', size = 80, className = '' }: AnimatedFlowerProps) {
  const [rotation, setRotation] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setRotation((prev) => (prev + 0.5) % 360);
    }, 50);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className={`relative ${className}`} style={{ width: size, height: size }}>
      {/* Petals */}
      {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => (
        <div
          key={i}
          className="absolute top-1/2 left-1/2 origin-center"
          style={{
            transform: `translate(-50%, -50%) rotate(${i * 45 + rotation}deg) translateY(-${size * 0.3}px)`,
            transition: 'transform 0.05s linear',
          }}
        >
          <div
            className="rounded-full opacity-60 animate-pulse"
            style={{
              width: size * 0.3,
              height: size * 0.5,
              background: `radial-gradient(ellipse at center, ${color}dd, ${color}88)`,
              boxShadow: `0 0 ${size * 0.1}px ${color}66`,
            }}
          />
        </div>
      ))}

      {/* Center of flower */}
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full animate-pulse"
        style={{
          width: size * 0.25,
          height: size * 0.25,
          background: `radial-gradient(circle, #FFD4B2, #E8B4B8)`,
          boxShadow: '0 0 10px rgba(255, 212, 178, 0.6)',
        }}
      />
    </div>
  );
}

interface FloatingFlowerProps {
  initialX: number;
  initialY: number;
  color: string;
  delay?: number;
}

export function FloatingFlower({ initialX, initialY, color, delay = 0 }: FloatingFlowerProps) {
  return (
    <div
      className="absolute animate-float"
      style={{
        left: `${initialX}%`,
        top: `${initialY}%`,
        animationDelay: `${delay}s`,
      }}
    >
      <AnimatedFlower color={color} size={60} />
    </div>
  );
}
