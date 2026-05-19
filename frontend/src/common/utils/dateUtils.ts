export const formatDisplayDate = (date: Date): string =>
  date.toLocaleDateString('en-US', { month: 'long', day: 'numeric' });
