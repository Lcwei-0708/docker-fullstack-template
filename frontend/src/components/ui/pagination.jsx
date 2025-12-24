import * as React from "react"
import { useTranslation } from 'react-i18next';
import {
  ChevronLeftIcon,
  ChevronRightIcon,
  MoreHorizontalIcon,
} from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button";

function Pagination({
  className,
  ...props
}) {
  return (
    <nav
      role="navigation"
      aria-label="pagination"
      data-slot="pagination"
      className={cn("mx-auto flex w-full justify-center", className)}
      {...props} />
  );
}

function PaginationContent({
  className,
  ...props
}) {
  return (
    <ul
      data-slot="pagination-content"
      className={cn("flex flex-row items-center justify-center gap-1", className)}
      {...props} />
  );
}

function PaginationItem({
  ...props
}) {
  return <li data-slot="pagination-item" {...props} />;
}

function PaginationLink({
  className,
  isActive,
  size = "icon",
  asChild = false,
  onClick,
  ...props
}) {
  return (
    <Button
      asChild={asChild}
      aria-current={isActive ? "page" : undefined}
      data-slot="pagination-link"
      data-active={isActive}
      variant={isActive ? "default" : "ghost"}
      size={size}
      onClick={isActive ? undefined : onClick}
      className={cn(
        "flex items-center justify-center",
        isActive && "pointer-events-none",
        className
      )}
      {...props} />
  );
}

function PaginationPrevious({
  className,
  ...props
}) {
  const { t } = useTranslation();
  return (
    <PaginationLink
      aria-label={t('components.pagination.previousPage')}
      size="default"
      className={cn("gap-1 px-2 rounded-sm font-normal", className)}
      {...props}>
      <ChevronLeftIcon className="shrink-0 size-5" />
      <span className="hidden sm:inline">{t('components.pagination.previous')}</span>
    </PaginationLink>
  );
}

function PaginationNext({
  className,
  ...props
}) {
  const { t } = useTranslation();
  return (
    <PaginationLink
      aria-label={t('components.pagination.nextPage')}
      size="default"
      className={cn("gap-1 px-2 rounded-sm font-normal", className)}
      {...props}>
      <span className="hidden sm:inline">{t('components.pagination.next')}</span>
      <ChevronRightIcon className="shrink-0 size-5" />
    </PaginationLink>
  );
}

function PaginationEllipsis({
  className,
  ...props
}) {
  const { t } = useTranslation();
  return (
    <span
      aria-hidden
      data-slot="pagination-ellipsis"
      className={cn("flex size-9 items-center justify-center", className)}
      {...props}>
      <MoreHorizontalIcon className="size-4" />
      <span className="sr-only">{t('components.pagination.morePages')}</span>
    </span>
  );
}

export {
  Pagination,
  PaginationContent,
  PaginationLink,
  PaginationItem,
  PaginationPrevious,
  PaginationNext,
  PaginationEllipsis,
}
