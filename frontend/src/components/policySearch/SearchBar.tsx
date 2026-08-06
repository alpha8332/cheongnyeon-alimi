import { useState, type FormEvent } from 'react';
import './PolicySearchShell.css';

interface SearchBarProps {
  defaultQ: string;
  onSubmit: (q: string) => void;
  onClear?: () => void;
  isSubmitting?: boolean;
  placeholder?: string;
}

export default function SearchBar({
  defaultQ,
  onSubmit,
  onClear,
  isSubmitting = false,
  placeholder = '예: 천안 사는 24세 청년 지원금',
}: SearchBarProps) {
  const [value, setValue] = useState(defaultQ);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    onSubmit(value);
  };

  const handleClear = () => {
    setValue('');
    onClear?.();
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="search-wrap">
        <span className="search-wrap__icon" aria-hidden="true">
          🔍
        </span>
        <input
          className="search-wrap__input"
          type="search"
          name="q"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          placeholder={placeholder}
          autoComplete="off"
          aria-label="정책 검색어"
        />
        {value ? (
          <button
            className="search-wrap__clear"
            type="button"
            aria-label="검색어 지우기"
            onClick={handleClear}
          >
            ✕
          </button>
        ) : null}
        <button
          className="btn btn-primary"
          type="submit"
          disabled={isSubmitting || !value.trim()}
        >
          검색하기
        </button>
      </div>
    </form>
  );
}
