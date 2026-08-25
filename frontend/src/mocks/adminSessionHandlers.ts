import type {
  AdminSessionRequest,
  AdminSessionResponse,
  AdminSessionErrorStatus,
  AdminPinChangeRequest,
} from '../types/adminSession.js';

export type AdminSessionMockResult =
  | { status: 200; body: AdminSessionResponse }
  | { status: AdminSessionErrorStatus; body: { message: string } };

const MOCK_ACCESS_TOKEN = 'mock-admin-access-token';
const MOCK_EXPIRES_IN = 900;
let mockAdminPin = '0000';

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

  if (pin === '5000') {
    return {
      status: 503,
      body: {
        message: 'Admin session service unavailable.',
      },
    };
  }

  if (pin === mockAdminPin) {
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

export type AdminPinChangeMockResult =
  | { status: 204 }
  | { status: 401 | 409 | 422; body: { message: string } };

export function handleAdminPinChangeMock(
  request: AdminPinChangeRequest,
): AdminPinChangeMockResult {
  const currentPin = request.current_pin.trim();
  const newPin = request.new_pin.trim();
  if (!/^\d{4}$/.test(currentPin) || !/^\d{4}$/.test(newPin)) {
    return { status: 422, body: { message: 'PIN must be exactly four numeric digits.' } };
  }
  if (currentPin !== mockAdminPin) {
    return { status: 401, body: { message: 'Current admin PIN is invalid.' } };
  }
  if (newPin === mockAdminPin) {
    return {
      status: 409,
      body: { message: 'New admin PIN must differ from the current PIN.' },
    };
  }

  mockAdminPin = newPin;
  return { status: 204 };
}

/** Contract-test helper. */
export function resetMockAdminPin(): void {
  mockAdminPin = '0000';
}

/** Mock-only helper for contract tests — never log or persist. */
export function getMockAdminAccessToken(): string {
  return MOCK_ACCESS_TOKEN;
}
