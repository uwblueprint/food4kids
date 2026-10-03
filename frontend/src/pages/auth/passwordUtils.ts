export const getPasswordRequirements = (password: string) => [
  {
    label: 'Be at least 8 characters (12+ recommended)',
    isSatisfied: password.length >= 8,
  },
  {
    label: 'Include at least 1 uppercase letter',
    isSatisfied: /[A-Z]/.test(password),
  },
  {
    label: 'Include at least 1 lowercase letter',
    isSatisfied: /[a-z]/.test(password),
  },
  {
    label: 'Include at least 1 number',
    isSatisfied: /\d/.test(password),
  },
  {
    label: 'Include at least 1 special character (e.g. ! @ # $ %)',
    isSatisfied: /[^A-Za-z0-9]/.test(password),
  },
];
