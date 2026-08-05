import { useState, type FormEvent } from 'react';
import './SearchBar.css';

interface SearchBarProps {
  initialQ: string;
  onSubmit: (q: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export default function SearchBar({
  initialQ,
  onSubmit,
  disabled = false,
  placeholder = '예: 서울 주거, 25세 일자리, 전국 청년',
}: SearchBarProps) {
  const [value, setValue] = useState(initialQ);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    onSubmit(value);
  };

  return (
    <form className="policy-search-bar" onSubmit={handleSubmit}>
      <div className="policy-search-bar__wrap">
        <span className="policy-search-bar__icon" aria-hidden="true">
          🔍
        </span>
        <input
          className="policy-search-bar__input"
          type="search"
          name="q"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          placeholder={placeholder}
          autoComplete="off"
          aria-label="정책 검색어"
          disabled={disabled}
        />
        <button
          className="policy-search-bar__submit"
          type="submit"
          disabled={disabled || !value.trim()}
        >
          검색
        </button>
      </div>
    </form>
  );
}
