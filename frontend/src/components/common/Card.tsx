import type { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  compact?: boolean;
  title?: string;
}

export default function Card({ children, compact = false, title }: CardProps) {
  return (
    <div className={`panel${compact ? ' panel--compact' : ''}`}>
      {title ? <h3 className="panel-title">{title}</h3> : null}
      {children}
    </div>
  );
}
