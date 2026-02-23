const yaml = require("js-yaml");
const filters = require("./src/_build/filters");

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
  eleventyConfig.addPassthroughCopy("src/book/*.css");
  
  // Copy shared modules to output js directory
  eleventyConfig.addPassthroughCopy({
    "src/lib/skills.js": "js/skills.js"
  });

  // Register all filters from filters module
  Object.entries(filters).forEach(([name, fn]) => {
    eleventyConfig.addFilter(name, fn);
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
