import { type HTMLAttributes } from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "../../lib/utils"

const badgeVariants = cva(
  [
    "inline-flex items-center rounded-full border px-2.5 py-0.5",
    "text-xs font-semibold transition-colors",
    "focus:outline-2 focus:outline-offset-2 focus:outline-ring",
  ].join(" "),
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground",
        secondary: "border-transparent bg-secondary text-secondary-foreground",
        destructive: "border-transparent bg-destructive text-destructive-foreground",
        outline: "text-foreground",
        sunni: "border-transparent bg-sunni-bg text-sunni",
        shia: "border-transparent bg-shia-bg text-shia",
        sahih: "border-transparent bg-sahih-bg text-sahih",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
)

interface BadgeProps
  extends HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
export type { BadgeProps }
