/* Robot avatar — inline SVG, faithful to the original's robot_svg in app.py */

export default function RobotAvatar({
  color,
  size = 62,
  working = false,
}: {
  color: string;
  size?: number;
  working?: boolean;
}) {
  return (
    <svg
      style={{ color }}
      className={working ? "robot-bob" : undefined}
      width={size}
      height={size}
      viewBox="0 0 64 64"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="robot avatar"
    >
      <line x1="32" y1="12" x2="32" y2="5" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <circle cx="32" cy="5" r="3.4" fill="currentColor" />
      <rect x="14" y="12" width="36" height="27" rx="10" fill="#0B1A1E" stroke="currentColor" strokeWidth="2" />
      <circle cx="24.5" cy="24" r="3.6" fill="currentColor" />
      <circle cx="39.5" cy="24" r="3.6" fill="currentColor" />
      <path d="M26 31 Q32 35.5 38 31" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" />
      <rect x="18" y="42" width="28" height="15" rx="7.5" fill="#0B1A1E" stroke="currentColor" strokeWidth="2" />
      <circle cx="32" cy="49.5" r="3.2" fill="currentColor" />
      <line x1="14" y1="48" x2="8" y2="44" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <line x1="50" y1="48" x2="56" y2="44" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}
