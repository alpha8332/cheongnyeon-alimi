import React from 'react';

interface CardProps {
  children: React.ReactNode;
}

export default function Card({ children }: CardProps) {
  return (
    <div style={{ border: '1px solid black', padding: '10px' }}>
      {children}
    </div>
  );
}