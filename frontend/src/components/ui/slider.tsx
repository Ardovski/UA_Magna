"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export interface SliderProps {
  value: number;
  min: number;
  max: number;
  step?: number;
  /**
   * Sürükleme/tuş değişiminde her frame çağrılır (anlık görsel feedback için
   * local state). Yalnızca bu çağrılırsa üst component her pixel'de store günceller
   * ve yoğun network trafiği oluşur — mümkünse `onCommit` ile birlikte kullan.
   */
  onChange: (v: number) => void;
  /**
   * Kullanıcı sürdürmeyi bıraktığında (mouseup/touchend/keyup) çağrılır.
   * Store/API çağrıları burada tetiklenmeli. shadcn/Radix `onValueCommit`
   * semantiğiyle uyumlu.
   */
  onCommit?: (v: number) => void;
  className?: string;
  disabled?: boolean;
  ariaLabel?: string;
}

export function Slider({
  value,
  min,
  max,
  step = 1,
  onChange,
  onCommit,
  className,
  disabled,
  ariaLabel,
}: SliderProps) {
  // onChange'i ref ile sar — prop değişse bile DOM event listener'ı stable kalsın.
  const onChangeRef = React.useRef(onChange);
  const onCommitRef = React.useRef(onCommit);
  React.useEffect(() => {
    onChangeRef.current = onChange;
    onCommitRef.current = onCommit;
  }, [onChange, onCommit]);

  return (
    <input
      type="range"
      value={value}
      min={min}
      max={max}
      step={step}
      disabled={disabled}
      aria-label={ariaLabel}
      onChange={(e) => onChangeRef.current(Number(e.target.value))}
      onMouseUp={(e) =>
        onCommitRef.current?.(Number((e.target as HTMLInputElement).value))
      }
      onTouchEnd={(e) =>
        onCommitRef.current?.(Number((e.target as HTMLInputElement).value))
      }
      onKeyUp={(e) =>
        onCommitRef.current?.(Number((e.target as HTMLInputElement).value))
      }
      className={cn(
        "h-2 w-full cursor-pointer appearance-none rounded-md bg-muted accent-primary disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
    />
  );
}
