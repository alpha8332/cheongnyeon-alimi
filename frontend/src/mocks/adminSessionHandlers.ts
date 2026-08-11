import type {
  AdminSessionRequest,
  AdminSessionResponse,
  AdminSessionErrorStatus,
} from '../types/adminSession.js';

export type AdminSessionMockResult =
  | { status: 200; body: AdminSessionResponse }
  | { status: AdminSessionErrorStatus; body: { message: string } };

const MOCK_ACCESS_TOKEN = 'mock-admin-access-token';
const MOCK_EXPIRES_IN = 900;

export function handleAdminSessionMock(
  request: AdminSessionRequest,
): AdminSessionMockResult {
  const pin = request.pin.trim();

  if (!/^\d{4}$/.test(pin)) {
    return {
      status: 422,
      body: { message: 'PIN must be exactly four numeric digits.' },
    };
  }

  if (pin === '4290') {
    return {
      status: 429,
      body: {
        message:
          'Too many failed login attempts. Account temporarily locked for 5 seconds.',
      },
    };
  }

  if (pin === '0000') {
    return {
      status: 200,
      body: {
        access_token: MOCK_ACCESS_TOKEN,
        token_type: 'bearer',
        expires_in: MOCK_EXPIRES_IN,
        role: 'admin',
      },
    };
  }

  return {
    status: 401,
    body: { message: 'Invalid admin PIN or authentication disabled.' },
  };
}

/** Mock-only helper for contract tests — never log or persist. */
export function getMockAdminAccessToken(): string {
  return MOCK_ACCESS_TOKEN;
}
