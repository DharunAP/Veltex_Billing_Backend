from django.db import models

class Buyer(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    gstin = models.CharField(max_length=15)
    state_code = models.CharField(max_length=5)
    phone = models.CharField(max_length=15)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100, unique=True)
    latest_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.name

class Bill(models.Model):
    bill_number = models.PositiveIntegerField(unique=True)
    date = models.DateField(auto_now_add=True)
    hsn_code = models.IntegerField(default=5208)
    buyer = models.ForeignKey(Buyer, on_delete=models.CASCADE)
    total_sarees = models.IntegerField(default=0)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gst_sgst = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    gst_cgst = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    gst_igst = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_in_words = models.CharField(max_length=255, default=0)
    is_same_state = models.BooleanField(default=True)

    def __str__(self):
        return f"Bill #{self.bill_number}"

class BillItem(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    particulars = models.CharField(max_length=255)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Item: {self.particulars} (Bill #{self.bill.bill_number})"
