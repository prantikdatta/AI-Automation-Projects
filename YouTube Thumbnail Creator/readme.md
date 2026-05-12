# YouTube Thumbnail Creator (n8n Workflow)

AI-powered YouTube thumbnail generator built with n8n, OpenAI, and Google Gemini.

This workflow:

* Analyzes uploaded images using Google Gemini
* Generates optimized thumbnail prompts using OpenAI
* Creates professional YouTube thumbnails using Gemini image editing

---

# Workflow Overview

The workflow takes:

* Video title
* Video context/description
* Two uploaded images

It then:

1. Analyzes both images
2. Creates a high-converting thumbnail prompt
3. Generates the final thumbnail image

---

# Workflow Architecture

```text
Form Trigger
├── Analyze Image 1 (Gemini)
├── Analyze Image 2 (Gemini)
│
└── Merge
    └── Code (Combine Descriptions)
        └── AI Agent (OpenAI)
            └── Merge
                └── Code (Prepare Final Payload)
                    └── Wait (30s)
                        └── Edit Image (Gemini)
```

---

# Requirements

## APIs & Credentials

You need:

* OpenAI API Key
* Google Gemini API Key (Image Analysis)
* Google Gemini API Key (Image Editing / Nano Banana)

---

# Node-by-Node Setup

---

# 1. Form Trigger

## Purpose

Creates a web form for collecting thumbnail inputs.

## Configuration

### Form Settings

| Field            | Value                                      |
| ---------------- | ------------------------------------------ |
| Form Title       | `Youtube Thumbnail Creator`                |
| Form Description | `Create thumbnail for your youtube videos` |

### Form Fields

#### Field 1 — Text Input

| Setting     | Value                                |
| ----------- | ------------------------------------ |
| Label       | `Video Title`                        |
| Placeholder | `Vlog 02: You Don't Wanna Miss This` |

---

#### Field 2 — Textarea

| Setting  | Value                |
| -------- | -------------------- |
| Label    | `Video Idea/Context` |
| Required | `Yes`                |

---

#### Field 3 — File Upload

| Setting        | Value     |
| -------------- | --------- |
| Label          | `Image 1` |
| Multiple Files | `Off`     |
| Required       | `Yes`     |

---

#### Field 4 — File Upload

| Setting        | Value     |
| -------------- | --------- |
| Label          | `Image 2` |
| Multiple Files | `Off`     |
| Required       | `Yes`     |

---

### Options

Disable:

```text
Append Attribution
```

## Output

* Video title
* Video context
* Two uploaded binary images

---

# 2. Analyze Image 1 (Google Gemini)

## Purpose

Analyzes the first uploaded image.

## Configuration

| Setting         | Value                     |
| --------------- | ------------------------- |
| Resource        | `Image`                   |
| Operation       | `Analyze`                 |
| Model           | `models/gemini-2.5-flash` |
| Input Type      | `Binary`                  |
| Binary Property | `Image_1`                 |

## Prompt

```text
Analyze the image then give description on what is the image about, what is the meaning, and other details to create a prompt for youtube thumbnail.
```

## Connection

```text
Form Trigger → Analyze Image 1
```

---

# 3. Analyze Image 2 (Google Gemini)

## Purpose

Analyzes the second uploaded image.

## Configuration

Same as Node 2, except:

| Setting         | Value     |
| --------------- | --------- |
| Binary Property | `Image_2` |

## Connection

```text
Form Trigger → Analyze Image 2
```

---

# 4. Merge

## Purpose

Combines both image analysis results.

## Configuration

| Setting    | Value       |
| ---------- | ----------- |
| Mode       | `Combine`   |
| Combine By | `Multiplex` |

## Connections

```text
Analyze Image 1 → Merge (Input 1)
Analyze Image 2 → Merge (Input 2)
```

---

# 5. Code — Make It 1 Item

## Purpose

Combines image descriptions and binaries into one item.

## Code

```javascript
const items = $input.all();

const image1Text =
  items[0]?.json?.content?.parts?.[0]?.text || '';

const image2Text =
  items[1]?.json?.content?.parts?.[0]?.text || '';

const binaries = {};

// Collect all binary files dynamically
items.forEach(item => {
  if (item.binary) {
    Object.entries(item.binary).forEach(([key, value]) => {
      binaries[key] = value;
    });
  }
});

return [
  {
    json: {
      image1Description: image1Text,
      image2Description: image2Text
    },
    binary: binaries
  }
];
```

## Connection

```text
Merge → Make It 1 Item
```

---

# 6. OpenAI Chat Model

## Purpose

Provides the AI model used by the AI Agent.

## Configuration

| Setting | Value               |
| ------- | ------------------- |
| Model   | `chatgpt-4o-latest` |

## Connection

Connect to the AI Agent using:

```text
AI Language Model Input
```

---

# 7. AI Agent

## Purpose

Generates the optimized thumbnail generation prompt.

## Configuration

| Setting                   | Value    |
| ------------------------- | -------- |
| Prompt Type               | `Define` |
| Passthrough Binary Images | `Off`    |

Paste your full AI prompt here.

Example:

```text
# ROLE

You are a world-class YouTube thumbnail strategist and visual designer...
```

## Connections

### Main Input

```text
Make It 1 Item → AI Agent
```

### AI Model Input

```text
OpenAI Chat Model → AI Agent
```

---

# 8. Edit Fields

## Purpose

Renames binary properties for consistency.

## Configuration

### Assignment 1

| Setting | Value     |
| ------- | --------- |
| Name    | `Image 1` |
| Value   | `Image_1` |
| Type    | `Binary`  |

### Assignment 2

| Setting | Value     |
| ------- | --------- |
| Name    | `Image 2` |
| Value   | `Image_2` |
| Type    | `Binary`  |

## Connection

```text
Form Trigger → Edit Fields
```

---

# 9. Merge

## Purpose

Combines AI Agent output with original binary files.

## Connections

```text
AI Agent → Merge (Input 1)
Edit Fields → Merge (Input 2)
```

---

# 10. Code in JavaScript

## Purpose

Prepares the final payload for image generation.

## Code

```javascript
const items = $input.all();

const outJson = {};
const outBinary = {};

let textIndex = 1;
let imageIndex = 1;

items.forEach((item) => {

  // -------- TEXT ----------
  const text = item.json?.content?.parts?.[0]?.text;

  if (text) {
    outJson[`image${textIndex}Description`] = text;
    textIndex++;
  }

  // -------- BINARY ----------
  if (item.binary) {
    Object.entries(item.binary).forEach(([key, value]) => {
      outBinary[`image_${imageIndex}`] = value;
      imageIndex++;
    });
  }

});

return [
  {
    json: outJson,
    binary: outBinary
  }
];
```

## Connection

```text
Merge → Code in JavaScript
```

---

# 11. Wait

## Purpose

Adds delay before image generation to avoid API rate limits.

## Configuration

| Setting | Value        |
| ------- | ------------ |
| Amount  | `30 Seconds` |

## Connection

```text
Code in JavaScript → Wait
```

---

# 12. Edit an Image (Google Gemini)

## Purpose

Generates the final YouTube thumbnail.

## Configuration

| Setting   | Value                               |
| --------- | ----------------------------------- |
| Resource  | `Image`                             |
| Operation | `Edit`                              |
| Model     | `models/gemini-3-pro-image-preview` |

## Prompt

```text
={{ $('AI Agent').first().json.output }}

Strictly use only the Images provided, DO NOT generate new people. Maintain Character Consistency.

Color palette: white & yellow text with dark outlines, subtle blue/black background tones.

Font: bold sans-serif, thick stroke, YouTube-optimized readability.

Do NOT write too much text. Only include Maximum 5 Words in the Thumbnail. DO NOT CLUTTER with Texts. Keep It Clean and Classy. Just keep the Title Texts, remove any extra small pop ups on top of the thumbnail.
```

## Add Images

| Image   | Binary Property |
| ------- | --------------- |
| Image 1 | `image_1`       |
| Image 2 | `image_2`       |

## Connection

```text
Wait → Edit an Image
```

---

# Testing the Workflow

## Step 1

Click:

```text
Test Workflow
```

---

## Step 2

Open the generated Form Trigger URL.

---

## Step 3

Fill in:

* Video title
* Video description/context
* Upload Image 1
* Upload Image 2

---

## Step 4

Submit the form.

---

## Step 5

Monitor workflow execution inside n8n.

The final thumbnail will appear in:

```text
Edit an Image
```

---

# Optimization Tips

## Increase Wait Time

If you encounter API rate limits:

```text
Increase the Wait node duration
```

---

## Improve Image Quality

Use:

* High-resolution images
* Clear subjects
* Good lighting

---

## Customize Thumbnail Style

Modify:

* AI Agent prompt
* Final Gemini edit prompt
* Color palette
* Typography instructions

---

# Recommended Prompting Style

Best-performing YouTube thumbnails usually include:

* High contrast
* Large readable text
* Strong facial emotions
* Minimal clutter
* Clear focal point
* Maximum 3–5 words

---

# Final Output

The workflow automatically generates:

* CTR-optimized thumbnails
* Consistent branding
* AI-enhanced compositions
* YouTube-ready visuals

---

# Tech Stack

* n8n
* OpenAI GPT-4o
* Google Gemini 2.5 Flash
* Google Gemini Nano Banana Pro

---

# License

MIT License
