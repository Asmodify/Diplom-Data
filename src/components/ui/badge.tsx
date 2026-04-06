import * as React from 'react';
import { cn } from '../../lib/utils';

type BadgeVariant = 'default' | 'secondary' | 'outline';

type BadgeProps = React.HTMLAttributes<HTMLSpanElement> & {
  variant?: BadgeVariant;
};

const variantClasses: Record<BadgeVariant, string> = {
  default: 'bg-cyan-500/15 text-cyan-200 ring-1 ring-inset ring-cyan-400/30',
  secondary: 'bg-slate-800/90 text-slate-200 ring-1 ring-inset ring-slate-700',
  outline: 'bg-transparent text-slate-300 ring-1 ring-inset ring-slate-700',
};

export function Badge({ className, variant = 'default', ...props }: BadgeProps) {
  return <span className={cn('inline-flex items-center rounded-full px-3 py-1 text-xs font-medium', variantClasses[variant], className)} {...props} />;
}