from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer,LoginSerializer,GroupSerializer,ExpenseSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from .models import Group,Expense,ExpenseSplit, Settlement, User
import decimal
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class RegisterView(APIView):
    def post(self,request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message':'User created successfully!'},status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self,request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            refresh = RefreshToken.for_user(user)
            return Response({
                'access':str(refresh.access_token),
                'refresh':str(refresh),
            })
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        
class GroupView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request):
        groups = Group.objects.filter(members = request.user)
        serializer = GroupSerializer(groups,many=True)
        return Response(serializer.data)
    
    def post(self,request):
        serializer = GroupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        
class ExpenseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ExpenseSerializer(data=request.data)
        if serializer.is_valid():
            expense = serializer.save(paid_by=request.user)
            
            # Auto create splits
            group = expense.group
            members = group.members.exclude(id=request.user.id)
            split_amount = decimal.Decimal(expense.amount) / (members.count() + 1)
            
            for member in members:
                ExpenseSplit.objects.create(
                    expense=expense,
                    user=member,
                    amount_owed=split_amount
                )
            # Broadcast to websocket layer
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'group_{expense.group_id}',
                {
                    'type':'expense_update',
                    'data':{
                        'action':'new_expense',
                        'expense_id':expense.id,
                        'amount':str(expense.amount),
                        'category':expense.category,
                        'paid_by':expense.paid_by.name
                    }
                }
            )
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class GroupBalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, group_id):
        splits = ExpenseSplit.objects.filter(
            expense__group_id=group_id,
            is_settled=False
        ).select_related('expense', 'user')

        balances = {}
        for split in splits:
            payer = split.expense.paid_by
            owes = split.user
            amount = split.amount_owed

            balances[payer.id] = balances.get(payer.id, {
                'name': payer.name, 'amount': decimal.Decimal(0)
            })
            balances[payer.id]['amount'] += amount

            balances[owes.id] = balances.get(owes.id, {
                'name': owes.name, 'amount': decimal.Decimal(0)
            })
            balances[owes.id]['amount'] -= amount

        return Response(balances)

class AddMemberView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, group_id):
        group = Group.objects.get(id=group_id)
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
            group.members.add(user)
            return Response({'message': 'Member added'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class GroupExpenseView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self,request,group_id):
        expenses = Expense.objects.filter(
            group_id = group_id
        ).select_related('paid_by')
        serializer = ExpenseSerializer(expenses,many=True)
        return Response(serializer.data)

class SettleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, group_id):
        paid_to_id = request.data.get('paid_to')
        amount = request.data.get('amount')

        try:
            paid_to = User.objects.get(id=paid_to_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        Settlement.objects.create(
            group_id=group_id,
            paid_by=request.user,
            paid_to=paid_to,
            amount=amount
        )

        ExpenseSplit.objects.filter(
            expense__group_id=group_id,
            user__in=[request.user, paid_to],
            is_settled=False
        ).update(is_settled=True)

        return Response({'message': 'Settlement recorded'})
        
    