import { describe, it, expect } from 'vitest';

// Simple utility functions to test
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(amount);
};

const validateEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

describe('Utility Functions', () => {
  describe('formatCurrency', () => {
    it('formats currency correctly', () => {
      expect(formatCurrency(1000)).toBe('$1,000.00');
      expect(formatCurrency(1234.56)).toBe('$1,234.56');
      expect(formatCurrency(0)).toBe('$0.00');
    });
  });

  describe('validateEmail', () => {
    it('validates email addresses correctly', () => {
      expect(validateEmail('test@example.com')).toBe(true);
      expect(validateEmail('user@compliantguard.com')).toBe(true);
      expect(validateEmail('invalid.email')).toBe(false);
      expect(validateEmail('missing@domain')).toBe(false);
      expect(validateEmail('')).toBe(false);
    });
  });
});

describe('Environment Setup', () => {
  it('has the correct test environment variables', () => {
    expect(import.meta.env.VITE_APP_ENV).toBe('test');
    expect(import.meta.env.VITE_API_URL).toBe('https://test-api.example.com');
  });
});