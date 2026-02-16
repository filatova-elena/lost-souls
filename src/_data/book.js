const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

// Load all book entries from the book directory
const bookDir = path.join(__dirname, 'book');
const entries = [];

// Read all chapter directories
const chapterDirs = fs.readdirSync(bookDir).filter(item => {
  const itemPath = path.join(bookDir, item);
  return fs.statSync(itemPath).isDirectory();
}).sort(); // Sort to maintain order

chapterDirs.forEach(chapterDir => {
  const chapterPath = path.join(bookDir, chapterDir);
  const files = fs.readdirSync(chapterPath).filter(f => 
    f.endsWith('.yaml') || f.endsWith('.yml')
  ).sort();
  
  files.forEach(file => {
    const filePath = path.join(chapterPath, file);
    try {
      const entry = yaml.load(fs.readFileSync(filePath, 'utf8'));
      if (entry) {
        entry.filename = path.basename(file, path.extname(file));
        entry.chapterDir = chapterDir;
        entries.push(entry);
      }
    } catch (error) {
      console.error(`Error reading ${filePath}:`, error.message);
    }
  });
});

// Sort entries by chapter directory first (to maintain chapter order), then by date, then by filename
entries.sort((a, b) => {
  // First sort by chapter directory (00, 01, 02, etc.)
  const chapterCompare = a.chapterDir.localeCompare(b.chapterDir);
  if (chapterCompare !== 0) return chapterCompare;
  
  // Within same chapter, sort by date
  if (a.date && b.date) {
    const dateCompare = a.date.localeCompare(b.date);
    if (dateCompare !== 0) return dateCompare;
  }
  
  // Finally by filename
  return a.filename.localeCompare(b.filename);
});

// Create a flat array with chapter pages and book pages
// We'll insert chapter pages before the first entry of each chapter
const pages = [];
let currentChapter = null;
let currentChapterDir = null;
let chapterNumber = 0;
let pageIndex = 0;

entries.forEach((entry, index) => {
  // If this is a new chapter, add a chapter page first
  if (entry.chapter && entry.chapter !== currentChapter) {
    currentChapter = entry.chapter;
    
    // Extract chapter number from folder name (e.g., "02_the_alchemist" -> 2)
    const chapterDirMatch = entry.chapterDir.match(/^(\d+)_/);
    if (chapterDirMatch) {
      chapterNumber = parseInt(chapterDirMatch[1], 10);
    } else {
      // Fallback: increment if we can't parse
      chapterNumber++;
    }
    
    // For prologue (00), use 0, otherwise use the number as-is
    // Display will be 1-indexed (0 -> 1, 1 -> 2, etc.)
    const displayChapterNumber = chapterNumber + 1;
    const isPrologue = chapterNumber === 0 || currentChapter.toLowerCase() === 'prologue';
    
    // Create a date object for sorting - use the first entry's date
    // Convert string date to Date object for Eleventy compatibility
    let chapterDate = null;
    if (entry.date) {
      try {
        chapterDate = new Date(entry.date);
      } catch (e) {
        // If date parsing fails, use a very early date
        chapterDate = new Date('1900-01-01');
      }
    } else {
      chapterDate = new Date('1900-01-01');
    }
    
    pages.push({
      type: 'chapter',
      chapter: currentChapter,
      chapterNumber: displayChapterNumber,
      isPrologue: isPrologue,
      id: `chapter-${displayChapterNumber}`,
      date: chapterDate, // Use Date object for Eleventy sorting
      dateString: entry.date, // Keep original string for display
      filename: `chapter-${displayChapterNumber}`,
      uniqueId: `chapter-${displayChapterNumber}`, // Simple chapter ID
      chapterDir: entry.chapterDir
    });
    
    pageIndex++; // Increment for next page
    
    currentChapterDir = entry.chapterDir;
  }
  
  // Add the book entry
  // Convert date string to Date object if it exists, but keep original string
  const entryWithDate = { ...entry };
  if (entry.date && typeof entry.date === 'string') {
    entryWithDate.dateString = entry.date; // Keep original string for display
    try {
      entryWithDate.date = new Date(entry.date); // Convert to Date for sorting
    } catch (e) {
      // Keep original string if parsing fails
      entryWithDate.date = new Date('1900-01-01');
    }
  }
  
  // Fix image paths in content - convert relative paths to absolute paths
  if (entryWithDate.content && typeof entryWithDate.content === 'string') {
    // Replace ../assets/ with /assets/images/
    entryWithDate.content = entryWithDate.content.replace(/\.\.\/assets\//g, '/assets/images/');
  }
  
  // Ensure unique ID - use filename if available, otherwise generate one
  entryWithDate.uniqueId = entry.filename ? entry.filename : `entry-${pageIndex++}`;
  pages.push({
    type: 'entry',
    ...entryWithDate
  });
});

module.exports = pages;
