import React from "react";
import { AlertCircle, RefreshCw } from "lucide-react";

export const LoadingSkeleton: React.FC<{ rows?: number; height?: string }> = ({
  rows = 4,
  height = "h-24",
}) => {
  return (
    <div className="w-full space-y-3 animate-pulse">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className={`w-full rounded bg-[#E7E9ED]/50 ${height}`} />
      ))}
    </div>
  );
};

export const EmptyState: React.FC<{
  title: string;
  description: string;
  actionText?: string;
  onAction?: () => void;
}> = ({ title, description, actionText, onAction }) => {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-[#E7E9ED] bg-white p-8 text-center sm:p-12">
      <div className="mb-2 text-sm font-semibold text-[#17191D]">{title}</div>
      <p className="max-w-md text-xs text-[#707784] leading-relaxed">
        {description}
      </p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="mt-4 rounded-md border border-[#E7E9ED] bg-[#F7F8FA] px-3 py-1.5 text-xs font-medium text-[#17191D] hover:bg-[#E7E9ED] transition-colors"
        >
          {actionText}
        </button>
      )}
    </div>
  );
};

export const ErrorMessage: React.FC<{
  message: string;
  onRetry?: () => void;
}> = ({ message, onRetry }) => {
  return (
    <div className="flex items-center justify-between rounded-md border border-[#FCA5A5] bg-[#FEF2F2] p-4 text-xs text-[#D32F2F]">
      <div className="flex items-center gap-2">
        <AlertCircle className="h-4 w-4 shrink-0" />
        <span>{message}</span>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="flex items-center gap-1 font-medium text-[#B91C1C] hover:underline"
        >
          <RefreshCw className="h-3 w-3" />
          <span>Retry</span>
        </button>
      )}
    </div>
  );
};
