export const getPasswordRequirements = (password: string) => [
  {
    label: '8+ characters (12 or more is recommended)',
    isSatisfied: password.length >= 8,
  },
  {
    label: 'One uppercase and one lowercase letter',
    isSatisfied: /[a-z]/.test(password) && /[A-Z]/.test(password),
  },
  {
    label: 'One number',
    isSatisfied: /\d/.test(password),
  },
  {
    label: 'One special character (e.g. ! @ # $ %)',
    isSatisfied: /[^A-Za-z0-9]/.test(password),
  },
];
