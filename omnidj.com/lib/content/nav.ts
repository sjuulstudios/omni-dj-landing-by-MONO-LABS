export type NavItem = {
  label: string;
  href: string;
  mega?: 'features' | 'solutions';
};

export const navItems: NavItem[] = [
  { label: 'Features', href: '/features', mega: 'features' },
  { label: 'Solutions', href: '/solutions', mega: 'solutions' },
  { label: 'Resources', href: '/resources' },
  { label: 'Pricing', href: '/pricing' },
  { label: 'For business', href: '/for-business' }
];

export const navAuth = {
  login: { label: 'Log in', href: '#' },
  signup: { label: 'Sign up', href: '#' }
};
