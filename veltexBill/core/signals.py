from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Bill
from .utils import clear_media_subfolder, generate_pdf
@receiver(post_delete, sender=Bill)
def renumber_bills(sender, instance, **kwargs):
    # Get bills with bill_number greater than the deleted one
    bills_to_update = Bill.objects.all().order_by('bill_number')
    clear_media_subfolder('Bills')
    for index,bill in enumerate(bills_to_update):
        bill.bill_number = index+1
        bill.save()
        generate_pdf(bill)
