from PIL import ImageFont
import os

class FontManager:
    def __init__(self):
        self.fonts = {}
        self.load_fonts()
        
    def load_fonts(self):
        fonts_dir = os.path.join('resources', 'fonts')
        self.fonts['normal'] = {
            'regular': ImageFont.truetype(os.path.join(fonts_dir, 'SourceHanSansSC-VF.ttf'), 32),
            'bold': ImageFont.truetype(os.path.join(fonts_dir, 'SourceHanSansHWSC-Bold.otf'), 32)
        }
        self.fonts['handwritten'] = {
            'regular': ImageFont.truetype(os.path.join(fonts_dir, 'bailutongtongshouxieti.ttf'), 32)
        }
        
    def get_font(self, style, weight='regular'):
        return self.fonts.get(style, {}).get(weight, self.fonts['normal']['regular']) 