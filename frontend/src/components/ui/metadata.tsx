import type { ReactNode } from "react"
import { cn } from "../../lib/utils"

export function MetadataCard({ children, className }: { children: ReactNode, className?: string }) {
    return (
        <div className={cn("bg-white p-6 rounded-xl border border-neutral-200 shadow-sm space-y-4", className)}>
            {children}
        </div>
    )
}

export function MetadataHeader({ icon: Icon, title, children }: { icon?: any, title: string, children?: ReactNode }) {
    return (
        <div className="flex items-center justify-between border-b border-neutral-100 pb-2 mb-4">
            <h3 className="flex items-center gap-2 font-semibold text-neutral-900">
                {Icon && <Icon className="w-4 h-4 text-orange-600" />}
                {title}
            </h3>
            {children}
        </div>
    )
}

export function MetadataGrid({ children, className }: { children: ReactNode, className?: string }) {
    return (
        <div className={cn("space-y-4", className)}>
            {children}
        </div>
    )
}

export function MetadataField({ label, children, className }: { label: string | ReactNode, children: ReactNode, className?: string }) {
    return (
        <div className={cn("flex flex-col gap-1.5", className)}>
            <div className="text-[11px] font-bold text-neutral-400 uppercase tracking-wider flex items-center gap-2">
                {label}
            </div>
            {children}
        </div>
    )
}

export function MetadataValue({ children, className, mono = false }: { children: ReactNode, className?: string, mono?: boolean }) {
    return (
        <div className={cn("text-neutral-900 text-sm", mono && "font-mono text-[13px]", className)}>
            {children}
        </div>
    )
}
