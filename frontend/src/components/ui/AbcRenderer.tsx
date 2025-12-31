import { useEffect, useRef } from 'react';
import abcjs from 'abcjs';

interface AbcRendererProps {
    notation: string;
    className?: string;
}

export function AbcRenderer({ notation, className }: AbcRendererProps) {
    const divRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (divRef.current && notation) {
            try {
                abcjs.renderAbc(divRef.current, notation, { responsive: "resize" });
            } catch (e) {
                console.error("Failed to render ABC notation:", e);
                divRef.current.innerHTML = `<span class="text-red-500 text-xs">Error rendering ABC</span>`;
            }
        }
    }, [notation]);

    return <div ref={divRef} className={className} />;
}
