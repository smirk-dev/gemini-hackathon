import React from 'react';

interface LoadingProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
}

/**
 * Loading State Component
 * Shows loading animation with optional message
 * 
 * Usage:
 * {isGenerating && <LoadingState message="AI is thinking..." />}
 */
export function LoadingState({ message = 'Processing...', size = 'md' }: LoadingProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  return (
    <div className="flex items-center gap-3 p-4">
      {/* Animated spinner */}
      <div className={`${sizeClasses[size]} relative`}>
        <div className="absolute inset-0 rounded-full border-2 border-gray-300 border-t-blue-500 animate-spin" />
      </div>
      
      {/* Loading text */}
      <span className="text-sm text-gray-600 dark:text-gray-400 animate-pulse">
        {message}
      </span>
    </div>
  );
}

export default LoadingState;
