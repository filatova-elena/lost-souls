# Image Optimization Guide

This document outlines recommendations for optimizing images to improve Lighthouse performance scores, particularly for character and clue pages.

## Current Status

- ✅ Images have `width` and `height` attributes to prevent layout shifts
- ✅ Images use `loading="lazy"` for lazy loading
- ✅ Images have descriptive `alt` text for accessibility

## Recommended Improvements

### 1. Convert to Modern Image Formats (WebP/AVIF)

**Priority: High** - This will significantly reduce file sizes and improve LCP scores.

**Implementation Options:**

#### Option A: Build-time Conversion (Recommended)
Use a build plugin or script to automatically convert images during the Eleventy build process:

```bash
# Example using sharp (Node.js)
npm install --save-dev sharp
```

Create a build script that:
1. Scans `src/assets/images/` for PNG/JPEG files
2. Converts to WebP (and optionally AVIF)
3. Generates responsive sizes (e.g., 300w, 600w, 900w)
4. Updates image references in templates to use `<picture>` elements

#### Option B: Manual Conversion
Use tools like:
- [Squoosh](https://squoosh.app/) - Web-based image optimizer
- [ImageMagick](https://imagemagick.org/) - Command-line tool
- [Sharp](https://sharp.pixelplumbing.com/) - Node.js library

### 2. Implement Responsive Images

**Priority: High** - Reduces bandwidth for mobile users.

Update image tags to use `srcset` and `sizes`:

```html
<img 
  src="{{ site.baseUrl }}{{ character.image }}"
  srcset="{{ site.baseUrl }}{{ character.image | replace('.png', '-300w.webp') }} 300w,
          {{ site.baseUrl }}{{ character.image | replace('.png', '-600w.webp') }} 600w,
          {{ site.baseUrl }}{{ character.image | replace('.png', '-900w.webp') }} 900w"
  sizes="(max-width: 600px) 300px, (max-width: 900px) 600px, 900px"
  alt="{{ character.title }} character portrait"
  width="300"
  height="300"
  loading="lazy">
```

Or use `<picture>` element for format fallback:

```html
<picture>
  <source srcset="image.avif" type="image/avif">
  <source srcset="image.webp" type="image/webp">
  <img src="image.png" alt="..." width="300" height="300" loading="lazy">
</picture>
```

### 3. Image Sizing Guidelines

- **Character portraits**: 300x300px (1:1 aspect ratio)
- **Clue content images**: Max width 800px, maintain aspect ratio
- **Thumbnails**: 200x200px

### 4. Compression Targets

- **WebP**: Aim for 70-80% quality
- **AVIF**: Aim for 60-70% quality (better compression than WebP)
- **Target file sizes**: 
  - Character images: < 50KB
  - Content images: < 100KB

### 5. Build Process Integration

Consider adding an Eleventy transform or plugin:

```javascript
// .eleventy.js
const sharp = require('sharp');
const path = require('path');

eleventyConfig.addTransform('optimize-images', async (content, outputPath) => {
  if (outputPath && outputPath.endsWith('.html')) {
    // Process images in HTML
    // This is a simplified example - full implementation would need
    // to handle image discovery, conversion, and path updates
  }
  return content;
});
```

## Testing

After implementing optimizations:

1. Run Lighthouse audits on character and clue pages
2. Check LCP (Largest Contentful Paint) scores - target < 2.5s
3. Verify image quality is acceptable
4. Test on various devices and network conditions

## Resources

- [Web.dev Image Optimization Guide](https://web.dev/fast/#optimize-your-images)
- [Responsive Images Guide](https://developer.mozilla.org/en-US/docs/Learn/HTML/Multimedia_and_embedding/Responsive_images)
- [Eleventy Image Plugin](https://www.11ty.dev/docs/plugins/image/) - Official Eleventy image optimization plugin
