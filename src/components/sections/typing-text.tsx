"use client";

import { useEffect, useState } from "react";

export function TypingText({
  text,
  speed = 28,
}: {
  text: string;
  speed?: number;
}) {
  const [displayed, setDisplayed] = useState("");

  useEffect(() => {
    let index = 0;
    setDisplayed("");
    const id = window.setInterval(() => {
      index += 1;
      setDisplayed(text.slice(0, index));
      if (index >= text.length) window.clearInterval(id);
    }, speed);
    return () => window.clearInterval(id);
  }, [text, speed]);

  return (
    <span aria-label={text}>
      {displayed}
      <span className="ml-0.5 inline-block h-5 w-[2px] translate-y-0.5 animate-pulse bg-brand" />
    </span>
  );
}
