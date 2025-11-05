import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface CardProps {
  children: ReactNode;
  className?: string;
  variant?: 'default' | 'rose' | 'lavender' | 'sage' | 'peach';
}

export function Card({ children, className, variant = 'default' }: CardProps) {
  const variants = {
    default: 'bg-white/80 border-rose/20',
    rose: 'bg-gradient-to-br from-soft-pink/60 to-rose/30 border-rose/30',
    lavender: 'bg-gradient-to-br from-lavender/40 to-powder-blue/30 border-lavender/30',
    sage: 'bg-gradient-to-br from-mint/40 to-sage/30 border-sage/30',
    peach: 'bg-gradient-to-br from-peach/40 to-dusty-rose/30 border-dusty-rose/30',
  };

  return (
    <div
      className={cn(
        'backdrop-blur-sm border-2 rounded-2xl p-6 shadow-lg transition-all duration-300 hover:shadow-xl hover:scale-[1.02]',
        variants[variant],
        className
      )}
    >
      {children}
    </div>
  );
}
