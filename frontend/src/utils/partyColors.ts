/**
 * Political Party Color Scheme
 * Defines consistent colors for each political party across the application
 */

export const PARTY_COLORS: Record<string, string> = {
  // Major Parties
  'awamileague': '#006a4e',      // Green - Awami League color
  'bnp': '#FF9933',              // Orange - BNP color
  'jamaat': '#006400',           // Dark Green - Jamaat
  'jatiyaparty': '#DC143C',      // Crimson - Jatiya Party
  
  // Other Parties
  'bikaldhara': '#8B4513',       // Saddle Brown
  'gonoforum': '#4169E1',        // Royal Blue
  'ganofront': '#9370DB',        // Medium Purple
  'leftfront': '#B22222',        // Firebrick
  'islami': '#556B2F',           // Dark Olive Green
  'liberal': '#20B2AA',          // Light Sea Green
  'nationalist': '#FF6347',       // Tomato
  'ganosamhati': '#4682B4',      // Steel Blue
  '12party': '#DAA520',          // Goldenrod
  'communist': '#8B0000',        // Dark Red
  'workers': '#CD5C5C',          // Indian Red
  
  // Interim Government & Special Categories
  'interimgovernment': '#2F4F4F', // Dark Slate Gray
  'advisors': '#708090',          // Slate Gray
  'military': '#2F4F2F',          // Dark Olive
  'judiciary': '#191970',         // Midnight Blue
  'civilsociety': '#8B7355',      // Burlywood
  
  // Default for unknown parties
  'others': '#808080',            // Gray
  'unknown': '#A9A9A9'           // Dark Gray
}

/**
 * Get color for a political party
 * @param partyKey - The party key (e.g., 'bnp', 'awamileague')
 * @returns Hex color code
 */
export function getPartyColor(partyKey: string): string {
  const normalizedKey = partyKey.toLowerCase().replace(/\s+/g, '')
  return PARTY_COLORS[normalizedKey] || PARTY_COLORS['others']
}

/**
 * Category colors for the 9 categories
 */
export const CATEGORY_COLORS: Record<string, string> = {
  'Reform': '#3B82F6',                                    // Blue
  'Elections': '#10B981',                                  // Green
  'Trial of The Fascist Government': '#DC2626',           // Red
  'National Security': '#F59E0B',                         // Amber
  'Conspiracy': '#8B5CF6',                                 // Purple
  'External Actors': '#EC4899',                           // Pink
  'Proportional Representation (PR) system': '#14B8A6',   // Teal
  'Legal Basis of July Charter': '#6366F1',               // Indigo
  'Others': '#6B7280'                                     // Gray
}

/**
 * Get color for a category
 * @param categoryName - The category name
 * @returns Hex color code
 */
export function getCategoryColor(categoryName: string): string {
  return CATEGORY_COLORS[categoryName] || CATEGORY_COLORS['Others']
}

/**
 * Get a lighter shade of a color (for backgrounds)
 * @param color - Hex color code
 * @param opacity - Opacity value (0-1)
 * @returns RGBA color string
 */
export function getLightColor(color: string, opacity: number = 0.1): string {
  // Convert hex to RGB
  const hex = color.replace('#', '')
  const r = parseInt(hex.substring(0, 2), 16)
  const g = parseInt(hex.substring(2, 4), 16)
  const b = parseInt(hex.substring(4, 6), 16)
  
  return `rgba(${r}, ${g}, ${b}, ${opacity})`
}

/**
 * Get array of colors for multiple parties (for charts)
 * @param parties - Array of party keys
 * @returns Array of color codes
 */
export function getPartyColorsArray(parties: string[]): string[] {
  return parties.map(party => getPartyColor(party))
}

/**
 * Get array of category colors (for charts)
 * @param categories - Array of category names
 * @returns Array of color codes
 */
export function getCategoryColorsArray(categories: string[]): string[] {
  return categories.map(category => getCategoryColor(category))
}
