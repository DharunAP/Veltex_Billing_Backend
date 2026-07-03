import decimal
from rest_framework import serializers
from .models import Buyer, Bill, BillItem
from num2words import num2words
from .utils import clear_media_subfolder, generate_pdf
from django.db.models import F
from django.db import transaction

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
        read_only_fields = ['bill_number']

    def create(self, validated_data):
        buyer_data = validated_data.pop("buyer")
        items_data = validated_data.pop("items")

        try:
            buyer = Buyer.objects.get(gstin=buyer_data["gstin"])
            buyer.name = buyer_data["name"]
            buyer.address = buyer_data["address"]
            buyer.phone = buyer_data["phone"]
            buyer.state_code = buyer_data["state_code"]
            buyer.save()
        except Buyer.DoesNotExist:
            buyer = Buyer.objects.create(**buyer_data)

        bill_date = validated_data["date"]

        # Find insertion point
        last_bill = (
            Bill.objects
            .filter(date__lte=bill_date)
            .order_by("-bill_number")
            .first()
        )

        with transaction.atomic():
            if last_bill:
                new_bill_number = last_bill.bill_number + 1

                # Shift only bills after the insertion point.
                # Process HIGHEST first so each bill vacates its slot
                # before the next one shifts into it (avoids unique
                # constraint collisions on bill_number).
                shifted = list(
                    Bill.objects.filter(
                        bill_number__gte=new_bill_number
                    ).order_by("-bill_number")
                )
                for b in shifted:
                    b.bill_number += 1
                    b.save(update_fields=["bill_number"])

            else:
                new_bill_number = 1

                # Shift every bill if inserting at the beginning.
                # Same highest-first ordering as above.
                shifted = list(
                    Bill.objects.all().order_by("-bill_number")
                )
                for b in shifted:
                    b.bill_number += 1
                    b.save(update_fields=["bill_number"])

        bill = Bill.objects.create(
            bill_number=new_bill_number,
            buyer=buyer,
            **validated_data
        )

        amount = 0
        quant = 0

        for item in items_data:

            bill_item = BillItem.objects.create(
                bill=bill,
                particulars=item["particulars"],
                hsn_code=item["hsn_code"],
                quantity=item["quantity"],
                rate=round(item["rate"]),
                amount=round(item["quantity"] * item["rate"])
            )

            amount += bill_item.amount
            quant += bill_item.quantity

        bill.subtotal = amount
        bill.total_sarees = quant

        if bill.buyer.state_code == "33":
            bill.gst_sgst = bill.gst_cgst = round(
                bill.subtotal * decimal.Decimal("0.025"), 2
            )
            bill.gst_igst = None
            bill.total_amount = round(
                bill.subtotal +
                bill.gst_sgst +
                bill.gst_cgst
            )
        else:
            bill.gst_igst = round(
                bill.subtotal * decimal.Decimal("0.05"), 2
            )
            bill.gst_sgst = None
            bill.gst_cgst = None
            bill.total_amount = round(
                bill.subtotal +
                bill.gst_igst
            )

        words = num2words(int(bill.total_amount), lang="en_IN").title()
        bill.amount_in_words = f"{words} Rupees only."

        bill.save()

        return bill

    def update(self, instance, validated_data):
        buyer_data = validated_data.pop('buyer', None)
        items_data = validated_data.pop('items', None)

        if buyer_data:
            buyer = instance.buyer
            for attr, value in buyer_data.items():
                setattr(buyer, attr, value)
            buyer.save()

        old_bill_number = instance.bill_number
        old_date = instance.date
        new_date = validated_data.get("date", old_date)

        if new_date != old_date:

            last_bill = (
                Bill.objects
                .filter(date__lte=new_date)
                .exclude(pk=instance.pk)
                .order_by("-bill_number")
                .first()
            )

            new_bill_number = 1 if last_bill is None else last_bill.bill_number + 1

            if new_bill_number != old_bill_number:

                with transaction.atomic():

                    # Park this bill on a slot that cannot collide with
                    # any real bill_number (max + 1000, computed fresh
                    # inside the transaction), so the shifts below never
                    # race with the instance's own row.
                    max_bill_number = (
                        Bill.objects.order_by("-bill_number")
                        .values_list("bill_number", flat=True)
                        .first()
                    ) or 0
                    parking_number = max_bill_number + 1000

                    Bill.objects.filter(pk=instance.pk).update(
                        bill_number=parking_number
                    )

                    # Moving Earlier
                    if new_bill_number < old_bill_number:

                        # Shift (new, old) up by 1. Process HIGHEST
                        # first so each bill vacates its slot before
                        # the next one moves into it.
                        shifted = list(
                            Bill.objects.filter(
                                bill_number__gte=new_bill_number,
                                bill_number__lt=old_bill_number
                            ).order_by("-bill_number")
                        )
                        for b in shifted:
                            b.bill_number += 1
                            b.save(update_fields=["bill_number"])

                        instance.bill_number = new_bill_number

                    # Moving Later
                    elif new_bill_number > old_bill_number:

                        # Shift (old, new) down by 1. Process LOWEST
                        # first so each bill vacates its slot before
                        # the next one moves into it.
                        shifted = list(
                            Bill.objects.filter(
                                bill_number__gt=old_bill_number,
                                bill_number__lt=new_bill_number
                            ).order_by("bill_number")
                        )
                        for b in shifted:
                            b.bill_number -= 1
                            b.save(update_fields=["bill_number"])

                        instance.bill_number = new_bill_number - 1

                    # Move instance from the parking slot to its final
                    # number now, inside the same transaction, so the
                    # DB is never left with the instance parked at a
                    # nonsensical bill_number.
                    Bill.objects.filter(pk=instance.pk).update(
                        bill_number=instance.bill_number
                    )

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if items_data is not None:

            instance.items.all().delete()

            amount = 0
            quant = 0

            for item in items_data:

                bill_item = BillItem.objects.create(
                    bill=instance,
                    particulars=item["particulars"],
                    hsn_code=item["hsn_code"],
                    quantity=item["quantity"],
                    rate=round(item["rate"]),
                    amount=round(item["quantity"] * item["rate"])
                )

                amount += bill_item.amount
                quant += bill_item.quantity

            instance.subtotal = amount
            instance.total_sarees = quant

            if instance.buyer.state_code == "33":
                instance.gst_sgst = instance.gst_cgst = round(
                    instance.subtotal * decimal.Decimal("0.025"), 2
                )
                instance.gst_igst = None
                instance.total_amount = round(
                    instance.subtotal +
                    instance.gst_sgst +
                    instance.gst_cgst
                )
            else:
                instance.gst_igst = round(
                    instance.subtotal * decimal.Decimal("0.05"), 2
                )
                instance.gst_sgst = None
                instance.gst_cgst = None
                instance.total_amount = round(
                    instance.subtotal +
                    instance.gst_igst
                )

            words = num2words(
                int(instance.total_amount),
                lang="en_IN"
            ).title()

            instance.amount_in_words = f"{words} Rupees only."

            instance.save()

        return instance