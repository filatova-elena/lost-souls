const markdownIt = require("markdown-it");
const yaml = require("js-yaml");
const markdownItOptions = {
  html: true,
  breaks: true,
  linkify: true
};

const md = new markdownIt(markdownItOptions);

module.exports = function(eleventyConfig) {
  // Register YAML data file format
  eleventyConfig.addDataExtension("yaml,yml", (contents) => {
    return yaml.load(contents);
  });

  // Pass through static assets
  eleventyConfig.addPassthroughCopy("src/css");
  eleventyConfig.addPassthroughCopy("src/js");
  eleventyConfig.addPassthroughCopy("src/assets");
  eleventyConfig.addPassthroughCopy("src/fonts");
  eleventyConfig.addPassthroughCopy("src/quests/*.css");
  eleventyConfig.addPassthroughCopy("src/clues/*.css");
  eleventyConfig.addPassthroughCopy("src/refs/*.css");

  // Add filters
  eleventyConfig.addFilter("json", function(value) {
    return JSON.stringify(value);
  });

  // Markdown filter - renders markdown strings to HTML
  eleventyConfig.addFilter("markdown", function(value) {
    if (!value) return "";
    return md.render(value);
  });

  // Get clue by filename - throws error if not found
  eleventyConfig.addFilter("getClue", function(filename, cluesData) {
    if (!filename || !cluesData) {
      throw new Error(`getClue: Missing filename or cluesData. filename=${filename}, cluesData=${!!cluesData}`);
    }
    const clue = cluesData.byFilename?.get(filename);
    if (!clue) {
      throw new Error(`Clue not found: "${filename}". Available clues: ${Array.from(cluesData.byFilename?.keys() || []).slice(0, 10).join(', ')}...`);
    }
    return clue;
  });

  // Get rumor by filename
  eleventyConfig.addFilter("getRumor", function(filename, rumorsData) {
    if (!filename || !rumorsData) return null;
    return rumorsData.byFilename?.get(filename) || null;
  });

  // Check if a key is a metadata key (for clue organization template)
  eleventyConfig.addFilter("isMetaKey", function(key) {
    return ["name", "purpose", "constraints", "notes"].includes(key);
  });

  // Concatenate arrays (for building tag lists in templates)
  eleventyConfig.addFilter("concat", function(arr, items) {
    if (!Array.isArray(arr)) return items || [];
    if (!Array.isArray(items)) return arr;
    return arr.concat(items);
  });

  // Get emoji icon for clue type
  eleventyConfig.addFilter("typeIcon", function(type) {
    if (!type) return "📝";
    const t = type.toLowerCase();
    if (t.includes("vision")) return "👁️";
    if (t.includes("artifact") || t.includes("object")) return "🏺";
    if (t.includes("document") || t.includes("medical") || t.includes("legal") || t.includes("financial")) return "📄";
    if (t.includes("botanical")) return "🌿";
    if (t.includes("newspaper")) return "📰";
    return "📝";
  });

  // Add collection for characters
  eleventyConfig.addCollection("characters", function(collectionApi) {
    return collectionApi.getAll().filter(item => item.data.type === "character");
  });

  // Add collection for clues
  eleventyConfig.addCollection("clues", function(collectionApi) {
    return collectionApi.getAll().filter(item => item.data.type === "clue");
  });

  // Add collection for book chapters
  eleventyConfig.addCollection("chapters", function(collectionApi) {
    return collectionApi.getAll().filter(item => item.data.type === "chapter");
  });

  return {
    pathPrefix: process.env.PATH_PREFIX || "/",
    dir: {
      input: "src",
      output: "_site",
      includes: "_includes",
      data: "_data"
    },
    templateFormats: ["njk", "md", "html"],
    htmlTemplateEngine: "njk",
    markdownTemplateEngine: "njk",
    dataFileExtensions: ["yaml", "yml", "json", "js", "cjs", "mjs", "ts"]
  };
};
