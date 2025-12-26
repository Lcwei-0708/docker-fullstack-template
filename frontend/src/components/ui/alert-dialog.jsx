import * as React from "react"
import * as AlertDialogPrimitive from "@radix-ui/react-alert-dialog"

import { cn } from "@/lib/utils"
import { Button, buttonVariants } from "@/components/ui/button"
import { useIsMobile } from "@/hooks/useMobile"

function AlertDialog({
  ...props
}) {
  return <AlertDialogPrimitive.Root data-slot="alert-dialog" {...props} />;
}

function AlertDialogTrigger({
  ...props
}) {
  return (<AlertDialogPrimitive.Trigger data-slot="alert-dialog-trigger" {...props} />);
}

function AlertDialogPortal({
  ...props
}) {
  return (<AlertDialogPrimitive.Portal data-slot="alert-dialog-portal" {...props} />);
}

function AlertDialogOverlay({
  className,
  ...props
}) {
  return (
    (<AlertDialogPrimitive.Overlay
      data-slot="alert-dialog-overlay"
      className={cn(
        "data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:duration-200 data-[state=open]:duration-200 fixed inset-0 z-50 bg-neutral-800/50 backdrop-blur-sm transition-opacity duration-200",
        className
      )}
      {...props} />)
  );
}

function AlertDialogContent({
  className,
  ...props
}) {
  return (
    (<AlertDialogPortal>
      <AlertDialogOverlay />
      <AlertDialogPrimitive.Content
        data-slot="alert-dialog-content"
        className={cn(
          "bg-background data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:duration-200 data-[state=open]:duration-200 fixed top-[50%] left-[50%] z-50 grid w-full max-w-[calc(100%-2rem)] translate-x-[-50%] translate-y-[-50%] gap-4 rounded-lg border p-6 shadow-lg sm:max-w-lg",
          className
        )}
        {...props} />
    </AlertDialogPortal>)
  );
}

function AlertDialogHeader({
  className,
  ...props
}) {
  const isMobile = useIsMobile();

  return (
    (<div
      data-slot="alert-dialog-header"
      className={cn("flex flex-col text-center sm:text-left", isMobile ? "gap-4" : "gap-2", className)}
      {...props} />)
  );
}

function AlertDialogFooter({
  className,
  ...props
}) {
  const isMobile = useIsMobile();
  
  return (
    (<div
      data-slot="alert-dialog-footer"
      className={cn(
        "flex flex-row",
        isMobile 
          ? "justify-between gap-4 [&>*]:flex-1 w-full mt-3" 
          : "justify-end gap-2",
        className
      )}
      {...props} />)
  );
}

function AlertDialogTitle({
  className,
  ...props
}) {
  return (
    (<AlertDialogPrimitive.Title
      data-slot="alert-dialog-title"
      className={cn("text-lg font-semibold", className)}
      {...props} />)
  );
}

function AlertDialogDescription({
  className,
  ...props
}) {
  return (
    (<AlertDialogPrimitive.Description
      data-slot="alert-dialog-description"
      className={cn("text-muted-foreground text-sm", className)}
      {...props} />)
  );
}

function AlertDialogAction({
  className,
  ...props
}) {
  return (
    <AlertDialogPrimitive.Action asChild>
      <Button 
        className={cn("", className)} 
        {...props} 
      />
    </AlertDialogPrimitive.Action>
  );
}

function AlertDialogCancel({
  className,
  ...props
}) {
  return (
    <AlertDialogPrimitive.Cancel asChild>
      <Button 
        variant="outline"
        className={cn("", className)} 
        {...props} 
      />
    </AlertDialogPrimitive.Cancel>
  );
}

export {
  AlertDialog,
  AlertDialogPortal,
  AlertDialogOverlay,
  AlertDialogTrigger,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogFooter,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogAction,
  AlertDialogCancel,
}