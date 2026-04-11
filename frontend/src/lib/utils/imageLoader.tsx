import { useEffect, useRef, useState, type ImgHTMLAttributes } from "react";

export interface ImageWithLoaderProps extends Omit<
  ImgHTMLAttributes<HTMLImageElement>,
  "src"
> {
  src: string;
}

/**
 * Lazy-loads an image when it enters the viewport (IntersectionObserver).
 */
export function ImageWithLoader({
  src,
  alt,
  className,
  ...rest
}: ImageWithLoaderProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([e]) => {
        if (e?.isIntersecting) {
          setVisible(true);
          obs.disconnect();
        }
      },
      { rootMargin: "120px" },
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  return (
    <div ref={ref} className={`relative ${className ?? ""}`}>
      {!loaded && (
        <div
          className="absolute inset-0 animate-pulse bg-gray-200 rounded-[inherit]"
          aria-hidden
        />
      )}
      {visible && (
        <img
          src={src}
          alt={alt}
          className={className}
          onLoad={() => setLoaded(true)}
          loading="lazy"
          {...rest}
        />
      )}
    </div>
  );
}
