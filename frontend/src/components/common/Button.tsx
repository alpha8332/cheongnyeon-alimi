import type { ButtonHTMLAttributes } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'gradient';
}

export default function Button({
  variant = 'primary',
  className = '',
  children,
  ...props
}: ButtonProps) {
  const variantClass =
    variant === 'gradient'
      ? 'btn-gradient'
      : variant === 'secondary'
        ? 'btn-secondary'
        : 'btn-primary';

  return (
    <button
      type="button"
      className={`btn ${variantClass} ${className}`.trim()}
      {...props}
    >
      {children}
    </button>
  );
}
