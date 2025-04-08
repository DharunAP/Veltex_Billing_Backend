from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Bill

@receiver(post_delete, sender=Bill)
def renumber_bills(sender, instance, **kwargs):
    # Get bills with bill_number greater than the deleted one
    bills_to_update = Bill.objects.filter(bill_number__gt=instance.bill_number).order_by('bill_number')
    
    for bill in bills_to_update:
        bill.bill_number -= 1
        bill.save()
