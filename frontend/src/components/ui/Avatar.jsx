/**
 * Reusable avatar component. Shows profile picture if available, otherwise initials.
 *
 * @param {object} props
 * @param {object} props.user - User object with optional profile_picture, first_name, username
 * @param {string} [props.size='md'] - 'xs' | 'sm' | 'md' | 'lg'
 * @param {string} [props.className] - Additional classes
 */
const sizes = {
  xs: 'w-6 h-6 text-[10px]',
  sm: 'w-7 h-7 text-[10px]',
  md: 'w-8 h-8 text-xs',
  lg: 'w-20 h-20 text-2xl',
};

export default function Avatar({ user, size = 'md', className = '' }) {
  const sizeClass = sizes[size] || sizes.md;
  const initial = (user?.first_name?.[0] || user?.username?.[0] || 'U').toUpperCase();
  const pic = user?.profile_picture;

  if (pic) {
    return (
      <img
        src={pic}
        alt=""
        className={`${sizeClass} rounded-full object-cover flex-shrink-0 ${className}`}
      />
    );
  }

  return (
    <div className={`${sizeClass} rounded-full bg-blue-600 flex items-center justify-center text-white font-semibold flex-shrink-0 ${className}`}>
      {initial}
    </div>
  );
}
