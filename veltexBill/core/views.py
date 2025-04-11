from rest_framework import generics
from .models import Buyer, Bill, BillItem
from .serializers import BuyerSerializer, BillSerializer, BillDetailSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.utils import timezone
from .utils import generate_pdf, generate_and_merge_pdfs, clear_media_subfolder
from django.shortcuts import render,redirect
from datetime import datetime

def rendertemp(request):
    bill = Bill.objects.get(bill_number=1)
    items = list(BillItem.objects.filter(bill_id=bill.id))
    itemsList = []
    for item in items:
        itemsList.append(item)
    for i in range(len(items),(20-len(items))*5):
        itemsList.append('0')
    return render(request,'bill.html',{'bill':bill,'items':itemsList})

# BUYER VIEWS
class BuyerListCreateView(generics.ListCreateAPIView):
    queryset = Buyer.objects.all()
    serializer_class = BuyerSerializer

class BuyerRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Buyer.objects.all()
    serializer_class = BuyerSerializer
    lookup_field = 'id'  # default, but you can set explicitly

# BILL CREATE tested
class BillCreateView(APIView):
    def post(self, request):
        serializer = BillDetailSerializer(data=request.data)
        if serializer.is_valid():
            bill = serializer.save(date=timezone.now())
            pdf_file = generate_pdf(bill)
            # upload_to_drive(pdf_file, f"Bill_{bill.bill_number}.pdf")
            return Response(BillDetailSerializer(bill).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# BILL RETRIEVE + UPDATE tested
class BillRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Bill.objects.all()
    serializer_class = BillDetailSerializer

    def perform_update(self, serializer):
        bill = serializer.save()
        generate_pdf(bill)  # Regenerate the PDF on update


# LIST ALL BILLS
class BillListView(generics.ListAPIView):
    queryset = Bill.objects.all().order_by('-bill_number')
    serializer_class = BillSerializer


# EXPORT BILL RANGE
class ExportBillsView(APIView):
    def post(self, request):
        file_name = request.query_params.get("file_name")
        print(request.data['bills'])
        bills = sorted(request.data.get('bills'), key=lambda x: x['bill_number'])
        path = generate_and_merge_pdfs(bills,file_name)
        return Response({"message": f"Bills {file_name} exported.",'path':path}, status=200)

# ARCHIVED FILES (for listing stored files)
class ArchiveListView(APIView):
    def get(self, request):
        # This can later be hooked into Google Drive listing
        bills = Bill.objects.all().order_by('bill_number')
        if not bills.exists():
            return Response({"error":"There are no bills left"},status=500)
        date = datetime.today().strftime('%d-%m-%Y')
        generate_and_merge_pdfs(bills,f"Archieve_{date}.pdf")
        clear_media_subfolder('Bills')
        bills.delete()
        return Response({"message":'Reset Done'})
