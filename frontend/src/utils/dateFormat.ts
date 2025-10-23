/**
 * Formats a date string or Date object to DD/MM/YYYY format
 * @param date - Date string (YYYY-MM-DD) or Date object
 * @returns Formatted date string in DD/MM/YYYY format
 */
export const formatDateToDDMMYYYY = (date: string | Date): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date
  
  const day = String(dateObj.getDate()).padStart(2, '0')
  const month = String(dateObj.getMonth() + 1).padStart(2, '0')
  const year = dateObj.getFullYear()
  
  return `${day}/${month}/${year}`
}

/**
 * Formats a date for input[type="date"] fields (YYYY-MM-DD format)
 * @param date - Date object
 * @returns Formatted date string in YYYY-MM-DD format
 */
export const formatDateForInput = (date: Date): string => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  
  return `${year}-${month}-${day}`
}
