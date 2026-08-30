---
name: Institutional Trust
colors:
  surface: '#f7fafc'
  surface-dim: '#d7dadc'
  surface-bright: '#f7fafc'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f1f4f6'
  surface-container: '#ebeef0'
  surface-container-high: '#e5e9eb'
  surface-container-highest: '#e0e3e5'
  on-surface: '#181c1e'
  on-surface-variant: '#43474f'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eef1f3'
  outline: '#737780'
  outline-variant: '#c3c6d1'
  surface-tint: '#3a5f94'
  primary: '#001e40'
  on-primary: '#ffffff'
  primary-container: '#003366'
  on-primary-container: '#799dd6'
  inverse-primary: '#a7c8ff'
  secondary: '#305ea0'
  on-secondary: '#ffffff'
  secondary-container: '#8cb7ff'
  on-secondary-container: '#0f4787'
  tertiary: '#181f23'
  on-tertiary: '#ffffff'
  tertiary-container: '#2d3438'
  on-tertiary-container: '#959ca1'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d5e3ff'
  primary-fixed-dim: '#a7c8ff'
  on-primary-fixed: '#001b3c'
  on-primary-fixed-variant: '#1f477b'
  secondary-fixed: '#d6e3ff'
  secondary-fixed-dim: '#a9c7ff'
  on-secondary-fixed: '#001b3d'
  on-secondary-fixed-variant: '#0e4686'
  tertiary-fixed: '#dce3e8'
  tertiary-fixed-dim: '#c0c7cc'
  on-tertiary-fixed: '#161d20'
  on-tertiary-fixed-variant: '#41484c'
  background: '#f7fafc'
  on-background: '#181c1e'
  surface-variant: '#e0e3e5'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  title-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.01em
  caption:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  container-max: 1200px
  gutter: 24px
  margin-desktop: 40px
  margin-mobile: 16px
---

## Brand & Style

This design system is built to convey **expertise, reliability, and security** for high-stakes financial interactions. The aesthetic is a refined **Corporate Modern** style that prioritizes absolute clarity and professional poise. 

The visual narrative avoids unnecessary decoration, focusing instead on structural integrity and high-quality typography. By utilizing a "Soft Professional" approach—combining rigid grid structures with gentle organic curves—the UI feels both technologically advanced and humanly accessible. The goal is to evoke the feeling of stepping into a premier physical wealth management office: quiet, orderly, and meticulously maintained.

## Colors

The palette is anchored in **Deep Navy**, symbolizing stability and institutional knowledge. 

- **Primary (#003366):** Used for critical brand moments, primary actions, and headers.
- **Secondary (#004080):** Used for interactive states and supportive structural elements.
- **Surface & Backgrounds:** The design relies on `#F4F7F9` (Off-white/Gray) for large background areas to reduce eye strain, while pure white (`#FFFFFF`) is reserved for foreground cards and chat bubbles to create a clear "layering" effect.
- **Functional Colors:** Use standard semantic success (Green), warning (Amber), and error (Red) tones, but desaturate them slightly to maintain the premium, understated atmosphere.

## Typography

The design system utilizes **Inter** for all roles to leverage its exceptional legibility and systematic appearance. 

- **Weight Strategy:** Use `600` (Semi-bold) for headlines to establish authority and `400` (Regular) for long-form reading to ensure a comfortable experience.
- **Optical Sizing:** Large headlines use slight negative letter spacing to feel more cohesive and high-end.
- **Hierarchy:** Maintain a strict vertical rhythm. Section headers should be significantly larger than body text to allow users to scan for financial terms quickly.

## Layout & Spacing

The design system employs a **Fixed Grid** for desktop centered layouts and a **Fluid Grid** for mobile chat interfaces.

- **The 8px Rule:** All spacing between elements (padding, margins) must be increments of 8px to ensure visual harmony.
- **Chat Layout:** The chat interface should be constrained to a maximum width of 800px on desktop to prevent long line lengths that hinder readability.
- **Margins:** Generous white space is a core requirement. Surfaces should never feel "crowded." Use 24px or 32px of internal padding for cards to emphasize the premium nature of the content.

## Elevation & Depth

This design system uses **Ambient Shadows** to create a clean, multi-layered environment. 

1. **Base Level:** The background surface (`#F4F7F9`).
2. **Elevated Level (Cards/Bubbles):** White surfaces with a soft, diffused shadow. Shadow parameters: `0px 4px 20px rgba(0, 51, 102, 0.08)`. The slight blue tint in the shadow maintains brand consistency and feels softer than neutral black.
3. **Interactive Level (Active/Hover):** On hover, shadows should expand slightly: `0px 8px 30px rgba(0, 51, 102, 0.12)`.

Avoid heavy inner shadows or skeuomorphic gradients; depth should be used purely to distinguish interactive elements from the background.

## Shapes

The design system uses a **Rounded (0.5rem / 8px)** base to strike a balance between friendly and professional. 

- **Main Cards & Chat Bubbles:** Use 12px (`rounded-lg`) to provide a modern, soft feel that contrasts with the traditional "sharp" edges of legacy finance apps.
- **Quick Action Buttons:** Use 8px to maintain a more functional, "tool-like" appearance.
- **Inputs:** Maintain 8px roundedness for consistency with the button set.

## Components

### Chat Bubbles
- **Assistant Bubbles:** White background, 1px border (`#E1E8ED`), 12px corner radius. Align to the left.
- **User Bubbles:** Primary Color (`#003366`) background, white text, 12px corner radius. Align to the right.

### Interactive Quick Actions
- **Style:** Ghost-style buttons with a 1px border using `#003366` and a background of `#FFFFFF`.
- **Interaction:** On hover, fill with `#E1E8ED` to indicate clickability without overpowering the primary CTA.

### Disclaimer Banners
- **Placement:** Always pinned to the top or bottom of the chat view.
- **Style:** Subtle light gray background (`#F4F7F9`), small caption-sized text, and a distinct "Institutional Trust" blue icon to signify legal importance.

### Input Fields
- **Design:** Large 56px height for touch-friendliness. 
- **States:** Focus state should use a 2px solid border of the Secondary Color (`#004080`) with a soft glow effect.

### Progress Indicators
- Use a slim, linear progress bar in the Secondary Color at the top of the chat window for multi-step FAQ flows.