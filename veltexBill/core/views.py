from rest_framework import generics
from .models import Buyer, Product, Bill, BillItem
from .serializers import BuyerSerializer, ProductSerializer, BillSerializer, BillDetailSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.utils import timezone
from .utils import generate_pdf
from django.shortcuts import render,redirect

def rendertemp(request):
    bill = Bill.objects.get(bill_number=20)
    items = list(BillItem.objects.filter(bill_id=bill.id))
    itemsList = []
    for item in items:
        itemsList.append(item)
    for i in range(len(items),(20-len(items))*5):
        itemsList.append('0')
    print(itemsList)
    return render(request,'bill.html',{'bill':bill,'items':itemsList})

# BUYER VIEWS
class BuyerListCreateView(generics.ListCreateAPIView):
    queryset = Buyer.objects.all()
    serializer_class = BuyerSerializer

# PRODUCT VIEWS
class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

# BILL CREATE
class BillCreateView(APIView):
    def post(self, request):
        serializer = BillDetailSerializer(data=request.data)
        if serializer.is_valid():
            bill = serializer.save(date=timezone.now())
            pdf_file = generate_pdf(bill)
            # upload_to_drive(pdf_file, f"Bill_{bill.bill_number}.pdf")
            return Response(BillDetailSerializer(bill).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# BILL RETRIEVE + UPDATE
class BillRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Bill.objects.all()
    serializer_class = BillDetailSerializer

    def perform_update(self, serializer):
        bill = serializer.save()
        pdf_file = generate_pdf(bill)

# LIST ALL BILLS
class BillListView(generics.ListAPIView):
    queryset = Bill.objects.all().order_by('-bill_number')
    serializer_class = BillSerializer

# RESET BILLS (Archive + Delete All Bills)
class ResetBillsView(APIView):
    def post(self, request):
        bills = Bill.objects.all().order_by('bill_number')
        bills.delete()
        return Response({"message": "Bills archived and deleted. Ready to restart billing."}, status=200)

# EXPORT BILL RANGE
class ExportBillsView(APIView):
    def post(self, request):
        start = int(request.query_params.get("start", 1))
        end = int(request.query_params.get("end", 999999))
        bills = Bill.objects.filter(bill_number__gte=start, bill_number__lte=end).order_by('bill_number')
        if not bills.exists():
            return Response({"error": "No bills in given range."}, status=404)
        return Response({"message": f"Bills {start}-{end} exported."}, status=200)

# ARCHIVED FILES (for listing stored files)
class ArchiveListView(APIView):
    def get(self, request):
        # This can later be hooked into Google Drive listing
        return Response({"archives": ["archive_2025-04-07.pdf"]})
