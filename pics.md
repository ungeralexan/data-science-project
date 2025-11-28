# Automated Event Images (Future Work)

Currently each event receives an image_key from the LLM, and the frontend maps that key to a static image.
This works but requires manual image collection and fails for niche or new events.

## What happens right now 
If no static image exists for an image_key, the backend can call an image-generation API (e.g. OpenAI DALL·E or Stability API) to create a small illustration based on:

- event title
- event category
- organizer/company name

## One time generation per label
Images are generated once per unique image_key, cached under
static/event_images/<image_key>.png,
and reused for all future events with the same label.

## What about costs 
Image generation APIs cost around $0.08–$0.12 per image (DALL·E).
Because we only generate one image per category, typical total cost is just a few euros

## Why would it be attractive
- No manual image collection
- Infinite coverage (even for niche events)
- Consistent visual style
- Easy to add after core pipeline is stable
