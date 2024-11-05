from PIL import ImageFont
import os

class FontManager:
    def __init__(self):
        self.fonts = {}
        self.load_fonts()
        
    def load_fonts(self):
        fonts_dir = os.path.join('resources', 'fonts')
        self.fonts['normal'] = {
            'regular': ImageFont.truetype(os.path.join(fonts_dir, 'normal.ttf'), 32),
            'bold': ImageFont.truetype(os.path.join(fonts_dir, 'normal-bold.ttf'), 32)
        }
        self.fonts['handwritten'] = {
            'regular': ImageFont.truetype(os.path.join(fonts_dir, 'handwritten.ttf'), 32)
        }
        
    def get_font(self, style, weight='regular'):
        return self.fonts.get(style, {}).get(weight, self.fonts['normal']['regular']) 