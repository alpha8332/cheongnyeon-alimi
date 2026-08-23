import { Navigate, useLocation } from 'react-router';

/**
 * Legacy `/search` route — preserves query string and lands on home search state.
 */
export default function PolicySearchRedirect() {
  const location = useLocation();

  return (
    <Navigate
      to={{
        pathname: '/',
        search: location.search,
      }}
      replace
    />
  );
}
