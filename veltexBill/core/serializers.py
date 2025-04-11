import decimal
from rest_framework import serializers
from .models import Buyer, Bill, BillItem
from num2words import num2words
from .utils import clear_media_subfolder, generate_pdf
# BUYER
class BuyerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Buyer
        fields = '__all__'
        extra_kwargs = {
            'gstin': {'validators': []},
        }

# BILL ITEM (used inside a bill)
class BillItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillItem
        fields = ['particulars', 'hsn_code', 'quantity', 'rate']



# BASIC BILL VIEW
class BillSerializer(serializers.ModelSerializer):
    buyer = BuyerSerializer()
    items = BillItemSerializer(many=True)

    class Meta:
        model = Bill
        fields = ['id','bill_number','date','total_amount','items','buyer']

# BILL CREATION / UPDATE
class BillDetailSerializer(serializers.ModelSerializer):
    items = BillItemSerializer(many=True)
    buyer = BuyerSerializer()

    class Meta:
        model = Bill
        fields = ['id', 'bill_number', 'date', 'buyer', 'items']
        read_only_fields = ['bill_number', 'date']

    def create(self, validated_data):
        buyer_data = validated_data.pop('buyer')
        items_data = validated_data.pop('items')
        # Auto-generate bill number
        last_bill = Bill.objects.order_by('-bill_number').first()
        next_bill_number = 1 if not last_bill else last_bill.bill_number + 1

        try:
            buyer = Buyer.objects.get(gstin=buyer_data['gstin'])
            # Update if needed
            buyer.name = buyer_data['name']
            buyer.address = buyer_data['address']
            buyer.phone = buyer_data['phone']
            buyer.state_code = buyer_data['state_code']
            buyer.save()
        except Buyer.DoesNotExist:
            buyer = Buyer.objects.create(**buyer_data)

        
        bill = Bill.objects.create(
            bill_number=next_bill_number,
            buyer=buyer,
            **validated_data
        )
        amount,quant = 0,0
        for item in items_data:
            billItem = BillItem.objects.create(
                bill=bill,
                particulars = item['particulars'],
                hsn_code = item['hsn_code'],
                quantity=item['quantity'],
                rate=item['rate'],
                amount=item['quantity']*item['rate'],
            )
            amount += billItem.amount
            quant += billItem.quantity
        bill.subtotal = amount
        bill.total_sarees = quant
        if(bill.buyer.state_code=="33"):
            bill.gst_sgst = bill.gst_cgst = round(bill.subtotal*decimal.Decimal(0.025),2)
            bill.total_amount = round(bill.subtotal + bill.gst_sgst + bill.gst_cgst )
        else:
            bill.gst_igst = round(bill.subtotal*decimal.Decimal(0.05),2)
            bill.total_amount = round(bill.subtotal + bill.gst_igst)
        words = num2words(int(bill.total_amount), lang='en_IN').title()
        bill.amount_in_words = f'{words} Rupees only.'
        bill.save()
        return bill

    def update(self, instance, validated_data):
        buyer_data = validated_data.pop('buyer', None)
        items_data = validated_data.pop('items', None)

        # Update buyer
        if buyer_data:
            buyer = instance.buyer
            for attr, value in buyer_data.items():
                setattr(buyer, attr, value)
            buyer.save()

        # Update bill fields (excluding buyer and items)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Remove old items and add new ones
        if items_data is not None:
            instance.items.all().delete()  # Assuming related_name='items' in BillItem FK

            amount = 0
            quant = 0

            for item in items_data:

                bill_item = BillItem.objects.create(
                    bill=instance,
                    particulars = item['particulars'],
                    hsn_code = item['hsn_code'],
                    quantity=item['quantity'],
                    rate=item['rate'],
                    amount=item['quantity'] * item['rate'],
                )
                amount += bill_item.amount
                quant += bill_item.quantity

            # GST calculations
            instance.subtotal = amount
            instance.total_sarees = quant

            if instance.buyer.state_code == "33":
                instance.gst_sgst = instance.gst_cgst = round(instance.subtotal * decimal.Decimal(0.025), 2)
                instance.total_amount = round(instance.subtotal + instance.gst_sgst + instance.gst_cgst)
            else:
                instance.gst_igst = round(instance.subtotal * decimal.Decimal(0.05), 2)
                instance.total_amount = round(instance.subtotal + instance.gst_igst)

            # Amount in words
            words = num2words(int(instance.total_amount), lang='en_IN').title()
            instance.amount_in_words = f'{words} Rupees only.'

            instance.save()

        return instance
    