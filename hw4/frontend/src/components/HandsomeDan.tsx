// Handsome Dan, Yale's bulldog mascot, drawn as an animated SVG (the site's "GIF").
// Poses: chomp (eating a Harvard pennant), cap (graduation cap), cheer (waving a Yale pennant), wag.

export type DanPose = 'chomp' | 'cap' | 'cheer' | 'wag'

const INK = '#1f2328'
const FAWN = '#c8925a'
const MUZZLE = '#f4efe9'

export default function HandsomeDan({ pose = 'wag', className = '' }: { pose?: DanPose; className?: string }) {
  return (
    <svg
      className={`dan dan-${pose} ${className}`}
      viewBox="0 0 260 240"
      role="img"
      aria-label={
        pose === 'chomp'
          ? 'Handsome Dan the bulldog chomping a Harvard pennant'
          : pose === 'cap'
            ? 'Handsome Dan the bulldog in a graduation cap'
            : pose === 'cheer'
              ? 'Handsome Dan the bulldog waving a Yale pennant'
              : 'Handsome Dan the bulldog wagging his tail'
      }
    >
      <g className="dan-body">
        {/* tail */}
        <path className="dan-tail" d="M196 178 q22 -6 20 -26" fill="none" stroke={INK} strokeWidth="9" strokeLinecap="round" />
        <path className="dan-tail" d="M196 178 q22 -6 20 -26" fill="none" stroke="#fff" strokeWidth="4" strokeLinecap="round" />
        {/* body */}
        <ellipse cx="130" cy="176" rx="74" ry="50" fill="#fff" stroke={INK} strokeWidth="4" />
        {/* Yale sweater */}
        <path d="M64 162 Q130 122 196 162 L192 206 Q130 222 68 206 Z" fill="#00356b" stroke={INK} strokeWidth="3" />
        <path d="M66 168 Q130 132 194 168" fill="none" stroke="#fff" strokeWidth="4" opacity="0.9" />
        <text x="130" y="200" textAnchor="middle" fontFamily="Georgia, serif" fontWeight="700" fontSize="34" fill="#fff">Y</text>
        {/* front legs and paws */}
        <rect x="92" y="196" width="26" height="34" rx="10" fill="#fff" stroke={INK} strokeWidth="4" />
        <rect x="142" y="196" width="26" height="34" rx="10" fill="#fff" stroke={INK} strokeWidth="4" />
        <path d="M100 230 v-7 M110 230 v-7 M150 230 v-7 M160 230 v-7" stroke={INK} strokeWidth="2.5" strokeLinecap="round" />
      </g>

      <g className="dan-head">
        {/* ears */}
        <path d="M78 58 Q52 36 58 80 Q68 70 82 74 Z" fill={FAWN} stroke={INK} strokeWidth="4" strokeLinejoin="round" />
        <path d="M182 58 Q208 36 202 80 Q192 70 178 74 Z" fill={FAWN} stroke={INK} strokeWidth="4" strokeLinejoin="round" />
        {/* head */}
        <ellipse cx="130" cy="98" rx="70" ry="57" fill="#fff" stroke={INK} strokeWidth="4" />
        <ellipse cx="100" cy="86" rx="24" ry="20" fill={FAWN} opacity="0.85" />
        {/* forehead wrinkles */}
        <path d="M112 64 Q130 57 148 64 M108 73 Q130 66 152 73" fill="none" stroke={INK} strokeWidth="2.5" strokeLinecap="round" />
        {/* eyes with sleepy bulldog lids */}
        <g className="dan-eyes">
          <circle cx="103" cy="90" r="8" fill={INK} />
          <circle cx="157" cy="90" r="8" fill={INK} />
          <circle cx="106" cy="87" r="2.6" fill="#fff" />
          <circle cx="160" cy="87" r="2.6" fill="#fff" />
        </g>
        <path d="M92 84 Q103 78 114 84 M146 84 Q157 78 168 84" fill="none" stroke={INK} strokeWidth="3" strokeLinecap="round" />
        {/* muzzle, nose, jowls */}
        <ellipse cx="130" cy="120" rx="44" ry="28" fill={MUZZLE} stroke={INK} strokeWidth="3" />
        <ellipse cx="130" cy="106" rx="17" ry="11" fill={INK} />
        <ellipse cx="124" cy="103" rx="5" ry="2.5" fill="#fff" opacity="0.6" />
        <path d="M130 117 v8 M96 128 Q113 141 130 130 Q147 141 164 128" fill="none" stroke={INK} strokeWidth="3" strokeLinecap="round" />
        {/* underbite jaw with two little teeth */}
        <g className="dan-jaw">
          <path d="M100 133 Q130 156 160 133 Q157 147 130 151 Q103 147 100 133 Z" fill="#d97b8a" stroke={INK} strokeWidth="3" strokeLinejoin="round" />
          <path d="M110 138 l4 -10 l4 10 Z M142 138 l4 -10 l4 10 Z" fill="#fff" stroke={INK} strokeWidth="1.5" strokeLinejoin="round" />
        </g>
        {pose === 'wag' && <ellipse className="dan-tongue" cx="134" cy="152" rx="9" ry="11" fill="#e8798b" stroke={INK} strokeWidth="2.5" />}

        {pose === 'cap' && (
          <g className="dan-cap">
            <path d="M84 52 Q130 36 176 52 L172 64 Q130 52 88 64 Z" fill="#14171c" stroke={INK} strokeWidth="2" />
            <path d="M60 40 L130 14 L200 40 L130 66 Z" fill="#1b1f25" stroke={INK} strokeWidth="3" strokeLinejoin="round" />
            <circle cx="130" cy="40" r="4" fill="#ffd55a" />
            <g className="dan-tassel">
              <path d="M130 40 Q170 44 182 58" fill="none" stroke="#ffd55a" strokeWidth="3" />
              <path d="M178 56 l4 18 l6 -16 Z" fill="#ffd55a" />
            </g>
          </g>
        )}
      </g>

      {pose === 'chomp' && (
        <g className="dan-pennant dan-pennant-harvard">
          <rect x="70" y="128" width="62" height="6" rx="3" fill="#7a5230" />
          <path d="M4 104 L74 126 L74 138 L4 160 Z" fill="#a51c30" stroke={INK} strokeWidth="3" strokeLinejoin="round" />
          <text x="34" y="140" textAnchor="middle" fontFamily="Georgia, serif" fontWeight="700" fontSize="24" fill="#fff">H</text>
          {/* torn-off bits flying */}
          <path className="dan-bit dan-bit-1" d="M6 150 l8 3 l-5 6 Z" fill="#a51c30" />
          <path className="dan-bit dan-bit-2" d="M10 110 l9 -2 l-3 8 Z" fill="#a51c30" />
          <path className="dan-bit dan-bit-3" d="M2 130 l7 4 l-7 4 Z" fill="#a51c30" />
        </g>
      )}

      {pose === 'cheer' && (
        <g className="dan-pennant dan-pennant-yale">
          <rect x="196" y="40" width="6" height="120" rx="3" fill="#7a5230" />
          <path d="M202 44 L258 64 L202 84 Z" fill="#00356b" stroke={INK} strokeWidth="3" strokeLinejoin="round" />
          <text x="222" y="70" textAnchor="middle" fontFamily="Georgia, serif" fontWeight="700" fontSize="13" fill="#fff">YALE</text>
          <ellipse cx="199" cy="160" rx="12" ry="9" fill="#fff" stroke={INK} strokeWidth="3" />
        </g>
      )}
    </svg>
  )
}
