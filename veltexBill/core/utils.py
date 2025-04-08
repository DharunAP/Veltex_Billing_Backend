from django.template.loader import get_template
import os
from django.conf import settings


import pdfkit

def convert_html_to_pdf(html_content, pdf_path):
    try:
        pdfkit.from_string(html_content, pdf_path)
        print(f"PDF generated and saved at {pdf_path}")
    except Exception as e:
        print(f"PDF generation failed: {e}")

def generate_pdf(bill):
    from .models import BillItem
    items = BillItem.objects.filter(bill=bill)
    itemsList = []
    for item in items:
        itemsList.append(item)
    for i in range(len(items),(20-len(items))*5):
        itemsList.append('0')
    print(itemsList)
    template_path = 'bill.html'
    context = {
        'bill': bill,
        'items': itemsList
    }
    template = get_template(template_path)
    html = template.render(context)


    filename = f"bill_{bill.bill_number}.pdf"
    pdf_path = os.path.join(settings.MEDIA_ROOT, filename)
    convert_html_to_pdf(html, pdf_path)

    return pdf_path
