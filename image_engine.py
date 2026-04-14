from PIL import Image, ImageDraw, ImageFont
import os

# Create static directory if not exists
os.makedirs("static/banners", exist_ok=True)

class ImageEngine:
    def __init__(self):
        self.width = 1200
        self.height = 630
        self.bg_color = (18, 18, 18)  # Deep Dark
        self.accent_color = (255, 71, 71)  # Hot Red for "LOOT"
        
    def generate_banner(self, title, price, discount="70% OFF", filename="temp_banner.png"):
        # Create base image
        img = Image.new('RGB', (self.width, self.height), color=self.bg_color)
        draw = ImageDraw.Draw(img)
        
        # Load fonts (using fallback if specific fonts aren't available)
        try:
            title_font = ImageFont.truetype("arial.ttf", 60)
            price_font = ImageFont.truetype("arial.ttf", 80)
            badge_font = ImageFont.truetype("arial.ttf", 40)
        except:
            title_font = ImageFont.load_default()
            price_font = ImageFont.load_default()
            badge_font = ImageFont.load_default()

        # Draw "LOOT DEAL" Badge
        draw.rectangle([50, 50, 400, 130], fill=self.accent_color)
        draw.text((80, 65), "🔥 LOOT DEAL", fill="white", font=badge_font)

        # Draw Title (Wrap text if needed - simplified for now)
        draw.text((50, 200), title[:40] + "...", fill="white", font=title_font)

        # Draw Price
        draw.text((50, 350), f"Price: {price}", fill=(0, 255, 127), font=price_font)
        
        # Draw Discount Badge
        draw.ellipse([800, 200, 1100, 500], fill=self.accent_color)
        draw.text((840, 320), discount, fill="white", font=price_font)

        # Draw Footer Branding
        draw.text((50, 550), "Join our channel for more! 👉 @DealsMaster", fill=(150, 150, 150), font=badge_font)

        path = f"static/uploads/{filename}"
        img.save(path)
        return path

    def apply_watermark(self, image_path, logo_path="logo.png"):
        """Overlays the logo on the image in the top-right corner"""
        if not os.path.exists(logo_path) or not os.path.exists(image_path):
            return image_path
            
        try:
            # Open base image and convert to RGBA for blending
            base = Image.open(image_path).convert('RGBA')
            logo = Image.open(logo_path).convert('RGBA')
            
            # Calculate standard scaling (Logo = 12% of base image width - More Subtle)
            base_w, base_h = base.size
            logo_w, logo_h = logo.size
            
            new_logo_w = int(base_w * 0.12)
            # Maintain aspect ratio
            new_logo_h = int(logo_h * (new_logo_w / logo_w))
            
            logo = logo.resize((new_logo_w, new_logo_h), Image.Resampling.LANCZOS)
            
            # ✨ Improve Quality: Apply Semi-Transparency (60% Opacity)
            # This makes it look like a real watermark
            r, g, b, a = logo.split()
            a = a.point(lambda p: p * 0.6) # Reduce alpha to 60%
            logo = Image.merge('RGBA', (r, g, b, a))
            
            # Position: Top-Right with subtle padding
            padding = 25
            pos_x = base_w - new_logo_w - padding
            pos_y = padding
            
            # Paste logo onto base with its alpha mask
            base.paste(logo, (pos_x, pos_y), logo)
            
            # Convert back to RGB (standard for Telegram/Web) and save
            final = base.convert('RGB')
            final.save(image_path, quality=95)
            return image_path
        except Exception as e:
            print(f"⚠️ Watermark failed: {e}")
            return image_path

# Example test
if __name__ == "__main__":
    engine = ImageEngine()
    engine.generate_banner("Apple iPhone 15 Pro", "₹99,999", "25% OFF")
