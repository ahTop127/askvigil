import { useRef, useEffect, useState } from "react";
import { Star } from "lucide-react";

interface EyeFollowMouseProps {
  mousePosition: { x: number; y: number };
}

export function EyeFollowMouse({ mousePosition }: EyeFollowMouseProps) {
  const eyeRef = useRef<HTMLDivElement>(null);
  const [pupilPosition, setPupilPosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    if (!eyeRef.current) return;

    const eyeRect = eyeRef.current.getBoundingClientRect();
    const eyeCenterX = eyeRect.left + eyeRect.width / 2;
    const eyeCenterY = eyeRect.top + eyeRect.height / 2;

    // Calculate angle and distance from eye center to mouse
    const deltaX = mousePosition.x - eyeCenterX;
    const deltaY = mousePosition.y - eyeCenterY;
    const angle = Math.atan2(deltaY, deltaX);

    // Limit pupil movement within the eye (max distance from center)
    const maxDistance = 25;
    const distance = Math.min(
      Math.sqrt(deltaX * deltaX + deltaY * deltaY) / 15,
      maxDistance,
    );

    const pupilX = Math.cos(angle) * distance;
    const pupilY = Math.sin(angle) * distance;

    setPupilPosition({ x: pupilX, y: pupilY });
  }, [mousePosition]);

  return (
    <div className="relative animate-bounce-slow">
      {/* Eye Container */}

      {/* Decorative stars */}
    </div>
  );
}
