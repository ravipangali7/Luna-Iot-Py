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
    
    # Add green "G" logo in the center of QR code (GPS icon style - location pin)
    # Create a location pin style logo with "G"
    logo_size = 50
    logo_img = Image.new('RGBA', (logo_size, logo_size), (0, 0, 0, 0))
    logo_draw = ImageDraw.Draw(logo_img)
    
    # Dark green color for logo (matching the body background)
    dark_green = (34, 139, 34)
    
    # Draw location pin shape (teardrop/pin shape)
    # Top circle
    logo_draw.ellipse([(logo_size//2 - 15, 5), (logo_size//2 + 15, 35)], fill=dark_green)
    # Bottom triangle/point
    logo_draw.polygon([
        (logo_size//2, 35),
        (logo_size//2 - 12, 45),
        (logo_size//2 + 12, 45)
    ], fill=dark_green)
    
    # Draw white "G" letter in the center
    try:
        logo_font = ImageFont.truetype("arial.ttf", 28)
    except:
        try:
            logo_font = ImageFont.truetype("arial.ttf", 24)
        except:
            logo_font = ImageFont.load_default()
    
    # Draw "G" text in white, centered
    g_bbox = logo_draw.textbbox((0, 0), "G", font=logo_font)
    g_width = g_bbox[2] - g_bbox[0]
    g_height = g_bbox[3] - g_bbox[1]
    g_x = (logo_size - g_width) // 2
    g_y = (logo_size - g_height) // 2 - 5  # Slightly above center
    logo_draw.text((g_x, g_y), "G", fill=(255, 255, 255), font=logo_font)
    
    # Paste logo in center of QR code
    qr_center_x = qr_img.width // 2 - logo_size // 2
    qr_center_y = qr_img.height // 2 - logo_size // 2
    qr_img.paste(logo_img, (qr_center_x, qr_center_y), logo_img)
    
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
    
    # Try to load a font, fallback to default if not available
    try:
        # Try to use a system font
        title_font = ImageFont.truetype("arial.ttf", 32)
        subtitle_font = ImageFont.truetype("arial.ttf", 20)
        text_font = ImageFont.truetype("arial.ttf", 16)
        small_font = ImageFont.truetype("arial.ttf", 14)
    except:
        # Fallback to default font
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Body section - Title at top
    body_y = 30
    title_text = "Contact Vehicle Owner"
    subtitle_text = "सवारीधनी लाई सम्पर्क गर्नुहोस् ।"
    
    # Calculate text positions (centered)
    bbox = draw.textbbox((0, 0), title_text, font=title_font)
    text_width = bbox[2] - bbox[0]
    text_x = (width - text_width) // 2
    draw.text((text_x, body_y), title_text, fill=white, font=title_font)
    
    bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
    text_width = bbox[2] - bbox[0]
    text_x = (width - text_width) // 2
    draw.text((text_x, body_y + 45), subtitle_text, fill=white, font=subtitle_font)
    
    # Place QR code in center of body
    qr_x = (width - qr_img.width) // 2
    qr_y = body_y + 100
    img.paste(qr_img, (qr_x, qr_y))
    
    # Tag ID below QR code
    tag_id_text = f"TAG ID: {vtid}"
    bbox = draw.textbbox((0, 0), tag_id_text, font=text_font)
    text_width = bbox[2] - bbox[0]
    text_x = (width - text_width) // 2
    draw.text((text_x, qr_y + qr_img.height + 20), tag_id_text, fill=white, font=text_font)
    
    # Download app text
    app_text = "Download Luna IOT App Now"
    bbox = draw.textbbox((0, 0), app_text, font=text_font)
    text_width = bbox[2] - bbox[0]
    text_x = (width - text_width) // 2
    draw.text((text_x, qr_y + qr_img.height + 50), app_text, fill=white, font=text_font)
    
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
    
    # Draw emergency message in dark green
    emergency_y = footer_y + icon_size + 20
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=small_font)
        text_width = bbox[2] - bbox[0]
        text_x = (width - text_width) // 2
        draw.text((text_x, emergency_y + i * 20), line, fill=dark_green, font=small_font)
    
    # Convert to bytes
    img_io = io.BytesIO()
    img.save(img_io, format='PNG')
    img_io.seek(0)
    
    return img_io

