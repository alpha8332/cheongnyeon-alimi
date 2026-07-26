import { Link } from 'react-router-dom';

export default function Header() {
  return (
    <header>
      <nav>
        <Link to="/"><button type="button">홈</button></Link>
        <Link to="/programs"><button type="button">정책 목록</button></Link>
      </nav>
      <hr />
    </header>
  );
}