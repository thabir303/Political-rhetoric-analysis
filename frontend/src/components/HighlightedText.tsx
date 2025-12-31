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

  // Clean the highlight text - remove quotes, extra whitespace
  const cleanHighlight = (str: string): string => {
    return str
      .replace(/^["'""\s]+|["'""\s]+$/g, '')  // Remove leading/trailing quotes and spaces
      .replace(/\s+/g, ' ')  // Normalize whitespace
      .trim();
  };

  const cleanedHighlight = cleanHighlight(highlight);
  
  // If cleaned highlight is too short or empty, return plain text
  if (!cleanedHighlight || cleanedHighlight.length < 10) {
    return <span className={className}>{text}</span>;
  }

  // Normalize text whitespace for comparison
  const normalizedText = text.replace(/\s+/g, ' ');
  const normalizedHighlight = cleanedHighlight.replace(/\s+/g, ' ');

  // Try to find the start position using first 30-40 chars of the excerpt
  const searchLength = Math.min(40, normalizedHighlight.length);
  const searchPhrase = normalizedHighlight.substring(0, searchLength);
  
  // Find where the excerpt starts in the original text
  let startIndex = normalizedText.indexOf(searchPhrase);
  
  // If not found, try with shorter phrase
  if (startIndex === -1 && searchPhrase.length > 20) {
    const shorterPhrase = normalizedHighlight.substring(0, 25);
    startIndex = normalizedText.indexOf(shorterPhrase);
  }
  
  // If still not found, try case-insensitive
  if (startIndex === -1) {
    startIndex = normalizedText.toLowerCase().indexOf(searchPhrase.toLowerCase());
  }

  // If we found the start, highlight the full excerpt length
  if (startIndex !== -1) {
    // Calculate end position - use the full excerpt length
    const highlightLength = Math.min(normalizedHighlight.length, normalizedText.length - startIndex);
    const endIndex = startIndex + highlightLength;
    
    // Map back to original text positions (handle whitespace differences)
    let originalStart = 0;
    let normalizedPos = 0;
    
    // Find original start position
    for (let i = 0; i < text.length && normalizedPos < startIndex; i++) {
      if (text[i].match(/\s/)) {
        if (i === 0 || !text[i-1].match(/\s/)) {
          normalizedPos++;
        }
      } else {
        normalizedPos++;
      }
      originalStart = i + 1;
    }
    
    // Find original end position
    let originalEnd = originalStart;
    for (let i = originalStart; i < text.length && normalizedPos < endIndex; i++) {
      if (text[i].match(/\s/)) {
        if (i === 0 || !text[i-1].match(/\s/)) {
          normalizedPos++;
        }
      } else {
        normalizedPos++;
      }
      originalEnd = i + 1;
    }

    const beforeText = text.substring(0, originalStart);
    const highlightedText = text.substring(originalStart, originalEnd);
    const afterText = text.substring(originalEnd);

    return (
      <span className={className}>
        {beforeText}
        <mark
          className="bg-yellow-200 text-gray-900 rounded font-medium"
          style={{
            backgroundColor: '#fef08a',
            padding: '2px 4px',
            borderRadius: '4px'
          }}
        >
          {highlightedText}
        </mark>
        {afterText}
      </span>
    );
  }

  // Fallback: no highlight found
  return <span className={className}>{text}</span>;
};

export default HighlightedText;
