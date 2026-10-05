# FusionSpace boot logos for small displays

Each header has the logo as C arrays, ready for a splash screen. Monochrome logos are white-on-black (lit pixels =
logo), drawn pixel-hinted so small sizes stay crisp. `PROGMEM` is defined away on non-AVR targets.

| Array suffix | Layout | Use with |
|---|---|---|
| `_gfx` | 1 bit/pixel, rows top to bottom, MSB = leftmost pixel, rows padded to whole bytes | Adafruit GFX `drawBitmap(x, y, bmp, w, h, WHITE)` |
| `_xbm` | 1 bit/pixel, rows, LSB = leftmost pixel (XBM) | U8g2 `drawXBM(x, y, w, h, bmp)`, also saved as `.xbm` |
| `_pages` | SSD1306 native: 8-pixel vertical bytes, page by page | Write straight to the SSD1306/SH1106 frame buffer |
| `_rgb565` | 16-bit RGB565, big-endian words, row-major, background Void | TFT_eSPI `pushImage(x, y, w, h, img)`, ST7789/ILI9341 |

| File | Size | Display |
|---|---|---|
| `oled-128x64.h` | 128 × 64 | monochrome OLED / e-paper |
| `oled-128x32.h` | 128 × 32 | monochrome OLED / e-paper |
| `oled-128x64-mark.h` | 128 × 64 | monochrome OLED / e-paper |
| `oled-72x40-mark.h` | 72 × 40 | monochrome OLED / e-paper |
| `epaper-296x128.h` | 296 × 128 | monochrome OLED / e-paper |
| `epaper-250x122.h` | 250 × 122 | monochrome OLED / e-paper |
| `tft-240x240.h` | 240 × 240 | color TFT (RGB565; LVGL v9 image in `tft-240x240-lvgl.c`) |
| `tft-320x240.h` | 320 × 240 | color TFT (RGB565; LVGL v9 image in `tft-320x240-lvgl.c`) |
| `tft-160x128.h` | 160 × 128 | color TFT (RGB565; LVGL v9 image in `tft-160x128-lvgl.c`) |
| `tft-135x240.h` | 135 × 240 | color TFT (RGB565; LVGL v9 image in `tft-135x240-lvgl.c`) |
| `tft-480x320.h` | 480 × 320 | color TFT (RGB565; LVGL v9 image in `tft-480x320-lvgl.c`) |
| `tft-240x240-round.h` | 240 × 240 | color TFT (RGB565, round GC9A01; LVGL v9 image in `tft-240x240-round-lvgl.c`) |
| `epaper-200x200.h` | 200 × 200 | monochrome OLED / e-paper |
| `epaper-400x300.h` | 400 × 300 | monochrome OLED / e-paper |

Previews: `*-preview@4x.png` (mono) and `*-preview@2x.png` (color). Regenerate with the build to change sizes
(`DISPLAYS` in `tools/build/kit_targets.py`). Color logos also come as LVGL v9 images (`*-lvgl.c`, `lv_image_dsc_t`, RGB565):
add the file to your project, then `LV_IMAGE_DECLARE(fs_logo_tft_240x240); lv_image_set_src(img, &fs_logo_tft_240x240);`.
The round 240 × 240 logo keeps the art inside the visible circle of a GC9A01 display.
