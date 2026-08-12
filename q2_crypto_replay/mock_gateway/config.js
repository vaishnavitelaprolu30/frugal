module.exports = {
  MODE: process.env.GATEWAY_MODE || 'SECURE',
  PORT: 8082,
  SECRET_SALT: 'frugal_crypto_salt_2026_x99',
  SHARED_SECRET: 'super_secret_hmac_key_frugal_9921',
  MAX_CLOCK_SKEW_MICROS: 5 * 1000 * 1000 // 5 seconds in microseconds
};
