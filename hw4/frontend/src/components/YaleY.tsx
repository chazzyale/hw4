// Yale athletics block "Y", traced from the official logo. The logo is a solid Y with a
// thin gap ring and an outer ring, drawn here as one outline stroked in layers so the
// colors can be adapted to the dark-blue banner.
const Y_OUTLINE =
  '540,113 878,113 878,233 790,233 1000,558 1211,233 1119,233 1119,113 1458,113 1458,233 ' +
  '1363,233 1097,633 1097,877 1245,877 1245,1012 753,1012 753,877 902,877 902,633 635,233 540,233'

type Props = {
  className?: string
  /** Fill of the letter and the outer ring. */
  color?: string
  /** Color of the thin ring between them (normally the background). */
  gapColor?: string
}

export default function YaleY({ className, color = '#00356b', gapColor = '#ffffff' }: Props) {
  return (
    <svg className={className} viewBox="490 63 1018 1000" role="img" aria-label="Yale Y logo">
      <polygon points={Y_OUTLINE} fill={color} stroke={color} strokeWidth="94" strokeLinejoin="miter" />
      <polygon points={Y_OUTLINE} fill={color} stroke={gapColor} strokeWidth="44" strokeLinejoin="miter" />
      <polygon points={Y_OUTLINE} fill={color} />
    </svg>
  )
}
