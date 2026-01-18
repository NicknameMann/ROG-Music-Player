from PIL import Image, ImageDraw

def create_rog_icon():
    # Buat kanvas 256x256 (standar ikon Windows)
    size = (256, 256)
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Warna khas ROG
    rog_red = (255, 0, 0)
    dark_gray = (20, 20, 20)

    # Gambar background lingkaran hitam
    draw.ellipse([10, 10, 246, 246], fill=dark_gray)

    # Gambar pola segitiga/tajam khas ROG
    # Koordinat ini membentuk pola mata/slash sederhana
    points = [(60, 100), (100, 60), (200, 130), (100, 200), (60, 160)]
    draw.polygon(points, fill=rog_red)
    
    # Tambah garis aksen
    draw.line([(40, 40), (216, 216)], fill=rog_red, width=15)

    # Simpan sebagai file .ico
    image.save("icon_rog.ico", format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (32, 32)])
    print("Ikon 'icon_rog.ico' berhasil dibuat!")

if __name__ == "__main__":
    create_rog_icon()