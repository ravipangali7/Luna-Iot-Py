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
    
    # Add actual logo in the center of QR code
    logo_size = 60
    try:
        # Get the path to static files
        static_dir = os.path.join(settings.BASE_DIR, 'static', 'vehicle_tag', 'images')
        logo_path = os.path.join(static_dir, 'logo.png')
        
        if os.path.exists(logo_path):
            logo_img = Image.open(logo_path)
            # Resize logo to fit in QR code center
            logo_img = logo_img.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # Convert to RGBA if needed for transparency
            if logo_img.mode != 'RGBA':
                logo_img = logo_img.convert('RGBA')
            
            # Paste logo in center of QR code
            qr_center_x = qr_img.width // 2 - logo_size // 2
            qr_center_y = qr_img.height // 2 - logo_size // 2
            qr_img.paste(logo_img, (qr_center_x, qr_center_y), logo_img)
    except Exception as e:
        # If logo fails to load, continue without it
        print(f"Warning: Could not load logo for QR code: {e}")
    
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
    body_height = 650
    draw.rectangle([(0, 0), (width, body_height)], fill=dark_green)
    
    # Footer section (white)
    footer_start = body_height
    footer_height = height - footer_start
    draw.rectangle([(0, footer_start), (width, height)], fill=white)
    
    # Try to load fonts with Unicode support for Nepali text
    # Try multiple font paths for better compatibility
    font_paths = [
        "arial.ttf",
        "Arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/ARIAL.TTF",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    
    title_font = None
    subtitle_font = None
    text_font = None
    small_font = None
    
    # Try to load bold fonts for better visibility
    for font_path in font_paths:
        try:
            if title_font is None:
                title_font = ImageFont.truetype(font_path, 42)  # Bigger and bold
            if subtitle_font is None:
                subtitle_font = ImageFont.truetype(font_path, 28)  # Bigger
            if text_font is None:
                text_font = ImageFont.truetype(font_path, 22)  # Bigger
            if small_font is None:
                small_font = ImageFont.truetype(font_path, 18)  # Bigger
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
    draw.text((subtitle_x, body_y + title_height + 20), subtitle_text, fill=white, font=subtitle_font)
    
    # Place QR code in center of body (with more spacing)
    qr_x = (width - qr_img.width) // 2
    qr_y = body_y + title_height + subtitle_height + 80
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
    draw.text((app_x, qr_y + qr_img.height + tag_id_height + 50), app_text, fill=white, font=text_font)
    
    # Footer section - First row: Icons
    footer_y = footer_start + 20
    icon_size = 60  # Size for each icon
    icon_spacing = 30  # Space between icons
    
    # Calculate positions for three icons centered horizontally
    total_icons_width = (icon_size * 3) + (icon_spacing * 2)
    start_x = (width - total_icons_width) // 2
    
    # Load and paste the three images
    try:
        # Get the path to static files
        static_dir = os.path.join(settings.BASE_DIR, 'static', 'vehicle_tag', 'images')
        
        # Load logo (left icon)
        logo_path = os.path.join(static_dir, 'logo.png')
        if os.path.exists(logo_path):
            logo_icon = Image.open(logo_path)
            logo_icon = logo_icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
            if logo_icon.mode == 'RGBA':
                img.paste(logo_icon, (start_x, footer_y), logo_icon)
            else:
                img.paste(logo_icon, (start_x, footer_y))
        
        # Load shield icon (center icon)
        shield_path = os.path.join(static_dir, 'shield.png')
        if os.path.exists(shield_path):
            shield_icon = Image.open(shield_path)
            shield_icon = shield_icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
            shield_x = start_x + icon_size + icon_spacing
            if shield_icon.mode == 'RGBA':
                img.paste(shield_icon, (shield_x, footer_y), shield_icon)
            else:
                img.paste(shield_icon, (shield_x, footer_y))
        
        # Load Google Lens icon (right icon)
        google_lens_path = os.path.join(static_dir, 'google_lens.png')
        if os.path.exists(google_lens_path):
            google_lens_icon = Image.open(google_lens_path)
            google_lens_icon = google_lens_icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
            google_lens_x = start_x + (icon_size + icon_spacing) * 2
            if google_lens_icon.mode == 'RGBA':
                img.paste(google_lens_icon, (google_lens_x, footer_y), google_lens_icon)
            else:
                img.paste(google_lens_icon, (google_lens_x, footer_y))
    except Exception as e:
        # If images fail to load, continue without them
        print(f"Warning: Could not load footer images: {e}")
    
    # Footer section - Second row: Nepali text
    emergency_text = "यदि यो सवारी साधन कुनै आपत्कालीन अवस्थामा छ भने माथिको QR स्क्यान गरी सम्बन्धित व्यक्तिलाई खबर गरिदिनुहोला।"
    
    # Wrap text if needed
    words = emergency_text.split()
    lines = []
    current_line = []
    current_width = 0
    
    for word in words:
        bbox = draw.textbbox((0, 0), word + " ", font=small_font)
        word_width = bbox[2] - bbox[0]
        if current_width + word_width > width - 40:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_width = word_width
            else:
                lines.append(word)
                current_width = 0
        else:
            current_line.append(word)
            current_width += word_width
    
    if current_line:
        lines.append(" ".join(current_line))
    
    # Draw emergency message in dark green (with larger spacing for bigger font)
    emergency_y = footer_y + icon_size + 30
    line_spacing = 25  # Increased spacing for larger font
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=small_font)
        text_width = bbox[2] - bbox[0]
        text_x = (width - text_width) // 2
        draw.text((text_x, emergency_y + i * line_spacing), line, fill=dark_green, font=small_font)
    
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

