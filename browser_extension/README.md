# URL Form Capture - Browser Extension

A simple Chrome extension that captures the URL of your current page and lets you fill out a quick form to save notes about it.

## Features

- 📍 Automatically captures the current page URL
- 📝 Auto-fills the page title
- 🏷️ Categorize pages (Reference, Tool, Inspiration, etc.)
- ⭐ Rate pages 1-5
- 💾 Saves entries to local browser storage

## Installation

### Chrome / Edge / Brave

1. Open your browser and go to `chrome://extensions/`
2. Enable **Developer mode** (toggle in top right corner)
3. Click **Load unpacked**
4. Select the folder containing these extension files
5. The extension icon will appear in your toolbar!

### Firefox

Firefox uses a slightly different manifest format. For Firefox:
1. Go to `about:debugging#/runtime/this-firefox`
2. Click **Load Temporary Add-on**
3. Select the `manifest.json` file

## Creating Icons

You'll need to create icon files. The easiest way:

1. Create a simple 128x128 PNG image (or use any icon)
2. Resize it to create these versions:
   - `icon16.png` (16x16)
   - `icon48.png` (48x48)
   - `icon128.png` (128x128)

Or just use a free icon generator like [favicon.io](https://favicon.io/)

## Usage

1. Navigate to any webpage
2. Click the extension icon in your toolbar
3. The URL will be captured automatically
4. Fill out the form fields
5. Click "Save Entry"

## Accessing Your Data

Your entries are stored in the browser's local storage. To view them:

1. Right-click the extension popup
2. Select "Inspect"
3. In the console, type: `exportEntries()`
4. Your entries will be logged and copied to clipboard as JSON

## Customization Ideas

- **Change the form fields**: Edit `popup.html` to add/remove questions
- **Add tags**: Implement a tagging system instead of categories
- **Export to file**: Add a button to download entries as JSON/CSV
- **Sync across devices**: Use `chrome.storage.sync` instead of `local`
- **Send to server**: Add a fetch call to POST data to your own API

## File Structure

```
browser-extension/
├── manifest.json    # Extension configuration
├── popup.html       # The popup UI and styles
├── popup.js         # JavaScript logic
├── icon16.png       # Toolbar icon (create this)
├── icon48.png       # Extension page icon (create this)
├── icon128.png      # Chrome Web Store icon (create this)
└── README.md        # This file
```

## Troubleshooting

**Extension not loading?**
- Make sure all files are in the same folder
- Check the console in `chrome://extensions/` for errors

**URL not showing?**
- Some special pages (chrome://, about:, etc.) don't allow URL access
- The extension needs the `activeTab` permission (already included)

**Data not saving?**
- Check the browser console for errors
- Make sure the `storage` permission is in manifest.json

## License

Do whatever you want with this code! 🎉
