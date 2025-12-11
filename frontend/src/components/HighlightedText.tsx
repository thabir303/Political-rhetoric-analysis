import React from 'react';

interface HighlightedTextProps {
  text: string;
  highlight?: string;
  className?: string;
}

const HighlightedText: React.FC<HighlightedTextProps> = ({ 
  text, 
  highlight, 
  className = '' 
}) => {
  // If no highlight text provided, return plain text
  if (!highlight || !highlight.trim()) {
    return <span className={className}>{text}</span>;
  }

  // Escape special regex characters in the highlight string
  const escapeRegExp = (string: string) => {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  };

  // Create case-insensitive regex to find all occurrences
  const escapedHighlight = escapeRegExp(highlight.trim());
  const regex = new RegExp(`(${escapedHighlight})`, 'gi');
  
  // Split text by highlighted portions
  const parts = text.split(regex);

  return (
    <span className={className}>
      {parts.map((part, index) => {
        // Check if this part matches the highlight (case-insensitive)
        if (part.toLowerCase() === highlight.toLowerCase()) {
          return (
            <mark
              key={index}
              className="bg-yellow-200 text-gray-900 px-1 rounded font-medium"
              style={{
                backgroundColor: '#fef08a', // Tailwind yellow-200
                padding: '2px 4px'
              }}
            >
              {part}
            </mark>
          );
        }
        return <span key={index}>{part}</span>;
      })}
    </span>
  );
};

export default HighlightedText;
