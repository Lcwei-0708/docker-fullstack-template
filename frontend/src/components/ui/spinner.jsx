import { Loader } from "@/components/animate-ui/icons/loader"
import { AnimateIcon } from "@/components/animate-ui/icons/icon"
import { cn } from "@/lib/utils"

function Spinner({
  className,
  animation = "default",
  ...props
}) {
  return (
    <AnimateIcon animate loop>
      <Loader
        role="status"
        aria-label="Loading"
        animation={animation}
        className={cn("size-4", className)}
        {...props} />
    </AnimateIcon>
  );
}

export { Spinner }
