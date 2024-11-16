from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# Masukkan API token bot Anda
BOT_TOKEN = '7819726080:AAHppyz8wYYHApbFzUDlbODiIB8heDCy6JE'

# Path ke file font yang sudah diunduh (ganti dengan path yang sesuai)
FONT_PATH = '1.ttf'

# Fungsi untuk membuat gambar kertas folio besar
def create_folio_image():
    img = Image.new('RGB', (850, 1200), 'white')
    draw = ImageDraw.Draw(img)
    margin_left = 50
    line_height = 30
    blue_line_color = (173, 216, 230)
    
    # Menarik garis biru di sebelah kiri
    draw.line([(margin_left, 0), (margin_left, img.height)], fill=blue_line_color, width=5)
    
    # Menarik garis-garis horizontal untuk efek kertas folio besar
    for y in range(100, img.height - 20, line_height):
        draw.line([(0, y), (img.width, y)], fill='lightgrey', width=1)
        
    return img

# Fungsi untuk menulis teks pada kolom dan memastikan teks penuh di kanan kolom sebelum turun
def write_on_folio(teks, folio_image, nama, tanggal):
    try:
        images = []
        img = folio_image.copy()
        draw = ImageDraw.Draw(img)
        
        # Tentukan font
        try:
            font = ImageFont.truetype(FONT_PATH, 24)
            bold_font = ImageFont.truetype(FONT_PATH, 28)  # Font lebih tebal untuk Nama dan Tanggal
        except IOError:
            font = ImageFont.load_default()
            bold_font = font  # Default font jika font khusus gagal

        # Menambahkan Nama di kiri dan Tanggal di kiri bagian atas gambar
        draw.text((70, 20), f"Nama: {nama}", font=bold_font, fill='black')
        draw.text((img.width - 300, 20), f"Tanggal: {tanggal}", font=bold_font, fill='black')


        # Pengaturan kolom yang diperbarui untuk kertas folio besar
        margin_left = 70
        margin_right = 20
        column_width = img.width - margin_left - margin_right
        columns = [
            (margin_left, 100, margin_left + column_width, img.height - 80),
            (margin_left, img.height - 70, margin_left + column_width, img.height - 30)
        ]
        
        line_spacing = 30
        current_column = 0
        text_y = columns[current_column][1]

        # Split teks menjadi baris
        words = teks.split()
        current_line = ""
        
        for word in words:
            left, top, right, bottom = columns[current_column]
            test_line = current_line + word + " "
            bbox = draw.textbbox((0, 0), test_line, font=font)
            text_width = bbox[2] - bbox[0]
            
            if text_width + left > right:
                draw.text((left, text_y), current_line.strip(), font=font, fill='black')
                text_y += line_spacing
                current_line = word + " "
                
                if text_y + line_spacing > bottom:
                    if current_column < len(columns) - 1:
                        current_column += 1
                        left, top, right, bottom = columns[current_column]
                        text_y = top
                    else:
                        images.append(img)
                        img = folio_image.copy()
                        draw = ImageDraw.Draw(img)
                        current_column = 0
                        left, top, right, bottom = columns[current_column]
                        text_y = top
            else:
                current_line = test_line

        draw.text((left, text_y), current_line.strip(), font=font, fill='black')
        images.append(img)

        output_images = []
        for image in images:
            bio = BytesIO()
            image.save(bio, 'PNG')
            bio.seek(0)
            output_images.append(bio)

        return output_images

    except Exception as e:
        print(f"Error dalam penulisan gambar: {e}")
        return None

# Fungsi untuk menangani perintah /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['state'] = 'get_name'
    await update.message.reply_text("Masukkan nama Anda:")

# Fungsi untuk menangani input pengguna berdasarkan langkah yang diinginkan
async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    user_input = update.message.text
    
    if user_data.get('state') == 'get_name':
        user_data['nama'] = user_input
        user_data['state'] = 'get_date'
        await update.message.reply_text("Masukkan tanggal (misalnya: 07/09/2024):")

    elif user_data.get('state') == 'get_date':
        user_data['tanggal'] = user_input
        user_data['state'] = 'get_text'
        await update.message.reply_text("Masukkan text yang ingin anda tulis:")

    elif user_data.get('state') == 'get_text':
        user_data['text'] = user_input
        process_message = await update.message.reply_text("Di Proses ⌛ ...")
        
        try:
            folio_image = user_data.get('folio_image', create_folio_image())
            images = write_on_folio(user_data['text'], folio_image, user_data['nama'], user_data['tanggal'])
            
            await update.message.reply_text("Proses Berhasil ✅gambar sedang dikirimkan!")
            await process_message.delete()
            
            for image in images:
                await update.message.reply_photo(photo=image)
                
        except Exception as e:
            await process_message.delete()
            await update.message.reply_text(f"Terjadi kesalahan: {str(e)}")
        
        # Reset user_data setelah selesai
        user_data.clear()

# Fungsi utama untuk menjalankan bot
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Menambahkan handler untuk perintah dan pesan teks
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input))

    # Jalankan bot
    application.run_polling()

if __name__ == '__main__':
    main()
