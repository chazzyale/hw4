import type { Collection } from '../api'

// Illustrations for the homepage sections. To use real photos (e.g. AI-generated images made elsewhere),
// drop files named residential-colleges / athletics / family (.jpg, .png, or .webp) into
// src/assets/sections/ and they are used automatically instead of the drawings.
const photos = import.meta.glob<string>('../assets/sections/*.{jpg,jpeg,png,webp}', { eager: true, import: 'default' })
const photoFor = (c: Collection) =>
  Object.entries(photos).find(([path]) => path.split('/').pop()?.startsWith(c))?.[1]

const ALT: Record<Collection, string> = {
  'residential-colleges': 'Students with residential college banners in a Gothic Yale courtyard at golden hour',
  athletics: 'Yale athletes celebrating a win under the lights at the Yale Bowl',
  family: 'A Yale graduate tossing a cap with family on Old Campus at Commencement',
}

export default function SectionArt({ collection }: { collection: Collection }) {
  const photo = photoFor(collection)
  return (
    <figure className={`section-art section-art-${collection}`}>
      {photo ? (
        <img src={photo} alt={ALT[collection]} />
      ) : collection === 'residential-colleges' ? (
        <Courtyard />
      ) : collection === 'athletics' ? (
        <Stadium />
      ) : (
        <Commencement />
      )}
    </figure>
  )
}

// A simple standing figure; arms up for celebrating.
function Person({ x, y, s = 1, color = '#1b2a44', arms = 'down', cap = false, gown = false }: {
  x: number; y: number; s?: number; color?: string; arms?: 'down' | 'up' | 'wave'; cap?: boolean; gown?: boolean
}) {
  const armL = arms === 'up' ? 'M-9 -44 L-22 -74' : arms === 'wave' ? 'M-9 -44 L-20 -30' : 'M-9 -44 L-14 -18'
  const armR = arms === 'down' ? 'M9 -44 L14 -18' : 'M9 -44 L22 -74'
  return (
    // Position lives on the outer group; the animation runs on the inner one so CSS doesn't override it.
    <g transform={`translate(${x} ${y}) scale(${s})`}>
      <g className={arms !== 'down' ? 'art-jump' : undefined} style={{ animationDelay: `${(x % 5) * 0.12}s` }}>
        <path d={`${armL} ${armR}`} stroke={color} strokeWidth="7" strokeLinecap="round" fill="none" />
        <path d="M-6 -14 L-8 0 M6 -14 L8 0" stroke={color} strokeWidth="8" strokeLinecap="round" />
        {gown ? (
          <path d="M-13 -48 Q0 -54 13 -48 L18 -6 Q0 -2 -18 -6 Z" fill={color} />
        ) : (
          <rect x="-11" y="-50" width="22" height="38" rx="9" fill={color} />
        )}
        <circle cx="0" cy="-61" r="9.5" fill={color} />
        {cap && <path d="M-13 -70 L0 -76 L13 -70 L0 -64 Z" fill="#111" />}
      </g>
    </g>
  )
}

function Courtyard() {
  return (
    <svg viewBox="0 0 400 500" preserveAspectRatio="xMidYMid slice" role="img" aria-label={ALT['residential-colleges']}>
      <defs>
        <linearGradient id="dusk" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#00356b" />
          <stop offset="0.55" stopColor="#286dc0" />
          <stop offset="1" stopColor="#f2c58c" />
        </linearGradient>
      </defs>
      <rect width="400" height="500" fill="url(#dusk)" />
      <circle cx="310" cy="300" r="46" fill="#ffd9a0" opacity="0.65" />
      {/* Harkness-style tower */}
      <g fill="#14233d">
        <rect x="170" y="110" width="60" height="260" />
        <rect x="178" y="70" width="44" height="50" />
        <path d="M184 70 L200 20 L216 70 Z" />
        <path d="M170 110 l6 -18 l6 18 M218 110 l6 -18 l6 18 M164 160 l6 -16 l6 16 M224 160 l6 -16 l6 16" />
      </g>
      <g fill="#ffd98a" opacity="0.85">
        <rect x="192" y="140" width="6" height="18" rx="3" />
        <rect x="203" y="140" width="6" height="18" rx="3" />
        <rect x="192" y="200" width="6" height="18" rx="3" />
        <rect x="203" y="200" width="6" height="18" rx="3" />
      </g>
      {/* Gothic college walls with arches and ivy */}
      <path d="M0 250 L0 400 L400 400 L400 250 L370 250 L370 236 L350 236 L350 250 L320 250 L320 236 L300 236 L300 250 L100 250 L100 236 L80 236 L80 250 L50 250 L50 236 L30 236 L30 250 Z" fill="#1e3354" />
      <g fill="#ffd98a" opacity="0.8">
        {[30, 70, 110, 290, 330, 370].map(x => (
          <path key={x} d={`M${x - 9} 320 L${x - 9} 290 Q${x} 274 ${x + 9} 290 L${x + 9} 320 Z`} />
        ))}
      </g>
      <g fill="#3f6b3a" opacity="0.95">
        <path d="M0 260 q20 10 10 40 q-6 30 12 60 L0 380 Z" />
        <path d="M400 262 q-24 14 -12 44 q8 26 -14 54 L400 380 Z" />
        <path d="M140 250 q14 18 -4 36 q-10 14 6 30 L120 316 L120 250 Z" />
        <path d="M262 250 q-12 22 6 40 q8 12 -4 26 L282 316 L282 250 Z" />
      </g>
      {/* lawn */}
      <path d="M0 392 Q200 370 400 392 L400 500 L0 500 Z" fill="#4c7a3f" />
      <path d="M0 430 Q200 410 400 430" stroke="#5f8f4e" strokeWidth="3" fill="none" />
      {/* students with college banners */}
      <g className="art-wave">
        <path d="M86 380 l0 -78 l34 10 l-34 12" fill="#5f712d" stroke="#14233d" strokeWidth="2" />
        <path d="M300 384 l0 -84 l-34 10 l34 12" fill="#bd5319" stroke="#14233d" strokeWidth="2" />
      </g>
      <Person x={86} y={452} s={1.05} color="#0f1d33" arms="wave" />
      <Person x={140} y={462} s={1.15} color="#1a2b47" />
      <Person x={250} y={458} s={1.1} color="#14233d" />
      <Person x={300} y={452} s={1.05} color="#0f1d33" arms="wave" />
      <Person x={200} y={470} s={1.2} color="#00356b" arms="up" />
    </svg>
  )
}

function Stadium() {
  const confetti = Array.from({ length: 26 }, (_, i) => ({
    x: (i * 53) % 400,
    y: (i * 37) % 260,
    c: i % 3 === 0 ? '#ffffff' : i % 3 === 1 ? '#63aaff' : '#286dc0',
    d: (i % 7) * 0.35,
  }))
  return (
    <svg viewBox="0 0 400 500" preserveAspectRatio="xMidYMid slice" role="img" aria-label={ALT.athletics}>
      <rect width="400" height="500" fill="#06142b" />
      {/* stadium lights and beams */}
      {[60, 340].map(x => (
        <g key={x}>
          <path className="art-beam" d={`M${x - 26} 40 L${x - 120} 330 L${x + 120} 330 L${x + 26} 40 Z`} fill="#bcd8ff" opacity="0.1" />
          <rect x={x - 26} y="24" width="52" height="22" rx="4" fill="#dfeeff" />
          <rect x={x - 3} y="46" width="6" height="150" fill="#33425c" />
        </g>
      ))}
      {/* crowd in the stands (Yale Bowl rows) */}
      <path d="M0 200 Q200 150 400 200 L400 300 L0 300 Z" fill="#11264a" />
      {Array.from({ length: 4 }, (_, row) =>
        Array.from({ length: 22 }, (_, i) => (
          <circle
            key={`${row}-${i}`}
            cx={10 + i * 18 + (row % 2) * 9}
            cy={206 + row * 22 - Math.sin((i / 21) * Math.PI) * 24}
            r="6"
            fill={(i + row) % 4 === 0 ? '#ffffff' : (i + row) % 3 === 0 ? '#63aaff' : '#286dc0'}
            opacity="0.8"
          />
        )),
      )}
      {/* field */}
      <path d="M0 300 L400 300 L400 500 L0 500 Z" fill="#2f6b34" />
      {[330, 370, 420, 480].map(y => (
        <line key={y} x1="0" x2="400" y1={y} y2={y} stroke="#fff" strokeOpacity="0.35" strokeWidth="2" />
      ))}
      <text x="200" y="404" textAnchor="middle" fontFamily="Georgia, serif" fontWeight="700" fontSize="40" fill="#fff" opacity="0.25">YALE</text>
      {/* scoreboard */}
      <g>
        <rect x="140" y="70" width="120" height="56" rx="6" fill="#0b1f3f" stroke="#63aaff" strokeWidth="2" />
        <text x="200" y="92" textAnchor="middle" fontFamily="Georgia, serif" fontSize="14" fill="#cfe3ff">FINAL</text>
        <text x="200" y="116" textAnchor="middle" fontFamily="Georgia, serif" fontWeight="700" fontSize="20" fill="#fff">YALE WINS!</text>
      </g>
      {/* celebrating athletes */}
      <Person x={110} y={470} s={1.3} color="#00356b" arms="up" />
      <Person x={180} y={476} s={1.4} color="#ffffff" arms="up" />
      <Person x={250} y={472} s={1.3} color="#00356b" arms="up" />
      <Person x={320} y={466} s={1.2} color="#ffffff" arms="wave" />
      <Person x={50} y={462} s={1.15} color="#ffffff" arms="wave" />
      {/* confetti */}
      {confetti.map((p, i) => (
        <rect key={i} className="art-confetti" x={p.x} y={p.y} width="6" height="10" rx="1" fill={p.c}
          style={{ animationDelay: `${p.d}s` }} />
      ))}
    </svg>
  )
}

function Commencement() {
  return (
    <svg viewBox="0 0 400 500" preserveAspectRatio="xMidYMid slice" role="img" aria-label={ALT.family}>
      <defs>
        <linearGradient id="noon" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#63aaff" />
          <stop offset="1" stopColor="#dcebff" />
        </linearGradient>
      </defs>
      <rect width="400" height="500" fill="url(#noon)" />
      <circle cx="320" cy="80" r="34" fill="#fff4cf" />
      {/* Old Campus building with banners */}
      <rect x="20" y="150" width="360" height="200" fill="#c9b79c" />
      <path d="M20 150 L200 96 L380 150 Z" fill="#a8957a" />
      <rect x="170" y="230" width="60" height="120" rx="30" fill="#5b4a37" />
      {[60, 110, 290, 340].map(x => (
        <rect key={x} x={x - 12} y="190" width="24" height="40" rx="12" fill="#e9dfcf" />
      ))}
      <g className="art-wave">
        <path d="M86 160 L86 230 L100 220 L114 230 L114 160 Z" fill="#00356b" />
        <path d="M286 160 L286 230 L300 220 L314 230 L314 160 Z" fill="#00356b" />
        <text x="100" y="200" textAnchor="middle" fontFamily="Georgia, serif" fontWeight="700" fontSize="18" fill="#fff">Y</text>
        <text x="300" y="200" textAnchor="middle" fontFamily="Georgia, serif" fontWeight="700" fontSize="18" fill="#fff">Y</text>
      </g>
      {/* elm tree */}
      <rect x="352" y="250" width="12" height="110" fill="#5b4a37" />
      <circle cx="358" cy="236" r="44" fill="#4c7a3f" />
      <circle cx="330" cy="260" r="28" fill="#5f8f4e" />
      {/* lawn */}
      <path d="M0 346 Q200 330 400 346 L400 500 L0 500 Z" fill="#5f8f4e" />
      {/* tossed cap */}
      <g className="art-toss">
        <path d="M184 120 L200 112 L216 120 L200 128 Z" fill="#111" />
        <path d="M200 120 q8 6 6 16" stroke="#ffd55a" strokeWidth="2" fill="none" />
      </g>
      {/* family: grandparent, parents, graduate, sibling */}
      <Person x={70} y={466} s={1.1} color="#5c6b80" />
      <Person x={130} y={472} s={1.25} color="#2c3e5c" arms="wave" />
      <Person x={200} y={470} s={1.35} color="#00356b" arms="up" gown />
      <Person x={268} y={474} s={1.25} color="#3d506e" arms="wave" />
      <Person x={326} y={480} s={0.9} color="#286dc0" arms="up" />
    </svg>
  )
}
