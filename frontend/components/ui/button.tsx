import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-all duration-300 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default:
          "bg-[#d97757] text-[#f5f0e9] shadow-[0_8px_24px_rgba(217,119,87,0.25)] hover:bg-[#c66647] hover:shadow-[0_12px_32px_rgba(217,119,87,0.35)]",
        destructive:
          "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline:
          "border border-[rgba(217,119,87,0.35)] bg-transparent text-[#d97757] hover:bg-[rgba(217,119,87,0.08)] hover:border-[rgba(217,119,87,0.55)]",
        secondary:
          "bg-[#221c25] text-[#c4b8aa] hover:bg-[#2a2030]",
        ghost:
          "hover:bg-[rgba(245,240,233,0.06)] hover:text-[#f5f0e9]",
        link:
          "text-[#d97757] underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm:  "h-9 rounded-md px-3",
        lg:  "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
