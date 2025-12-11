"""
QR Code Generation Service
Generates QR code images for vehicle tags
"""
import qrcode
from PIL import Image, ImageDraw, ImageFont
import io
from django.conf import settings
import os


def generate_tag_image(vtid, base_url='https://app.mylunago.com'):
    """
    Generate vehicle tag image with QR code
    
    Args:
        vtid: Vehicle Tag ID (e.g., VTID1)
        base_url: Base URL for the application
    
    Returns:
        BytesIO object containing the image
    """
    # Create QR code
    qr_url = f"{base_url}/vehicle-tag/alert/{vtid}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # Higher error correction to allow logo
        box_size=10,
        border=4,
    )
    qr.add_data(qr_url)
    qr.make(fit=True)
    
    # Create QR code image
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_img = qr_img.resize((300, 300))  # Resize QR code
    # Ensure QR code is in RGB mode for proper pasting
    if qr_img.mode != 'RGB':
        qr_img = qr_img.convert('RGB')
    
    # No logo in center of QR code - clean QR code only
    
    # Create main image (matching the design from the image description)
    # Dimensions: approximately 600x900 pixels (portrait orientation)
    width = 600
    height = 900
    
    # Create image with white background
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Colors (matching the design)
    dark_green = (34, 139, 34)  # Dark green for body
    white = (255, 255, 255)
    black = (0, 0, 0)
    
    # Body section (dark green) - starts from top
    body_height = 720  # Increased to make footer smaller
    draw.rectangle([(0, 0), (width, body_height)], fill=dark_green)
    
    # Footer section (white)
    footer_start = body_height
    footer_height = height - footer_start
    draw.rectangle([(0, footer_start), (width, height)], fill=white)
    
    # Try to load fonts with Unicode support for Nepali text
    # Separate fonts for English and Nepali text to ensure proper rendering
    english_font_paths = [
        # Linux fonts that support English well
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        # Windows fonts
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/ARIAL.TTF",
        "C:/Windows/Fonts/arialbd.ttf",  # Arial Bold
        # macOS fonts
        "/System/Library/Fonts/Helvetica.ttc",
        # Fallback
        "arial.ttf",
        "Arial.ttf",
    ]

    nepali_font_paths = [
        # Linux fonts that support Devanagari
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
        "/usr/share/fonts/truetype/lohit-devanagari/Lohit-Devanagari.ttf",
        # Windows fonts
        "C:/Windows/Fonts/mangal.ttf",
        "C:/Windows/Fonts/MANGAL.TTF",
        "C:/Windows/Fonts/kalapi.ttf",
        "C:/Windows/Fonts/KALAPI.TTF",
        "C:/Windows/Fonts/notosansdevanagari.ttf",
        "C:/Windows/Fonts/Nirmala.ttf",
        "C:/Windows/Fonts/NIRMALA.TTF",
        # macOS fonts
        "/System/Library/Fonts/Supplemental/Devanagari.ttc",
    ]

    title_font = None
    subtitle_font = None
    text_font = None
    small_font = None
    nepali_font = None  # Separate font for Nepali text

    # First, load English fonts for English text
    for font_path in english_font_paths:
        try:
            test_font = ImageFont.truetype(font_path, 20)
            if title_font is None:
                title_font = ImageFont.truetype(font_path, 38)  # Slightly smaller (was 42)
            if text_font is None:
                text_font = ImageFont.truetype(font_path, 32)  # Increased for Download text prominence
            if small_font is None:
                small_font = ImageFont.truetype(font_path, 16)  # Slightly smaller (was 18)
            if title_font and text_font and small_font:
                break
        except:
            continue

    # Then, load Devanagari fonts specifically for Nepali text
    for font_path in nepali_font_paths:
        try:
            test_font = ImageFont.truetype(font_path, 20)
            if subtitle_font is None:
                subtitle_font = ImageFont.truetype(font_path, 34)  # Increased for Nepali subtitle prominence
            if nepali_font is None:
                nepali_font = ImageFont.truetype(font_path, 16)  # Slightly smaller (was 18)
            if subtitle_font and nepali_font:
                break
        except:
            continue

    # Fallback to default font if all attempts fail
    if title_font is None:
        title_font = ImageFont.load_default()
    if subtitle_font is None:
        subtitle_font = ImageFont.load_default()
    if text_font is None:
        text_font = ImageFont.load_default()
    if small_font is None:
        small_font = ImageFont.load_default()
    if nepali_font is None:
        nepali_font = small_font  # Use small_font as fallback for Nepali
    
    # Body section - Title at top
    body_y = 40
    title_text = "Contact Vehicle Owner"
    subtitle_text = "सवारीधनी लाई सम्पर्क गर्नुहोस् ।"
    
    # Calculate text positions (centered) - with larger spacing for bigger fonts
    bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_width = bbox[2] - bbox[0]
    title_height = bbox[3] - bbox[1]
    title_x = (width - title_width) // 2
    draw.text((title_x, body_y), title_text, fill=white, font=title_font)
    
    bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
    subtitle_width = bbox[2] - bbox[0]
    subtitle_height = bbox[3] - bbox[1]
    subtitle_x = (width - subtitle_width) // 2
    draw.text((subtitle_x, body_y + title_height + 25), subtitle_text, fill=white, font=subtitle_font)
    
    # Place QR code in center of body (with more spacing)
    qr_x = (width - qr_img.width) // 2
    qr_y = body_y + title_height + subtitle_height + 90
    img.paste(qr_img, (qr_x, qr_y))
    
    # Tag ID below QR code
    tag_id_text = f"TAG ID: {vtid}"
    bbox = draw.textbbox((0, 0), tag_id_text, font=text_font)
    tag_id_width = bbox[2] - bbox[0]
    tag_id_height = bbox[3] - bbox[1]
    tag_id_x = (width - tag_id_width) // 2
    draw.text((tag_id_x, qr_y + qr_img.height + 30), tag_id_text, fill=white, font=text_font)
    
    # Download app text
    app_text = "Download Luna IOT App Now"
    bbox = draw.textbbox((0, 0), app_text, font=text_font)
    app_width = bbox[2] - bbox[0]
    app_x = (width - app_width) // 2
    draw.text((app_x, qr_y + qr_img.height + tag_id_height + 60), app_text, fill=white, font=text_font)
    
    # Footer section - First row: Icons
    footer_y = footer_start + 15  # Reduced spacing (was 20)
    icon_size = 55  # Slightly smaller icons (was 60)
    logo_width = 240  # Slightly smaller logo width (was 260)
    logo_height = 55  # Slightly smaller logo height (was 60)
    icon_spacing = 25  # Reduced spacing (was 30)
    
    # Calculate positions for three icons centered horizontally
    # Logo is wider, so we need to account for that
    total_icons_width = logo_width + icon_size + icon_size + (icon_spacing * 2)
    start_x = (width - total_icons_width) // 2
    
    # Load and paste the three images
    try:
        # Get the path to static files
        static_dir = os.path.join(settings.BASE_DIR, 'static', 'vehicle_tag', 'images')
        
        # Load logo (left icon) - make it wider for better visibility
        logo_path = os.path.join(static_dir, 'logo.png')
        if os.path.exists(logo_path):
            logo_icon = Image.open(logo_path)
            # Resize logo to be wider (maintain aspect ratio or use fixed wider size)
            logo_icon = logo_icon.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
            if logo_icon.mode == 'RGBA':
                img.paste(logo_icon, (start_x, footer_y), logo_icon)
            else:
                img.paste(logo_icon, (start_x, footer_y))
        
        # Load shield icon (center icon)
        shield_path = os.path.join(static_dir, 'shield.png')
        if os.path.exists(shield_path):
            shield_icon = Image.open(shield_path)
            shield_icon = shield_icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
            shield_x = start_x + logo_width + icon_spacing
            if shield_icon.mode == 'RGBA':
                img.paste(shield_icon, (shield_x, footer_y), shield_icon)
            else:
                img.paste(shield_icon, (shield_x, footer_y))
        
        # Load Google Lens icon (right icon)
        google_lens_path = os.path.join(static_dir, 'google_lens.png')
        if os.path.exists(google_lens_path):
            google_lens_icon = Image.open(google_lens_path)
            google_lens_icon = google_lens_icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
            google_lens_x = start_x + logo_width + icon_spacing + icon_size + icon_spacing
            if google_lens_icon.mode == 'RGBA':
                img.paste(google_lens_icon, (google_lens_x, footer_y), google_lens_icon)
            else:
                img.paste(google_lens_icon, (google_lens_x, footer_y))
    except Exception as e:
        # If images fail to load, continue without them
        print(f"Warning: Could not load footer images: {e}")
    
    # Footer section - Second row: Nepali text
    emergency_text = "यदि यो सवारी साधन कुनै आपत्कालीन अवस्थामा छ भने माथिको QR स्क्यान गरी सम्बन्धित व्यक्तिलाई खबर गरिदिनुहोला।"
    
    # Split text into segments to handle mixed English/Nepali text
    # Split by "QR" to render it with English font
    text_segments = emergency_text.split("QR")
    
    # Wrap text if needed and handle mixed fonts
    def wrap_text_with_mixed_fonts(text_segments, nepali_font, english_font, max_width):
        """Wrap text handling mixed Nepali and English fonts"""
        lines = []
        current_line_parts = []
        current_width = 0
        
        for segment_idx, segment in enumerate(text_segments):
            words = segment.split()
            for word in words:
                # Determine font based on whether it's English or Nepali
                # Simple check: if word contains only ASCII, use English font
                is_english = all(ord(c) < 128 for c in word)
                font_to_use = english_font if is_english else nepali_font
                
                bbox = draw.textbbox((0, 0), word + " ", font=font_to_use)
                word_width = bbox[2] - bbox[0]
                
                if current_width + word_width > max_width:
                    if current_line_parts:
                        lines.append(current_line_parts)
                        current_line_parts = []
                        current_width = 0
                
                current_line_parts.append((word, font_to_use))
                current_width += word_width
            
            # Add "QR" between segments (except after last segment)
            if segment_idx < len(text_segments) - 1:
                bbox = draw.textbbox((0, 0), "QR ", font=english_font)
                qr_width = bbox[2] - bbox[0]
                if current_width + qr_width > max_width:
                    if current_line_parts:
                        lines.append(current_line_parts)
                        current_line_parts = []
                        current_width = 0
                current_line_parts.append(("QR", english_font))
                current_width += qr_width
        
        if current_line_parts:
            lines.append(current_line_parts)
        
        return lines
    
    wrapped_lines = wrap_text_with_mixed_fonts(text_segments, nepali_font, small_font, width - 40)
    
    # Draw emergency message in dark green (with larger spacing for bigger font)
    # Handle mixed English/Nepali text rendering
    emergency_y = footer_y + icon_size + 20  # Reduced spacing (was 30)
    line_spacing = 22  # Slightly reduced spacing (was 25)
    
    for i, line_parts in enumerate(wrapped_lines):
        # Calculate total width of the line
        total_width = 0
        for word, font in line_parts:
            bbox = draw.textbbox((0, 0), word + " ", font=font)
            total_width += bbox[2] - bbox[0]
        
        # Start position (centered)
        x_pos = (width - total_width) // 2
        
        # Draw each word with its appropriate font
        for word, font in line_parts:
            draw.text((x_pos, emergency_y + i * line_spacing), word + " ", fill=dark_green, font=font)
            bbox = draw.textbbox((0, 0), word + " ", font=font)
            x_pos += bbox[2] - bbox[0]
    
    # Add grey border around the entire design
    # Create a frame by making a slightly larger image with grey background
    border_width = 3  # Thin border width in pixels
    grey_color = (200, 200, 200)  # Light grey color
    
    # Create new image with border space
    bordered_width = width + (border_width * 2)
    bordered_height = height + (border_width * 2)
    bordered_img = Image.new('RGB', (bordered_width, bordered_height), color=grey_color)
    
    # Paste the original image on top of the grey background (centered)
    bordered_img.paste(img, (border_width, border_width))
    
    # Use the bordered image for final output
    img = bordered_img
    
    # Ensure image is in RGB mode for proper PNG encoding
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Convert to bytes - ensure proper PNG encoding
    img_io = io.BytesIO()
    # Save with explicit parameters to ensure proper encoding
    try:
        img.save(img_io, format='PNG', optimize=False)
    except Exception as e:
        # If save fails, try with default settings
        img_io = io.BytesIO()
        img.save(img_io, format='PNG')
    
    # Reset to beginning of stream
    img_io.seek(0)
    
    # Verify the image was saved properly (check if stream has content)
    if img_io.getvalue() == b'':
        # If stream is empty, there was an error - create a simple error image
        error_img = Image.new('RGB', (600, 900), color='white')
        error_draw = ImageDraw.Draw(error_img)
        error_draw.text((200, 400), 'Error generating image', fill='black')
        img_io = io.BytesIO()
        error_img.save(img_io, format='PNG')
        img_io.seek(0)
    
    return img_io

