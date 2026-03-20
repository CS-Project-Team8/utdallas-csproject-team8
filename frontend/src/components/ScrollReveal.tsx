"use client";
import { useEffect, useRef, useState, type ReactNode } from "react";

interface ScrollRevealProps {
  children: ReactNode;
  className?: string;
  animation?: "fade-up" | "slide-left" | "slide-right" | "fade-in";
  delay?: number;
}

export const ScrollReveal = ({
  children,
  className = "",
  animation = "fade-up",
  delay = 0,
}: ScrollRevealProps) => {
  const ref = useRef<HTMLDivElement>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.unobserve(entry.target);
        }
      },
      { threshold: 0.15 }
    );

    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  const animationClass = {
    "fade-up": "animate-fade-up",
    "slide-left": "animate-slide-left",
    "slide-right": "animate-slide-right",
    "fade-in": "animate-fade-in",
  }[animation];

  return (
    <div
      ref={ref}
      className={`${className} ${isVisible ? animationClass : "opacity-0"}`}
      style={{ animationDelay: isVisible ? `${delay}ms` : undefined }}
    >
      {children}
    </div>
  );
};
