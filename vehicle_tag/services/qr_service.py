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
    
    # Light green color for logo (matching the body background)
    light_green = (144, 238, 144)
    
    # Draw location pin shape (teardrop/pin shape)
    # Top circle
    logo_draw.ellipse([(logo_size//2 - 15, 5), (logo_size//2 + 15, 35)], fill=light_green)
    # Bottom triangle/point
    logo_draw.polygon([
        (logo_size//2, 35),
        (logo_size//2 - 12, 45),
        (logo_size//2 + 12, 45)
    ], fill=light_green)
    
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
    
    # Add white border around QR code
    bordered_qr = Image.new('RGB', (qr_img.width + 20, qr_img.height + 20), 'white')
    bordered_qr.paste(qr_img, (10, 10))
    qr_img = bordered_qr
    
    # Create main image (matching the design from the image description)
    # Dimensions: approximately 600x800 pixels (portrait orientation)
    width = 600
    height = 900
    
    # Create image with white background
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Colors (matching the design)
    dark_green = (34, 139, 34)  # Dark green for header
    light_green = (144, 238, 144)  # Light green for body
    white = (255, 255, 255)
    black = (0, 0, 0)
    
    # Header section (dark green)
    header_height = 120
    draw.rectangle([(0, 0), (width, header_height)], fill=dark_green)
    
    # Main body section (light green)
    body_start = header_height
    body_height = 600
    draw.rectangle([(0, body_start), (width, body_start + body_height)], fill=light_green)
    
    # Footer section (white)
    footer_start = body_start + body_height
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
    
    # Header text
    header_text = "Contact Vehicle Owner"
    header_nepali = "सवारीधनी लाई सम्पर्क गर्नुहोस्।"
    
    # Calculate text positions (centered)
    bbox = draw.textbbox((0, 0), header_text, font=title_font)
    text_width = bbox[2] - bbox[0]
    text_x = (width - text_width) // 2
    draw.text((text_x, 20), header_text, fill=white, font=title_font)
    
    bbox = draw.textbbox((0, 0), header_nepali, font=subtitle_font)
    text_width = bbox[2] - bbox[0]
    text_x = (width - text_width) // 2
    draw.text((text_x, 65), header_nepali, fill=white, font=subtitle_font)
    
    # Body section text
    body_y = body_start + 20
    draw.text((width // 2 - 100, body_y), "Scan with QR Scanner", fill=white, font=text_font)
    
    # Place QR code in center of body (accounting for border)
    qr_x = (width - qr_img.width) // 2
    qr_y = body_y + 40
    img.paste(qr_img, (qr_x, qr_y))
    
    # Tag ID below QR code (adjust for bordered QR code)
    tag_id_text = f"TAG ID: {vtid}"
    bbox = draw.textbbox((0, 0), tag_id_text, font=text_font)
    text_width = bbox[2] - bbox[0]
    text_x = (width - text_width) // 2
    draw.text((text_x, qr_y + qr_img.height + 20), tag_id_text, fill=white, font=text_font)
    
    # SMS instructions
    sms_text = f'SEND SMS: "LUNATAG {vtid}" TO 31064'
    bbox = draw.textbbox((0, 0), sms_text, font=small_font)
    text_width = bbox[2] - bbox[0]
    text_x = (width - text_width) // 2
    draw.text((text_x, qr_y + qr_img.height + 60), sms_text, fill=white, font=small_font)
    
    # Download app text
    app_text = "Download Luna GPS App Now"
    bbox = draw.textbbox((0, 0), app_text, font=text_font)
    text_width = bbox[2] - bbox[0]
    text_x = (width - text_width) // 2
    draw.text((text_x, qr_y + qr_img.height + 100), app_text, fill=white, font=text_font)
    
    # Footer separator line
    line_y = footer_start
    draw.rectangle([(0, line_y), (width, line_y + 5)], fill=light_green)
    
    # Footer branding
    footer_text = "LUNA GPS"
    bbox = draw.textbbox((0, 0), footer_text, font=text_font)
    text_width = bbox[2] - bbox[0]
    text_x = (width - text_width) // 2
    draw.text((text_x, line_y + 20), footer_text, fill=dark_green, font=text_font)
    
    # Emergency message in Nepali
    emergency_text = "यदि यो सवारी साधन कुनै आपतकालीन अवस्थामा छ भने माथिको QR स्क्यन गरि सम्बन्धित ब्यक्ति लाई खबर गरिदिनु होला"
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
    
    # Draw emergency message
    emergency_y = line_y + 60
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=small_font)
        text_width = bbox[2] - bbox[0]
        text_x = (width - text_width) // 2
        draw.text((text_x, emergency_y + i * 20), line, fill=black, font=small_font)
    
    # Convert to bytes
    img_io = io.BytesIO()
    img.save(img_io, format='PNG')
    img_io.seek(0)
    
    return img_io

