from django.template.loader import get_template
import os
from django.conf import settings
from .models import Bill, BillItem
from PyPDF2 import PdfMerger
import pdfkit
from datetime import datetime

def convert_html_to_pdf(html_content, pdf_path):
    try:
        pdfkit.from_string(html_content, pdf_path)
        print(f"PDF generated and saved at {pdf_path}")
    except Exception as e:
        print(f"PDF generation failed: {e}")

def generate_pdf(bill):
    items = BillItem.objects.filter(bill=bill)
    itemsList = []
    for item in items:
        itemsList.append(item)
    for i in range(len(items),(20-len(items))*5):
        itemsList.append('0')
    template_path = 'bill.html'
    context = {
        'bill': bill,
        'items': itemsList
    }
    template = get_template(template_path)
    html = template.render(context)


    filename = f"bill_{bill.bill_number}.pdf"
    pdf_path = os.path.join(settings.MEDIA_ROOT+'/Bills', filename)
    convert_html_to_pdf(html, pdf_path)

    return pdf_path

def generate_and_merge_pdfs(bills, filename):
    merger = PdfMerger()

    today = datetime.now().strftime("%Y-%m-%d")
    merged_filename = f"{filename}"
    output_dir = os.path.join(settings.MEDIA_ROOT, "Archives")

    os.makedirs(output_dir, exist_ok=True)  # Make sure the directory exists
    merged_path = os.path.join(output_dir, merged_filename)
    def get_value(obj, key):
        if isinstance(obj, dict):
            return obj.get(key)
        return getattr(obj, key, None)

    for bill in bills:
        bill_pdf_filename = f"bill_{get_value(bill, 'bill_number')}.pdf"
        bill_pdf_path = os.path.join(settings.MEDIA_ROOT, "Bills", bill_pdf_filename)

        # ✅ Check if PDF already exists
        if not os.path.exists(bill_pdf_path):
            bill_pdf_path = generate_pdf(bill)  # Generate and return full path

        # ✅ Append existing or newly generated PDF
        try:
            merger.append(bill_pdf_path)
        except Exception as e:
            print(f"Error merging Bill {get_value(bill, 'bill_number')}: {e}")

    merger.write(merged_path)
    merger.close()

    return merged_path


def clear_media_subfolder(subfolder_name):
    folder_path = os.path.join(settings.MEDIA_ROOT, subfolder_name)

    if not os.path.exists(folder_path):
        print(f"Directory {folder_path} does not exist.")
        return

    deleted = 0
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                deleted += 1
        except Exception as e:
            print(f"Failed to delete {file_path}: {e}")
